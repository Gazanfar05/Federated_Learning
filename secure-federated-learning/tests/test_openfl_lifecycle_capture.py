import importlib
import json
import sys
from pathlib import Path

import pytest


WORKSPACE = Path(__file__).resolve().parents[2] / "openfl-diabetes-workspace"


@pytest.fixture
def lifecycle_module(monkeypatch):
    monkeypatch.syspath_prepend(str(WORKSPACE))
    sys.modules.pop("src.openfl_event_callback", None)
    sys.modules.pop("src.event_components", None)
    return importlib.import_module("src.openfl_event_callback")


def read_records(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_callback_import_and_aggregator_lifecycle(lifecycle_module, tmp_path):
    callback = lifecycle_module.OpenFLLifecycleCallback(
        role="aggregator",
        workspace_dir=tmp_path,
        event_log_file="events.jsonl",
    )
    callback.on_experiment_begin()
    callback.on_round_begin(0)
    callback.on_round_end(0)
    callback.on_experiment_end()

    records = read_records(tmp_path / "events.jsonl")
    assert [record["event_type"] for record in records] == [
        "aggregator_started",
        "round_started",
        "round_completed",
        "experiment_ended",
    ]
    assert records[1]["round_number"] == 0
    assert "collaborator_id" not in records[0]


def test_collaborator_task_lifecycle_and_timestamp(lifecycle_module, tmp_path):
    callback = lifecycle_module.OpenFLLifecycleCallback(
        role="collaborator",
        collaborator_id="hospital_01",
        workspace_dir=tmp_path,
        event_log_file="events.jsonl",
    )
    callback.on_experiment_begin()
    callback.on_round_begin(2)
    callback.on_task_begin("train", 2)
    callback.on_task_end("train", 2)
    callback.on_round_end(2)

    records = read_records(tmp_path / "events.jsonl")
    assert [record["event_type"] for record in records] == [
        "round_started",
        "local_training_started",
        "task_completed",
        "round_completed",
    ]
    assert all(record["collaborator_id"] == "hospital_01" for record in records)
    assert all(record["timestamp"].endswith("+00:00") for record in records)


def test_callback_rejects_malformed_arguments_and_path_traversal(lifecycle_module, tmp_path):
    callback = lifecycle_module.OpenFLLifecycleCallback(
        role="aggregator",
        workspace_dir=tmp_path,
        event_log_file="events.jsonl",
    )
    with pytest.raises(ValueError):
        callback.on_round_begin(-1)
    with pytest.raises(ValueError):
        lifecycle_module.OpenFLLifecycleCallback(
            role="collaborator",
            collaborator_id="not-a-hospital",
            workspace_dir=tmp_path,
        )
    with pytest.raises(ValueError):
        lifecycle_module.OpenFLLifecycleCallback(
            role="aggregator",
            workspace_dir=tmp_path,
            event_log_file="../events.jsonl",
        )


def test_callback_reports_output_failure(lifecycle_module, monkeypatch, tmp_path):
    callback = lifecycle_module.OpenFLLifecycleCallback(
        role="aggregator",
        workspace_dir=tmp_path,
        event_log_file="events.jsonl",
    )

    def fail_open(*args, **kwargs):
        raise OSError("permission denied")

    monkeypatch.setattr(lifecycle_module.os, "open", fail_open)
    with pytest.raises(RuntimeError, match="Unable to write"):
        callback.on_experiment_begin()


def test_wrappers_preserve_existing_callbacks(lifecycle_module, monkeypatch, tmp_path):
    components = importlib.import_module("src.event_components")
    existing = lifecycle_module.Callback()
    aggregator_seen = {}
    collaborator_seen = {}

    def fake_aggregator_init(self, *args, **kwargs):
        aggregator_seen["callbacks"] = kwargs["callbacks"]

    def fake_collaborator_init(self, *args, **kwargs):
        collaborator_seen["callbacks"] = kwargs["callbacks"]

    monkeypatch.setattr(components.Aggregator, "__init__", fake_aggregator_init)
    monkeypatch.setattr(components.Collaborator, "__init__", fake_collaborator_init)
    components.EventAggregator(callbacks=[existing], workspace_dir=tmp_path)
    components.EventCollaborator(
        collaborator_name="hospital_01",
        callbacks=existing,
        workspace_dir=tmp_path,
    )

    assert aggregator_seen["callbacks"][0] is existing
    assert isinstance(aggregator_seen["callbacks"][1], lifecycle_module.OpenFLLifecycleCallback)
    assert collaborator_seen["callbacks"][0] is existing
    assert isinstance(collaborator_seen["callbacks"][1], lifecycle_module.OpenFLLifecycleCallback)


def test_plan_templates_import_from_fixture(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(WORKSPACE))
    plan = {
        "aggregator": {"template": "src.event_components.EventAggregator", "settings": {}},
        "collaborator": {"template": "src.event_components.EventCollaborator", "settings": {}},
    }
    from openfl.federated import Plan

    assert Plan.import_(plan["aggregator"]["template"]).__name__ == "EventAggregator"
    assert Plan.import_(plan["collaborator"]["template"]).__name__ == "EventCollaborator"


def test_generated_records_are_accepted_by_existing_adapter(lifecycle_module, tmp_path):
    callback = lifecycle_module.OpenFLLifecycleCallback(
        role="collaborator",
        collaborator_id="hospital_02",
        workspace_dir=tmp_path,
        event_log_file="events.jsonl",
    )
    callback.on_task_begin("train", 1)

    from server.services.openfl_events import OpenFLEvents

    result = OpenFLEvents(tmp_path, "events.jsonl").inspect()
    assert result["events_available"] is True
    assert result["events"][0]["event_type"] == "local_training_started"


def test_callback_and_adapter_share_explicit_fixture_path(lifecycle_module, tmp_path):
    event_file = "fixture/events.jsonl"
    callback = lifecycle_module.OpenFLLifecycleCallback(
        role="aggregator",
        workspace_dir=tmp_path,
        event_log_file=event_file,
    )
    callback.on_experiment_end()

    from server.services.openfl_events import OpenFLEvents

    result = OpenFLEvents(tmp_path, event_file).inspect()
    assert result["events_available"] is True
    assert result["events"][0]["event_type"] == "experiment_ended"


def test_unset_adapter_event_file_remains_unavailable(lifecycle_module, tmp_path):
    callback = lifecycle_module.OpenFLLifecycleCallback(
        role="aggregator",
        workspace_dir=tmp_path,
    )
    callback.on_experiment_begin()

    from server.services.openfl_events import OpenFLEvents

    result = OpenFLEvents(tmp_path).inspect()
    assert result["events_available"] is False
    assert result["events"] == []
