import csv
import json
import logging
import os
import uuid
from collections import defaultdict
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Iterator

from app.core.database import Database
from app.core.errors import ApiError
from app.services.locations import LocationService
from app.services.providers import OpenMeteoClient


VARIABLE_UNITS = {
    "temperature_2m_mean": "°C",
    "temperature_2m_max": "°C",
    "temperature_2m_min": "°C",
    "temperature_2m": "°C",
    "precipitation_sum": "mm",
    "precipitation": "mm",
    "relative_humidity_2m_mean": "%",
    "relative_humidity_2m": "%",
    "wind_speed_10m_max": "km/h",
    "wind_speed_10m": "km/h",
    "wind_direction_10m_dominant": "°",
    "shortwave_radiation_sum": "MJ/m²",
    "surface_pressure": "hPa",
}


class HistoricalService:
    def __init__(
        self,
        database: Database,
        data_dir: Path,
        locations: LocationService,
        client: OpenMeteoClient,
    ):
        self.database = database
        self.data_dir = data_dir / "historical"
        self.locations = locations
        self.client = client

    def create_job(self, location_id: str, start_date: date, end_date: date) -> dict:
        job_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        with self.database.connection() as connection:
            connection.execute(
                "INSERT INTO ingestion_jobs(id, status, location_id, start_date, end_date, created_at) VALUES (?, 'queued', ?, ?, ?, ?)",
                (
                    job_id,
                    location_id,
                    start_date.isoformat(),
                    end_date.isoformat(),
                    now,
                ),
            )
        return self.get_job(job_id)

    def get_job(self, job_id: str) -> dict:
        with self.database.connection() as connection:
            row = connection.execute(
                "SELECT * FROM ingestion_jobs WHERE id = ?", (job_id,)
            ).fetchone()
        if row is None:
            raise ApiError(
                404, "job_not_found", "The requested ingestion job does not exist."
            )
        return dict(row)

    async def run_ingestion(self, job_id: str) -> None:
        job = self.get_job(job_id)
        now = datetime.now(UTC).isoformat()
        with self.database.connection() as connection:
            connection.execute(
                "UPDATE ingestion_jobs SET status = 'running', started_at = ? WHERE id = ?",
                (now, job_id),
            )
        try:
            location = self.locations.get(job["location_id"])
            payload = await self.client.archive(
                location["latitude"],
                location["longitude"],
                location["timezone"],
                job["start_date"],
                job["end_date"],
            )
            daily = payload.get("daily")
            if not isinstance(daily, dict) or not isinstance(daily.get("time"), list):
                raise ValueError("Historical provider response has no daily series")
            dataset_id = self._write_dataset(
                location, job, daily, payload.get("daily_units", {})
            )
            completed = datetime.now(UTC).isoformat()
            with self.database.connection() as connection:
                connection.execute(
                    "UPDATE ingestion_jobs SET status = 'completed', completed_at = ?, dataset_id = ? WHERE id = ?",
                    (completed, dataset_id, job_id),
                )
        except Exception:
            logging.getLogger(__name__).exception(
                "Historical ingestion failed", extra={"job_id": job_id}
            )
            with self.database.connection() as connection:
                connection.execute(
                    "UPDATE ingestion_jobs SET status = 'failed', completed_at = ?, error_message = ? WHERE id = ?",
                    (
                        datetime.now(UTC).isoformat(),
                        "Historical ingestion failed; inspect server logs.",
                        job_id,
                    ),
                )

    def _write_dataset(
        self, location: dict, job: dict, daily: dict, units: dict
    ) -> str:
        dataset_id = str(uuid.uuid4())
        self.data_dir.mkdir(parents=True, exist_ok=True)
        path = self.data_dir / f"{dataset_id}.csv"
        temporary_path = self.data_dir / f".{dataset_id}.tmp"
        times, variables = self._validate_daily_series(
            daily, job["start_date"], job["end_date"]
        )
        retrieved_at = datetime.now(UTC).isoformat()
        try:
            with temporary_path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=[
                        "date",
                        *variables,
                        "source",
                        "data_kind",
                        "location_id",
                        "retrieved_at",
                    ],
                )
                writer.writeheader()
                for index, timestamp in enumerate(times):
                    row = {
                        "date": timestamp,
                        "source": "Open-Meteo Historical Weather API",
                        "data_kind": "reanalysis",
                        "location_id": location["id"],
                        "retrieved_at": retrieved_at,
                    }
                    for variable in variables:
                        row[variable] = daily[variable][index]
                    writer.writerow(row)
            os.replace(temporary_path, path)
            metadata = {
                "location": location,
                "variables": variables,
                "units": {
                    name: units.get(name, VARIABLE_UNITS[name]) for name in variables
                },
                "provider": "Open-Meteo Historical Weather API",
                "source_kind": "ERA5 reanalysis",
                "processing": "Raw daily provider values stored without imputation or interpolation.",
            }
            with self.database.connection() as connection:
                connection.execute(
                    "INSERT INTO historical_datasets(id, location_id, source, data_kind, file_path, start_date, end_date, retrieved_at, row_count, metadata_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        dataset_id,
                        location["id"],
                        "Open-Meteo Historical Weather API",
                        "reanalysis",
                        str(path.resolve()),
                        job["start_date"],
                        job["end_date"],
                        retrieved_at,
                        len(times),
                        json.dumps(metadata),
                    ),
                )
        except Exception:
            temporary_path.unlink(missing_ok=True)
            path.unlink(missing_ok=True)
            raise
        return dataset_id

    @staticmethod
    def _validate_daily_series(
        daily: dict, start_date: str, end_date: str
    ) -> tuple[list[str], list[str]]:
        times = daily.get("time")
        if not isinstance(times, list) or not times:
            raise ValueError("Historical provider response has no daily timestamps")
        parsed_times = []
        for timestamp in times:
            if not isinstance(timestamp, str):
                raise ValueError(
                    "Historical provider response contains an invalid timestamp"
                )
            parsed_times.append(date.fromisoformat(timestamp))
        if len(set(parsed_times)) != len(parsed_times):
            raise ValueError(
                "Historical provider response contains duplicate timestamps"
            )
        if parsed_times != sorted(parsed_times):
            raise ValueError(
                "Historical provider response timestamps are not chronological"
            )
        if parsed_times[0] < date.fromisoformat(start_date) or parsed_times[
            -1
        ] > date.fromisoformat(end_date):
            raise ValueError(
                "Historical provider response exceeds the requested date range"
            )
        variables = [key for key in VARIABLE_UNITS if isinstance(daily.get(key), list)]
        if not variables:
            raise ValueError("Historical provider response has no supported variables")
        for variable in variables:
            values = daily[variable]
            if len(values) != len(times) or any(
                value is not None
                and (not isinstance(value, (int, float)) or isinstance(value, bool))
                for value in values
            ):
                raise ValueError(
                    f"Historical provider response contains an invalid {variable} series"
                )
        return times, variables

    def list_datasets(self, location_id: str | None) -> list[dict]:
        with self.database.connection() as connection:
            query = "SELECT * FROM historical_datasets"
            params: tuple = ()
            if location_id:
                query += " WHERE location_id = ?"
                params = (location_id,)
            query += " ORDER BY retrieved_at DESC"
            rows = connection.execute(query, params).fetchall()
        return [self._dataset_record(row) for row in rows]

    def dataset(self, dataset_id: str) -> dict:
        with self.database.connection() as connection:
            row = connection.execute(
                "SELECT * FROM historical_datasets WHERE id = ?", (dataset_id,)
            ).fetchone()
        if row is None:
            raise ApiError(
                404,
                "dataset_not_found",
                "The requested historical dataset does not exist.",
            )
        return self._dataset_record(row)

    @staticmethod
    def _dataset_record(row) -> dict:
        result = dict(row)
        result["metadata"] = json.loads(result.pop("metadata_json"))
        result.pop("file_path", None)
        return result

    def read_rows(self, dataset_id: str) -> Iterator[dict]:
        with self.database.connection() as connection:
            row = connection.execute(
                "SELECT file_path FROM historical_datasets WHERE id = ?", (dataset_id,)
            ).fetchone()
        if row is None:
            raise ApiError(
                404,
                "dataset_not_found",
                "The requested historical dataset does not exist.",
            )
        path = Path(row["file_path"])
        # If path points to parquet but a companion CSV exists, prefer CSV for DictReader compatibility
        if path.suffix == ".parquet" and path.with_suffix(".csv").is_file():
            path = path.with_suffix(".csv")

        if not path.is_file() or path.parent.resolve() != self.data_dir.resolve():
            raise ApiError(
                409,
                "dataset_unavailable",
                "The historical dataset file is unavailable.",
            )

        if path.suffix == ".parquet":
            import pandas as pd
            df = pd.read_parquet(path)
            for r in df.to_dict(orient="records"):
                yield {k: str(v) if v is not None else "" for k, v in r.items()}
            return

        with path.open(newline="", encoding="utf-8") as file:
            yield from csv.DictReader(file)

    def summary(
        self,
        dataset_id: str,
        variable: str,
        period: str,
        baseline_dataset_id: str | None = None,
    ) -> dict:
        if variable not in VARIABLE_UNITS:
            raise ApiError(
                422, "unsupported_variable", "The requested variable is not supported."
            )
        groups: dict[str, list[float]] = defaultdict(list)
        for row in self.read_rows(dataset_id):
            value = self._number(row.get(variable))
            if value is None and variable in ("temperature_2m_mean", "temperature_2m"):
                value = self._number(row.get("temperature_2m") or row.get("temperature_2m_max"))
            elif value is None and variable in ("precipitation_sum", "precipitation"):
                value = self._number(row.get("precipitation") or row.get("precipitation_sum"))
            if value is None:
                continue
            date_str = str(row.get("date", ""))[:10]
            if not date_str:
                continue
            groups[self._period_key(date_str, period)].append(value)
        values: list[dict[str, Any]] = [
            {
                "period": key,
                "count": len(numbers),
                "mean": round(sum(numbers) / len(numbers), 3),
                "total": round(sum(numbers), 3)
                if variable == "precipitation_sum"
                else None,
                "min": round(min(numbers), 3),
                "max": round(max(numbers), 3),
            }
            for key, numbers in sorted(groups.items())
        ]
        result: dict[str, Any] = {
            "dataset_id": dataset_id,
            "variable": variable,
            "unit": VARIABLE_UNITS[variable],
            "period": period,
            "items": values,
            "source_note": "Derived from stored reanalysis data, not direct station observations.",
        }
        if baseline_dataset_id:
            baseline = self._mean(baseline_dataset_id, variable)
            if baseline is None:
                raise ApiError(
                    422,
                    "inadequate_baseline",
                    "The selected baseline has no compatible valid values.",
                )
            result["baseline"] = {
                "dataset_id": baseline_dataset_id,
                "mean": round(baseline, 3),
                "anomaly_method": "Each period mean minus the selected baseline-dataset mean.",
            }
            for item in values:
                item["anomaly"] = round(item["mean"] - baseline, 3)
        return result

    def monsoon(self, dataset_id: str, start_month: int, end_month: int) -> dict:
        rows = []
        for row in self.read_rows(dataset_id):
            rainfall = self._number(row.get("precipitation_sum"))
            if rainfall is None:
                rainfall = self._number(row.get("precipitation"))
            date_str = str(row.get("date", ""))[:10]
            if not date_str:
                continue
            month = date.fromisoformat(date_str).month
            within = (
                start_month <= month <= end_month
                if start_month <= end_month
                else month >= start_month or month <= end_month
            )
            if rainfall is not None and within:
                rows.append(rainfall)
        return {
            "dataset_id": dataset_id,
            "variable": "precipitation_sum",
            "unit": "mm",
            "period": {"start_month": start_month, "end_month": end_month},
            "days_with_data": len(rows),
            "rainfall_total": round(sum(rows), 3) if rows else None,
            "note": "No missing values are imputed.",
        }

    def heat_patterns(
        self, dataset_id: str, threshold_celsius: float = 40.0
    ) -> dict:
        self.dataset(dataset_id)
        daily_records: list[tuple[str, float]] = []
        for row in self.read_rows(dataset_id):
            val = self._number(row.get("temperature_2m_max"))
            if val is None:
                val = self._number(row.get("temperature_2m_mean"))
            if val is None:
                val = self._number(row.get("temperature_2m"))
            if val is not None:
                date_str = str(row.get("date", ""))[:10]
                daily_records.append((date_str, val))

        if not daily_records:
            raise ApiError(
                422,
                "insufficient_data",
                "Dataset contains no valid temperature series for heat pattern analysis.",
            )

        daily_records.sort(key=lambda x: x[0])
        temperatures = [temp for _, temp in daily_records]

        days_above_35 = sum(1 for t in temperatures if t >= 35.0)
        days_above_40 = sum(1 for t in temperatures if t >= 40.0)
        days_above_45 = sum(1 for t in temperatures if t >= 45.0)
        days_above_threshold = sum(1 for t in temperatures if t >= threshold_celsius)

        max_streak = 0
        current_streak = 0
        for _, temp in daily_records:
            if temp >= threshold_celsius:
                current_streak += 1
                if current_streak > max_streak:
                    max_streak = current_streak
            else:
                current_streak = 0

        max_entry = max(daily_records, key=lambda x: x[1])
        min_entry = min(daily_records, key=lambda x: x[1])

        monthly_hot: dict[str, int] = defaultdict(int)
        for d_str, temp in daily_records:
            if temp >= threshold_celsius:
                monthly_hot[d_str[:7]] += 1

        summer_temps = [
            temp
            for d_str, temp in daily_records
            if 3 <= date.fromisoformat(d_str[:10]).month <= 6
        ]

        return {
            "dataset_id": dataset_id,
            "threshold_celsius": threshold_celsius,
            "unit": "°C",
            "total_days_analyzed": len(daily_records),
            "days_above_35c": days_above_35,
            "days_above_40c": days_above_40,
            "days_above_45c": days_above_45,
            "days_above_threshold": days_above_threshold,
            "max_consecutive_hot_days": max_streak,
            "peak_temperature": {
                "temperature": round(max_entry[1], 2),
                "date": max_entry[0],
            },
            "lowest_daily_max": {
                "temperature": round(min_entry[1], 2),
                "date": min_entry[0],
            },
            "mean_temperature": round(sum(temperatures) / len(temperatures), 2),
            "summer_season_summary": {
                "months": "March-June (Pre-monsoon / Summer)",
                "days_with_data": len(summer_temps),
                "mean_temperature": round(sum(summer_temps) / len(summer_temps), 2)
                if summer_temps
                else None,
                "hot_days_count": sum(1 for t in summer_temps if t >= threshold_celsius),
            },
            "monthly_hot_days": dict(sorted(monthly_hot.items())),
            "source_note": "Derived from stored ERA5 reanalysis daily maximum temperatures; not direct meteorological station observations.",
        }

    def compare(
        self, left_dataset_id: str, right_dataset_id: str, variable: str
    ) -> dict:
        if left_dataset_id == right_dataset_id:
            raise ApiError(
                422, "invalid_comparison", "Comparison requires two distinct datasets."
            )
        if variable not in VARIABLE_UNITS:
            raise ApiError(
                422, "unsupported_variable", "The requested variable is not supported."
            )
        left = self.dataset(left_dataset_id)
        right = self.dataset(right_dataset_id)
        left_mean = self._mean(left_dataset_id, variable)
        right_mean = self._mean(right_dataset_id, variable)
        if left_mean is None or right_mean is None:
            raise ApiError(
                422,
                "insufficient_comparison_data",
                "Both datasets require valid values for the selected variable.",
            )
        return {
            "variable": variable,
            "unit": VARIABLE_UNITS[variable],
            "left": {
                "dataset_id": left_dataset_id,
                "location_id": left["location_id"],
                "mean": round(left_mean, 3),
            },
            "right": {
                "dataset_id": right_dataset_id,
                "location_id": right["location_id"],
                "mean": round(right_mean, 3),
            },
            "difference_left_minus_right": round(left_mean - right_mean, 3),
            "note": "Comparison uses dataset-level means and does not infer conditions between coordinates.",
        }

    @staticmethod
    def _number(value: str | None) -> float | None:
        try:
            if value is None or value in ("", "null"):
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _period_key(timestamp: str, period: str) -> str:
        date_part = timestamp[:10]
        parsed = date.fromisoformat(date_part)
        if period == "daily":
            return date_part
        if period == "monthly":
            return f"{parsed.year}-{parsed.month:02d}"
        if period == "annual":
            return str(parsed.year)
        season = (
            "monsoon"
            if 6 <= parsed.month <= 9
            else "pre-monsoon"
            if 3 <= parsed.month <= 5
            else "post-monsoon"
            if 10 <= parsed.month <= 11
            else "winter"
        )
        return f"{parsed.year}-{season}"

    def _mean(self, dataset_id: str, variable: str) -> float | None:
        values = [
            value
            for row in self.read_rows(dataset_id)
            if (value := self._number(row.get(variable))) is not None
        ]
        return sum(values) / len(values) if values else None
