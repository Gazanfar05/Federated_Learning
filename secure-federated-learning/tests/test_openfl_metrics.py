import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from server.api import monitoring_routes
from server.main import app
from server.services.openfl_metrics import OpenFLMetrics


def _database(workspace: Path, values: list[tuple[str, object]]) -> None:
    database_dir = workspace / "local_state"
    database_dir.mkdir(parents=True)
    with sqlite3.connect(database_dir / "tensor.db") as connection:
        connection.execute("CREATE TABLE key_value_store (key TEXT PRIMARY KEY, value REAL NOT NULL)")
        connection.executemany("INSERT INTO key_value_store (key, value) VALUES (?, ?)", values)
        connection.commit()


def test_missing_metrics_source_is_unavailable(tmp_path: Path):
    result = OpenFLMetrics(tmp_path / "missing").inspect()
    assert result["metrics_available"] is False
    assert result["best_observed_result"] is None


def test_verified_best_score_has_accuracy_semantics(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _database(workspace, [("round_number", 2.0), ("best_score", 0.6875)])

    result = OpenFLMetrics(workspace).inspect()
    assert result["metrics_available"] is True
    assert result["metric_name"] == "accuracy"
    assert result["metric_semantics_verified"] is True
    assert result["best_observed_result"] == {"value": 0.6875, "round": None}
    assert result["round_results"] == []


def test_incomplete_and_invalid_records_are_not_exposed(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _database(workspace, [("round_number", 2.0)])
    result = OpenFLMetrics(workspace).inspect()
    assert result["metrics_available"] is False

    invalid_workspace = tmp_path / "invalid"
    invalid_workspace.mkdir()
    _database(invalid_workspace, [("round_number", -1.0), ("best_score", 0.5)])
    invalid_result = OpenFLMetrics(invalid_workspace).inspect()
    assert invalid_result["metrics_available"] is False


def test_endpoint_returns_metrics_schema_without_paths(tmp_path: Path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _database(workspace, [("round_number", 2.0), ("best_score", 0.6875)])
    monkeypatch.setattr(
        monitoring_routes,
        "OpenFLMetrics",
        lambda configured_path: OpenFLMetrics(workspace),
    )

    response = TestClient(app).get("/monitoring/openfl/metrics")
    assert response.status_code == 200
    payload = response.json()
    assert payload["metric_name"] == "accuracy"
    assert "workspace" not in str(payload).lower()
    assert "tensor.db" not in str(payload).lower()
