from fastapi import APIRouter, Query

from app.api.dependencies import get_location_service
from app.models.schemas import LocationResponse, LocationsResponse

router = APIRouter()


@router.get("", response_model=LocationsResponse)
async def list_locations(
    query: str | None = Query(default=None, min_length=1, max_length=100),
    state: str | None = Query(default=None, min_length=1, max_length=100),
    loc_type: str | None = Query(default=None, alias="type", pattern="^(city|district|state)$"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    locations, total = get_location_service().search(query, state, offset, limit, loc_type)
    return {
        "items": locations,
        "pagination": {"offset": offset, "limit": limit, "total": total},
        "catalogue_coverage": "Catalogue covers Indian states, union territories, representative districts, and configured cities. District and state coordinates represent administrative points; they do not assume dedicated forecast grid points for every district.",
    }


@router.get("/states")
async def list_states() -> dict:
    items = get_location_service().states()
    return {
        "items": items,
        "total": len(items),
        "note": "Reference administrative centres for Indian states and union territories.",
    }


@router.get("/{location_id}", response_model=LocationResponse)
async def location_detail(location_id: str) -> dict:
    return get_location_service().get(location_id)
