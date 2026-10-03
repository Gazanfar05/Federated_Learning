from __future__ import annotations

from fastapi import APIRouter, HTTPException

from server.dependencies import get_coordinator
from server.schemas.auth import ClientHeartbeat, ClientRegistration

router = APIRouter(prefix="/auth")


@router.post("/register")
async def register_client(payload: ClientRegistration) -> dict:
    coordinator = get_coordinator()
    ok = coordinator.register_client(payload.client_id, payload.certificate_identity)
    if not ok:
        raise HTTPException(status_code=403, detail="Unknown client identity. Registration rejected.")
    return {
        "status": "registered",
        "client_id": payload.client_id,
        "certificate_identity": payload.certificate_identity,
    }


@router.post("/heartbeat")
async def heartbeat(payload: ClientHeartbeat) -> dict:
    coordinator = get_coordinator()
    ok = coordinator.authenticate_client(payload.client_id, payload.certificate_identity)
    if not ok:
        raise HTTPException(status_code=401, detail="Authentication failed. Client rejected.")
    return {
        "status": "alive",
        "client_id": payload.client_id,
        "round_id": coordinator.state.current_round,
    }
