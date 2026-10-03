from __future__ import annotations

from fastapi import APIRouter, HTTPException

from server.dependencies import get_coordinator
from server.schemas.models import ModelRequest
from server.schemas.training import ModelUpdate, TrainingCompleteRequest, TrainingJoinRequest

router = APIRouter(prefix="/training")


@router.get("/status")
async def training_status() -> dict:
    coordinator = get_coordinator()
    return coordinator.get_training_status()


@router.post("/join")
async def join_training(payload: TrainingJoinRequest) -> dict:
    coordinator = get_coordinator()
    if not coordinator.client_manager.authenticator.validate_client_id(payload.client_id):
        raise HTTPException(status_code=403, detail="Unknown client identity.")
    return coordinator.join_training_round(payload.client_id, payload.round_id)


@router.get("/model")
async def get_global_model(client_id: str) -> dict:
    coordinator = get_coordinator()
    try:
        return coordinator.get_model_snapshot(client_id)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/update")
async def submit_update(payload: ModelUpdate) -> dict:
    coordinator = get_coordinator()
    result = coordinator.submit_update(payload.model_dump())
    if not result["accepted"]:
        return result
    return result


@router.post("/complete")
async def complete_training(payload: TrainingCompleteRequest) -> dict:
    coordinator = get_coordinator()
    return coordinator.complete_round(payload.client_id, payload.round_id)


@router.post("/admin/start-round")
async def start_round() -> dict:
    coordinator = get_coordinator()
    return coordinator.start_round()


@router.post("/admin/stop-round")
async def stop_round() -> dict:
    coordinator = get_coordinator()
    coordinator.state.running = False
    return {"status": "stopped", "round_id": coordinator.state.current_round}


@router.post("/admin/recover")
async def recover_round() -> dict:
    coordinator = get_coordinator()
    return coordinator.recover_latest_checkpoint()
