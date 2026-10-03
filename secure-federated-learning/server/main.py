from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from server.api.auth_routes import router as auth_router
from server.api.health_routes import router as health_router
from server.api.model_routes import router as model_router
from server.api.monitoring_routes import router as monitoring_router
from server.api.training_routes import router as training_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Secure Federated Learning Server",
        description="Central server for privacy-preserving diabetes prediction in a multi-hospital setup.",
        version="1.0.0",
    )
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(training_router)
    app.include_router(model_router)
    app.include_router(monitoring_router)

    frontend_dir = Path(__file__).resolve().parents[1] / "frontend"
    if frontend_dir.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
    return app


app = create_app()
