from __future__ import annotations

from fastapi.testclient import TestClient

from server.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_frontend_assets_served():
    index_response = client.get("/")
    assert index_response.status_code == 200
    assert "SECURE FL HEALTHCARE" in index_response.text

    js_response = client.get("/app.js")
    assert js_response.status_code == 200
    assert "SECURE FEDERATED LEARNING" in js_response.text

    status_response = client.get("/server-status")
    assert status_response.status_code == 200
    assert "Server Status: ONLINE" in status_response.text


def test_auth_register_and_monitoring():
    response = client.post(
        "/auth/register",
        json={"client_id": "hospital_01", "certificate_identity": "hospital_01"},
    )
    assert response.status_code == 200

    status_response = client.get("/training/status")
    assert status_response.status_code == 200

    privacy_response = client.get("/monitoring/privacy")
    assert privacy_response.status_code == 200


def test_update_submission_and_round_completion():
    update = {
        "client_id": "hospital_01",
        "round_id": 1,
        "model_version": 1,
        "num_samples": 10,
        "update_hash": "abc123456789",
        "protected_update": [0.1] * 8,
        "timestamp": "2026-10-03T00:00:00Z",
    }

    response = client.post("/training/update", json=update)
    assert response.status_code == 200
    assert response.json()["accepted"] is True

    complete_response = client.post("/training/complete", json={"client_id": "hospital_01", "round_id": 1})
    assert complete_response.status_code == 200
