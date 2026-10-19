"""Read-only OpenFL lifecycle event capture for the workspace.

Set ``OPENFL_EVENT_LOG_FILE=runtime/openfl-events.jsonl`` in the API
environment so ``GET /monitoring/openfl/events`` reads this source.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openfl.callbacks import Callback


_EVENT_TYPES = {
    "aggregator_started",
    "experiment_ended",
    "local_training_started",
    "task_completed",
    "round_started",
    "round_completed",
    "aggregator_stopped",
}
_MAX_MESSAGE_LENGTH = 200
_DEFAULT_EVENT_LOG = "runtime/openfl-events.jsonl"
_COLLABORATOR_PATTERN = re.compile(r"^hospital_\d{2}$")


class OpenFLLifecycleCallback(Callback):
    """Write verified OpenFL lifecycle callbacks as bounded JSONL records."""

    def __init__(
        self,
        role: str,
        collaborator_id: str | None = None,
        workspace_dir: str | Path | None = None,
        event_log_file: str | None = None,
    ) -> None:
        super().__init__()
        if role not in {"aggregator", "collaborator"}:
            raise ValueError("role must be 'aggregator' or 'collaborator'")
        if role == "collaborator" and (
            not isinstance(collaborator_id, str)
            or not _COLLABORATOR_PATTERN.fullmatch(collaborator_id)
        ):
            raise ValueError("collaborator_id is required for collaborator callbacks")

        self.role = role
        self.collaborator_id = collaborator_id
        self.workspace_dir = self._resolve_workspace(workspace_dir)
        self.event_log_path = self._resolve_event_log(event_log_file)

    def on_experiment_begin(self, logs: Any = None) -> None:
        if self.role == "aggregator":
            self._emit("aggregator_started", "OpenFL aggregator experiment started")

    def on_round_begin(self, round_num: int, logs: Any = None) -> None:
        self._emit_round("round_started", round_num, "OpenFL round started")

    def on_task_begin(self, task_name: str, round_num: int, logs: Any = None) -> None:
        if self.role == "collaborator":
            self._emit_round("local_training_started", round_num, "OpenFL collaborator task started")

    def on_task_end(self, task_name: str, round_num: int, logs: Any = None) -> None:
        if self.role == "collaborator":
            self._emit_round("task_completed", round_num, "OpenFL collaborator task completed")

    def on_round_end(self, round_num: int, logs: Any = None) -> None:
        self._emit_round("round_completed", round_num, "OpenFL round completed")

    def on_experiment_end(self, logs: Any = None) -> None:
        if self.role == "aggregator":
            self._emit("experiment_ended", "OpenFL aggregator experiment ended")

    def _emit_round(self, event_type: str, round_num: int, message: str) -> None:
        if not isinstance(round_num, int) or isinstance(round_num, bool) or round_num < 0:
            raise ValueError("round_num must be a nonnegative integer")
        self._emit(event_type, message, round_number=round_num)

    def _emit(
        self,
        event_type: str,
        message: str,
        *,
        round_number: int | None = None,
    ) -> None:
        if event_type not in _EVENT_TYPES:
            raise ValueError(f"Unsupported lifecycle event type: {event_type}")

        record: dict[str, Any] = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": message[:_MAX_MESSAGE_LENGTH],
        }
        if round_number is not None:
            record["round_number"] = round_number
        if self.collaborator_id is not None:
            record["collaborator_id"] = self.collaborator_id

        payload = (json.dumps(record, separators=(",", ":")) + "\n").encode("utf-8")
        try:
            self.event_log_path.parent.mkdir(parents=True, exist_ok=True)
            descriptor = os.open(
                self.event_log_path,
                os.O_WRONLY | os.O_APPEND | os.O_CREAT,
                0o600,
            )
            try:
                written = os.write(descriptor, payload)
                if written != len(payload):
                    raise OSError("short event-log write")
            finally:
                os.close(descriptor)
        except OSError as exc:
            raise RuntimeError("Unable to write the OpenFL lifecycle event log") from exc

    @staticmethod
    def _resolve_workspace(workspace_dir: str | Path | None) -> Path:
        configured = workspace_dir or os.getenv("OPENFL_WORKSPACE_DIR") or Path.cwd()
        return Path(configured).expanduser().resolve()

    def _resolve_event_log(self, event_log_file: str | None) -> Path:
        configured = event_log_file or os.getenv("OPENFL_EVENT_LOG_FILE") or _DEFAULT_EVENT_LOG
        candidate = Path(configured).expanduser()
        path = (self.workspace_dir / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
        try:
            path.relative_to(self.workspace_dir)
        except ValueError as exc:
            raise ValueError("OpenFL event log must remain inside the workspace") from exc
        return path
