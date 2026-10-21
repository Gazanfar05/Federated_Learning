from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest
from fastapi.testclient import TestClient

from server.config import settings
from server.dependencies import get_coordinator
from server.main import app
from server.checkpointing.checkpoint_manager import CheckpointManager


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Keep API tests away from the real project checkpoints.
    test_settings = replace(
        settings,
        checkpoint_dir=tmp_path / "checkpoints",
    )
    monkeypatch.setattr(
        "server.core.coordinator.settings",
        test_settings,
    )
    get_coordinator.cache_clear()
    with TestClient(app) as test_client:
        yield test_client
    get_coordinator.cache_clear()


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_frontend_assets_served(client):
    index_response = client.get("/")
    assert index_response.status_code == 200
    assert "SECURE FL HEALTHCARE" in index_response.text

    js_response = client.get("/app.js")
    assert js_response.status_code == 200
    assert "SECURE FEDERATED LEARNING" in js_response.text

    status_response = client.get("/server-status")
    assert status_response.status_code == 200
    assert "Server Status: ONLINE" in status_response.text


def test_auth_register_and_monitoring(client):
    response = client.post(
        "/auth/register",
        json={
            "client_id": "hospital_01",
            "certificate_identity": "hospital_01",
        },
    )
    assert response.status_code == 200

    status_response = client.get("/training/status")
    assert status_response.status_code == 200

    privacy_response = client.get("/monitoring/privacy")
    assert privacy_response.status_code == 200


def test_update_submission_and_round_completion(client):
    coordinator = get_coordinator()
    start = client.post("/training/admin/start-round")
    assert start.status_code == 200
    round_id = start.json()["round_id"]

    model = client.get(
        "/training/model", params={"client_id": "hospital_01"}
    ).json()
    initial = np.asarray(model["model_vector"], dtype=np.float32)
    assert initial.size == 433

    # Two clients are required by the default quorum.
    for client_id, num_samples, delta in [
        ("hospital_01", 10, 0.01),
        ("hospital_02", 30, 0.02),
    ]:
        update = {
            "client_id": client_id,
            "round_id": round_id,
            "model_version": model["model_version"],
            "num_samples": num_samples,
            "update_hash": f"test-update-{client_id}-123",
            "protected_update": (initial + delta).tolist(),
            "reference_model": initial.tolist(),
            "timestamp": "2026-10-21T00:00:00Z",
        }
        response = client.post("/training/update", json=update)
        assert response.status_code == 200
        assert response.json()["accepted"] is True, response.json()

    before_version = coordinator.model_version
    complete_response = client.post(
        "/training/complete",
        json={"client_id": "hospital_01", "round_id": round_id},
    )
    assert complete_response.status_code == 200
    completed = complete_response.json()
    assert completed["status"] == "completed", completed
    assert coordinator.model_version == before_version + 1
    assert completed["metrics"]["available"] is False


def test_rejects_wrong_vector_size(client):
    client.post("/training/admin/start-round")
    model = client.get(
        "/training/model", params={"client_id": "hospital_01"}
    ).json()

    update = {
        "client_id": "hospital_01",
        "round_id": model["round_id"],
        "model_version": model["model_version"],
        "num_samples": 10,
        "update_hash": "wrong-vector-size-test",
        "protected_update": [0.1] * 8,
        "reference_model": model["model_vector"],
        "timestamp": "2026-10-21T00:00:00Z",
    }
    response = client.post("/training/update", json=update)
    assert response.status_code == 200
    assert response.json()["accepted"] is False
    assert "Expected 433 model values" in response.json()["reason"]


def test_rejects_inactive_round(client):
    client.post("/training/admin/start-round")
    client.post("/training/admin/stop-round")
    model = client.get(
        "/training/model", params={"client_id": "hospital_01"}
    ).json()
    update = {
        "client_id": "hospital_01",
        "round_id": model["round_id"],
        "model_version": model["model_version"],
        "num_samples": 10,
        "update_hash": "inactive-round-test",
        "protected_update": model["model_vector"],
        "reference_model": model["model_vector"],
        "timestamp": "2026-10-21T00:00:00Z",
    }
    response = client.post("/training/update", json=update)
    assert response.status_code == 200, response.text
    assert response.json()["accepted"] is False, response.json()
    assert "not active" in response.json()["reason"]


def test_rejects_stale_model_version(client):
    client.post("/training/admin/start-round")
    coordinator = get_coordinator()
    coordinator.model_version = 2
    coordinator.state.model_version = 2
    model = client.get(
        "/training/model", params={"client_id": "hospital_01"}
    ).json()
    update = {
        "client_id": "hospital_01",
        "round_id": model["round_id"],
        "model_version": 1,
        "num_samples": 10,
        "update_hash": "stale-model-version-test",
        "protected_update": model["model_vector"],
        "reference_model": model["model_vector"],
        "timestamp": "2026-10-21T00:00:00Z",
    }
    response = client.post("/training/update", json=update)
    assert response.status_code == 200, response.text
    assert response.json()["accepted"] is False, response.json()
    assert "model version" in response.json()["reason"]


def test_rejects_duplicate_client_submission(client):
    client.post("/training/admin/start-round")
    model = client.get(
        "/training/model", params={"client_id": "hospital_01"}
    ).json()
    update = {
        "client_id": "hospital_01",
        "round_id": model["round_id"],
        "model_version": model["model_version"],
        "num_samples": 10,
        "update_hash": "duplicate-submission-test",
        "protected_update": (
            np.asarray(model["model_vector"], dtype=np.float32) + 0.01
        ).tolist(),
        "reference_model": model["model_vector"],
        "timestamp": "2026-10-21T00:00:00Z",
    }
    first = client.post("/training/update", json=update).json()
    second = client.post("/training/update", json=update).json()

    assert first["accepted"] is True, first
    assert second["accepted"] is False, second
    assert "already submitted" in second["reason"]


def test_rejects_mismatched_reference_model(client):
    client.post("/training/admin/start-round")
    model = client.get(
        "/training/model", params={"client_id": "hospital_02"}
    ).json()
    reference = np.asarray(model["model_vector"], dtype=np.float32)
    reference[0] += 10.0

    update = {
        "client_id": "hospital_02",
        "round_id": model["round_id"],
        "model_version": model["model_version"],
        "num_samples": 10,
        "update_hash": "reference-mismatch-test",
        "protected_update": model["model_vector"],
        "reference_model": reference.tolist(),
        "timestamp": "2026-10-21T00:00:00Z",
    }
    response = client.post("/training/update", json=update)
    assert response.status_code == 200
    assert response.json()["accepted"] is False
    assert "reference model" in response.json()["reason"]
