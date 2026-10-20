from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


_COLLABORATOR_PATTERN = re.compile(r"^hospital_\d{2}$")
_EVENT_TYPES = {
    "aggregator_started",
    "collaborator_connected",
    "experiment_ended",
    "local_training_started",
    "round_started",
    "task_completed",
    "round_completed",
    "aggregator_stopped",
}
_MAX_MESSAGE_LENGTH = 500


class OpenFLEvents:
    """Read verified, structured OpenFL events from one explicitly configured JSONL file."""

    def __init__(self, workspace_dir: Path | str, event_log_file: str = "") -> None:
        self.workspace_dir = Path(workspace_dir).expanduser().resolve()
        self.event_log_file = event_log_file

    def inspect(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "events_available": False,
            "source_description": "No structured OpenFL event source configured.",
            "events": [],
            "limitations": [],
        }
        path = self._configured_path()
        if path is None:
            result["limitations"].append(
                "OpenFL 1.9 logging is disabled in the current plan and no event log file is configured."
            )
            return result
        if not path.is_file():
            result["source_description"] = "Configured OpenFL event source is unavailable."
            result["limitations"].append("Configured OpenFL event log is missing or unavailable.")
            return result

        result["source_description"] = "Configured structured OpenFL JSONL event log, read-only."
        events: list[dict[str, Any]] = []
        try:
            with path.open(encoding="utf-8") as event_file:
                for line_number, line in enumerate(event_file, start=1):
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        result["limitations"].append(f"Malformed event record at line {line_number}.")
                        continue
                    event = self._normalize_event(record)
                    if event is None:
                        result["limitations"].append(f"Incomplete event record at line {line_number}.")
                        continue
                    events.append(event)
        except (OSError, UnicodeError):
            result["limitations"].append("Configured OpenFL event log is unreadable.")
            return result

        result["events"] = events
        result["events_available"] = bool(events)
        if not events:
            result["limitations"].append("No verifiable structured OpenFL events were found.")
        return result

    def _configured_path(self) -> Path | None:
        if not self.event_log_file:
            return None
        configured = Path(self.event_log_file).expanduser()
        path = (self.workspace_dir / configured).resolve() if not configured.is_absolute() else configured.resolve()
        try:
            path.relative_to(self.workspace_dir)
        except ValueError:
            return None
        return path

    @staticmethod
    def _normalize_event(record: Any) -> dict[str, Any] | None:
        if not isinstance(record, dict):
            return None
        event_type = record.get("event_type")
        if not isinstance(event_type, str) or not event_type:
            return None

        event: dict[str, Any] = {
            "event_type": event_type if event_type in _EVENT_TYPES else "unknown",
        }
        timestamp = record.get("timestamp")
        if timestamp is not None:
            if not isinstance(timestamp, str):
                return None
            try:
                datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                return None
            event["timestamp"] = timestamp

        collaborator_id = record.get("collaborator_id")
        if collaborator_id is not None:
            if not isinstance(collaborator_id, str) or not _COLLABORATOR_PATTERN.fullmatch(collaborator_id):
                return None
            event["collaborator_id"] = collaborator_id

        round_number = record.get("round_number")
        if round_number is not None:
            if not isinstance(round_number, int) or round_number < 0:
                return None
            event["round_number"] = round_number

        message = record.get("message")
        if message is not None:
            if not isinstance(message, str):
                return None
            event["message"] = message[:_MAX_MESSAGE_LENGTH]
        return event
