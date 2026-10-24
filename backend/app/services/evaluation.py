import json
import math
import uuid
from datetime import UTC, datetime

from app.core.database import Database
from app.core.errors import ApiError
from app.services.historical import HistoricalService, VARIABLE_UNITS


class EvaluationService:
    def __init__(self, database: Database, historical: HistoricalService):
        self.database = database
        self.historical = historical

    def evaluate_persistence(self, dataset_id: str, target: str) -> dict:
        if target not in VARIABLE_UNITS:
            raise ApiError(
                422,
                "unsupported_variable",
                "The requested target variable is unsupported.",
            )
        values = []
        for row in self.historical.read_rows(dataset_id):
            value = self.historical._number(row.get(target))
            if value is not None:
                values.append((row["date"], value))
        if len(values) < 20:
            raise ApiError(
                422,
                "insufficient_evaluation_data",
                "At least 20 valid chronological samples are required for evaluation.",
            )
        split = max(1, int(len(values) * 0.8))
        test = values[split:]
        if len(test) < 2:
            raise ApiError(
                422,
                "insufficient_evaluation_data",
                "The chronological test split is too small.",
            )
        predictions, actuals = [], []
        for index, (_, actual) in enumerate(test):
            source_index = split + index - 1
            predictions.append(values[source_index][1])
            actuals.append(actual)
        errors = [
            actual - prediction for actual, prediction in zip(actuals, predictions)
        ]
        result = {
            "id": str(uuid.uuid4()),
            "model_name": "persistence-baseline",
            "model_version": "1",
            "status": "baseline_only",
            "target_variable": target,
            "unit": VARIABLE_UNITS[target],
            "dataset_id": dataset_id,
            "training_period": {
                "start": values[0][0],
                "end": values[split - 1][0],
                "samples": split,
            },
            "test_period": {
                "start": test[0][0],
                "end": test[-1][0],
                "samples": len(test),
            },
            "metrics": {
                "mae": round(sum(abs(error) for error in errors) / len(errors), 4),
                "rmse": round(
                    math.sqrt(sum(error**2 for error in errors) / len(errors)), 4
                ),
            },
            "methodology": "Chronological holdout. Persistence predicts each value from the immediately preceding valid daily value. No ML model was trained or deployed.",
            "limitations": "Irregular or missing dates are excluded; this baseline does not establish an improved forecast.",
        }
        with self.database.connection() as connection:
            connection.execute(
                "INSERT INTO model_evaluations(id, model_name, target_variable, unit, evaluation_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    result["id"],
                    result["model_name"],
                    target,
                    result["unit"],
                    json.dumps(result),
                    datetime.now(UTC).isoformat(),
                ),
            )
        return result

    def list(self) -> list[dict]:
        with self.database.connection() as connection:
            rows = connection.execute(
                "SELECT evaluation_json FROM model_evaluations ORDER BY created_at DESC"
            ).fetchall()
        return [json.loads(row["evaluation_json"]) for row in rows]
