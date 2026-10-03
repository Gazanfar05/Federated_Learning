from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from server.dependencies import get_coordinator

router = APIRouter()


@router.get("/server-status", response_class=HTMLResponse)
async def root() -> str:
    return """
    <html>
      <head><title>Secure Federated Learning Server</title></head>
      <body>
        <h1>SECURE FEDERATED LEARNING SERVER</h1>
        <p>Server Status: ONLINE</p>
        <p>Current Round: 0</p>
        <p>Protocol: TLS 1.3 + secure aggregation demo</p>
      </body>
    </html>
    """


@router.get("/health")
async def health() -> dict:
    coordinator = get_coordinator()
    return {
        "status": "healthy",
        "service": "secure-federated-learning",
        "round": coordinator.state.current_round,
        "model_version": coordinator.model_version,
    }
