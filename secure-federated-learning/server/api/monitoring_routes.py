from __future__ import annotations

from fastapi import APIRouter

from server.dependencies import get_coordinator

router = APIRouter(prefix="/monitoring")


@router.get("/clients")
async def clients() -> dict:
    coordinator = get_coordinator()
    return {"clients": coordinator.monitoring_clients()}


@router.get("/round")
async def round_status() -> dict:
    coordinator = get_coordinator()
    return coordinator.monitoring_round()


@router.get("/metrics")
async def metrics() -> dict:
    coordinator = get_coordinator()
    return coordinator.monitoring_metrics()


@router.get("/privacy")
async def privacy() -> dict:
    coordinator = get_coordinator()
    return coordinator.monitoring_privacy()


@router.get("/anomalies")
async def anomalies() -> dict:
    coordinator = get_coordinator()
    return {"anomalies": coordinator.monitoring_anomalies()}
