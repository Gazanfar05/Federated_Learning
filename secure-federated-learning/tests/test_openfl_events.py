import json
from pathlib import Path

from fastapi.testclient import TestClient

from server.api import monitoring_routes
from server.main import app
from server.services.openfl_events import OpenFLEvents


def test_missing_event_source_is_unavailable(tmp_path: Path):
    result = OpenFLEvents(tmp_path / "workspace").inspect()
    assert result["events_available"] is False
    assert result["events"] == []


def test_empty_log_is_unavailable(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    log = workspace / "events.jsonl"
    log.touch()
    result = OpenFLEvents(workspace, "events.jsonl").inspect()
    assert result["events_available"] is False
    assert result["events"] == []


def test_structured_events_are_extracted_safely(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    log = workspace / "events.jsonl"
    log.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "event_type": "round_completed",
                        "timestamp": "2026-10-19T15:00:00Z",
                        "collaborator_id": "hospital_01",
                        "round_number": 2,
                        "message": "<not html>",
                    }
                ),
                json.dumps({"event_type": "future_event", "message": "unknown type"}),
            ]
        ),
        encoding="utf-8",
    )
    result = OpenFLEvents(workspace, "events.jsonl").inspect()
    assert result["events_available"] is True
    assert result["events"][0]["event_type"] == "round_completed"
    assert result["events"][0]["collaborator_id"] == "hospital_01"
    assert result["events"][1] == {"event_type": "unknown", "message": "unknown type"}


def test_malformed_and_incomplete_records_are_skipped(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "events.jsonl").write_text(
        '{"event_type":"round_started","timestamp":"invalid"}\n'
        'not json\n'
        '{"event_type":"round_started","round_number":-1}\n',
        encoding="utf-8",
    )
    result = OpenFLEvents(workspace, "events.jsonl").inspect()
    assert result["events_available"] is False
    assert len(result["limitations"]) == 4


def test_path_traversal_is_rejected(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    result = OpenFLEvents(workspace, "../events.jsonl").inspect()
    assert result["events_available"] is False


def test_events_endpoint_schema(tmp_path: Path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.setattr(
        monitoring_routes,
        "OpenFLEvents",
        lambda configured_workspace, configured_log: OpenFLEvents(workspace),
    )
    response = TestClient(app).get("/monitoring/openfl/events")
    assert response.status_code == 200
    assert set(response.json()) == {"events_available", "source_description", "events", "limitations"}
