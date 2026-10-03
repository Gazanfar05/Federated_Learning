from __future__ import annotations

from fastapi import APIRouter, HTTPException

from server.dependencies import get_coordinator
from server.schemas.models import ModelRequest, ModelResponse

router = APIRouter(prefix="/model")


@router.get("/current")
async def get_model(client_id: str) -> dict:
    coordinator = get_coordinator()
    return coordinator.get_model_snapshot(client_id)


@router.post("/current")
async def fetch_model(payload: ModelRequest) -> ModelResponse:
    coordinator = get_coordinator()
    data = coordinator.get_model_snapshot(payload.client_id)
    return ModelResponse(
        client_id=data["client_id"],
        model_version=data["model_version"],
        round_id=data["round_id"],
        architecture=data["architecture"],
        parameter_count=data["parameter_count"],
        update_hash=data["update_hash"],
    )
