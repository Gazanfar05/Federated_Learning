from __future__ import annotations

from fastapi import APIRouter

from server.config import settings
from server.dependencies import get_coordinator
from server.services.openfl_monitor import OpenFLMonitor
from server.services.openfl_metrics import OpenFLMetrics
from server.services.openfl_events import OpenFLEvents

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


@router.get("/openfl")
async def openfl_status() -> dict:
    return OpenFLMonitor(settings.openfl_workspace_dir).inspect()


@router.get("/openfl/metrics")
async def openfl_metrics() -> dict:
    return OpenFLMetrics(settings.openfl_workspace_dir).inspect()


@router.get("/openfl/events")
async def openfl_events() -> dict:
    return OpenFLEvents(
        settings.openfl_workspace_dir,
        settings.openfl_event_log_file,
    ).inspect()
