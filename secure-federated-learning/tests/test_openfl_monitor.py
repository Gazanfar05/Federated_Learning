from pathlib import Path

from fastapi.testclient import TestClient

from server.api import monitoring_routes
from server.main import app
from server.services.openfl_monitor import OpenFLMonitor


def _write_workspace(workspace: Path, *, valid_config: bool = True) -> None:
    (workspace / "plan").mkdir(parents=True)
    (workspace / "save").mkdir()
    (workspace / "local_state").mkdir()
    if valid_config:
        (workspace / "plan/cols.yaml").write_text(
            "collaborators:\n- hospital_01\n- hospital_02\n- hospital_03\n",
            encoding="utf-8",
        )
        (workspace / "plan/plan.yaml").write_text(
            "aggregator:\n  settings:\n    rounds_to_train: 3\n",
            encoding="utf-8",
        )
        (workspace / "plan/data.yaml").write_text(
            "hospital_01,/workspace/data/hospital_01/hospital1.csv\n"
            "hospital_02,/workspace/data/hospital_02/hospital2.csv\n"
            "hospital_03,/workspace/data/hospital_03/hospital3.csv\n",
            encoding="utf-8",
        )


def test_missing_workspace_is_unavailable(tmp_path: Path):
    result = OpenFLMonitor(tmp_path / "missing").inspect()
    assert result["workspace_available"] is False
    assert result["federation_status"] == "unknown"
    assert result["configured_collaborators"] == []


def test_workspace_without_artifacts_is_available_but_unknown(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    result = OpenFLMonitor(workspace).inspect()
    assert result["workspace_available"] is True
    assert result["available_checkpoint_names"] == []
    assert result["experiment_database_available"] is False
    assert result["federation_status"] == "unknown"


def test_missing_database_is_reported_unavailable(tmp_path: Path):
    workspace = tmp_path / "workspace"
    _write_workspace(workspace)
    result = OpenFLMonitor(workspace).inspect()
    assert result["experiment_database_available"] is False


def test_valid_configuration_and_artifacts_are_reported(tmp_path: Path):
    workspace = tmp_path / "workspace"
    _write_workspace(workspace)
    (workspace / "save/best.pbuf").write_bytes(b"not parsed")
    (workspace / "local_state/tensor.db").touch()

    result = OpenFLMonitor(workspace).inspect()
    assert result["configured_collaborators"] == ["hospital_01", "hospital_02", "hospital_03"]
    assert result["configured_rounds"] == 3
    assert result["available_checkpoint_names"] == ["best"]
    assert result["experiment_database_available"] is True


def test_malformed_configuration_is_explicit(tmp_path: Path):
    workspace = tmp_path / "workspace"
    _write_workspace(workspace, valid_config=False)
    result = OpenFLMonitor(workspace).inspect()
    assert result["configured_collaborators"] == []
    assert result["configured_rounds"] is None
    assert any("malformed" in item for item in result["limitations"])


def test_database_is_opened_read_only(tmp_path: Path):
    workspace = tmp_path / "workspace"
    _write_workspace(workspace)
    database = workspace / "local_state/tensor.db"
    import sqlite3

    with sqlite3.connect(database) as connection:
        connection.execute("create table marker (value text)")
        connection.commit()

    result = OpenFLMonitor(workspace).inspect()
    assert result["experiment_database_available"] is True
    assert not (workspace / "local_state/tensor.db-wal").exists()


def test_invalid_workspace_path_is_unavailable(tmp_path: Path):
    file_path = tmp_path / "not-a-directory"
    file_path.write_text("not a workspace", encoding="utf-8")
    result = OpenFLMonitor(file_path).inspect()
    assert result["workspace_available"] is False


def test_artifact_path_traversal_is_rejected(tmp_path: Path):
    monitor = OpenFLMonitor(tmp_path / "workspace")
    assert monitor._safe_child(Path("../outside")) is None


def test_openfl_endpoint_returns_structured_status(tmp_path: Path, monkeypatch):
    workspace = tmp_path / "workspace"
    _write_workspace(workspace)
    monkeypatch.setattr(
        monitoring_routes,
        "OpenFLMonitor",
        lambda configured_path: OpenFLMonitor(workspace),
    )

    response = TestClient(app).get("/monitoring/openfl")
    assert response.status_code == 200
    payload = response.json()
    assert payload["workspace_available"] is True
    assert payload["configured_rounds"] == 3
    assert "workspace_dir" not in payload
