from fastapi import APIRouter, Depends

from app.api.dependencies import get_database
from app.api.routes.historical import get_historical_service
from app.models.schemas import EvaluationRequest
from app.services.evaluation import EvaluationService
from app.services.historical import HistoricalService

router = APIRouter()


def get_evaluation_service(
    historical: HistoricalService = Depends(get_historical_service),
) -> EvaluationService:
    return EvaluationService(get_database(), historical)


@router.post("")
async def evaluate(
    request: EvaluationRequest,
    service: EvaluationService = Depends(get_evaluation_service),
) -> dict:
    return service.evaluate_persistence(request.dataset_id, request.target_variable)


@router.get("")
async def evaluations(
    service: EvaluationService = Depends(get_evaluation_service),
) -> dict:
    return {
        "items": service.list(),
        "note": "No experimental model is deployed. Records are reproducible baseline evaluations only.",
    }
