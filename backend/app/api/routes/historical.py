import csv
from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_database, get_location_service, get_provider
from app.core.config import get_settings
from app.core.errors import ApiError
from app.models.schemas import HistoricalIngestionRequest
from app.services.historical import HistoricalService

router = APIRouter()


def get_historical_service() -> HistoricalService:
    return HistoricalService(
        get_database(), get_settings().data_dir, get_location_service(), get_provider()
    )


@router.post("/ingestions", status_code=202)
async def create_ingestion(
    request: HistoricalIngestionRequest,
    background_tasks: BackgroundTasks,
    service: HistoricalService = Depends(get_historical_service),
) -> dict:
    get_location_service().get(request.location_id)
    if (
        request.end_date - request.start_date
    ).days + 1 > get_settings().max_historical_days:
        raise ApiError(
            422,
            "historical_range_too_large",
            f"Historical ingestions are limited to {get_settings().max_historical_days} days per job.",
        )
    if request.end_date > date.today():
        raise ApiError(
            422,
            "invalid_historical_range",
            "Historical ingestion cannot include future dates.",
        )
    job = service.create_job(request.location_id, request.start_date, request.end_date)
    background_tasks.add_task(service.run_ingestion, job["id"])
    return {
        "job": job,
        "note": "Ingestion runs in the background. Historical output is labelled reanalysis when provided by the selected source.",
    }


@router.get("/ingestions/{job_id}")
async def ingestion_status(
    job_id: str, service: HistoricalService = Depends(get_historical_service)
) -> dict:
    return service.get_job(job_id)


@router.get("/datasets")
async def datasets(
    location_id: str | None = Query(default=None),
    service: HistoricalService = Depends(get_historical_service),
) -> dict:
    return {"items": service.list_datasets(location_id)}


@router.get("/summary")
async def summary(
    dataset_id: str,
    variable: str = Query(default="temperature_2m_mean"),
    period: str = Query(default="monthly", pattern="^(daily|monthly|seasonal|annual)$"),
    baseline_dataset_id: str | None = None,
    service: HistoricalService = Depends(get_historical_service),
) -> dict:
    return service.summary(dataset_id, variable, period, baseline_dataset_id)


@router.get("/monsoon")
async def monsoon(
    dataset_id: str,
    start_month: int = Query(default=6, ge=1, le=12),
    end_month: int = Query(default=9, ge=1, le=12),
    service: HistoricalService = Depends(get_historical_service),
) -> dict:
    return service.monsoon(dataset_id, start_month, end_month)


@router.get("/heat-patterns")
async def heat_patterns(
    dataset_id: str,
    threshold_celsius: float = Query(default=40.0, ge=20.0, le=60.0),
    service: HistoricalService = Depends(get_historical_service),
) -> dict:
    return service.heat_patterns(dataset_id, threshold_celsius)


@router.get("/compare")
async def compare(
    left_dataset_id: str,
    right_dataset_id: str,
    variable: str = Query(default="temperature_2m_mean"),
    service: HistoricalService = Depends(get_historical_service),
) -> dict:
    return service.compare(left_dataset_id, right_dataset_id, variable)


@router.get("/summary.csv")
async def export_summary_csv(
    dataset_id: str,
    variable: str = Query(default="temperature_2m_mean"),
    period: str = Query(default="monthly", pattern="^(daily|monthly|seasonal|annual)$"),
    baseline_dataset_id: str | None = None,
    service: HistoricalService = Depends(get_historical_service),
):
    result = service.summary(dataset_id, variable, period, baseline_dataset_id)

    def rows():
        columns = ["period", "count", "mean", "total", "min", "max", "anomaly"]
        yield _csv_line(columns) + "\n"
        for item in result["items"]:
            yield _csv_line([item.get(column) for column in columns]) + "\n"

    return StreamingResponse(
        rows(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="alya-summary-{dataset_id}.csv"'
        },
    )


@router.get("/export.csv")
async def export_csv(
    dataset_id: str, service: HistoricalService = Depends(get_historical_service)
):
    service.dataset(dataset_id)

    def rows():
        iterator = service.read_rows(dataset_id)
        first = next(iterator, None)
        if first is None:
            return
        yield ",".join(first.keys()) + "\n"
        yield _csv_line(first.values()) + "\n"
        for row in iterator:
            yield _csv_line(row.values()) + "\n"

    return StreamingResponse(
        rows(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="alya-historical-{dataset_id}.csv"'
        },
    )


def _csv_line(values):
    import io

    output = io.StringIO()
    csv.writer(output).writerow(values)
    return output.getvalue().rstrip("\r\n")
