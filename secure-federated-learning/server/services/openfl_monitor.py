from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_COLLABORATOR_PATTERN = re.compile(r"^\s*-\s*([A-Za-z0-9_-]+)\s*$")
_ROUND_PATTERN = re.compile(r"^\s*rounds_to_train\s*:\s*(\d+)\s*$", re.MULTILINE)
_DATA_MAPPING_PATTERN = re.compile(r"^\s*([A-Za-z0-9_-]+)\s*,\s*(\S+)\s*$", re.MULTILINE)


class OpenFLMonitor:
    """Read-only inspection of explicitly configured OpenFL workspace artifacts."""

    _CHECKPOINTS = (
        ("best", Path("save/best.pbuf")),
        ("last", Path("save/last.pbuf")),
        ("init", Path("save/init.pbuf")),
    )

    def __init__(self, workspace_dir: Path | str) -> None:
        self.workspace_dir = Path(workspace_dir).expanduser().resolve()

    def inspect(self) -> dict[str, Any]:
        observed_at = datetime.now(timezone.utc).isoformat()
        base = {
            "integration_available": False,
            "workspace_available": False,
            "federation_status": "unknown",
            "configured_collaborators": [],
            "configured_rounds": None,
            "available_checkpoint_names": [],
            "experiment_database_available": False,
            "last_observed_at": observed_at,
            "limitations": [],
        }

        if not self.workspace_dir.is_dir():
            base["limitations"].append("OpenFL workspace is unavailable.")
            return base

        base["workspace_available"] = True
        base["integration_available"] = True
        limitations = base["limitations"]

        cols_text = self._read_text(Path("plan/cols.yaml"), limitations)
        plan_text = self._read_text(Path("plan/plan.yaml"), limitations)
        data_text = self._read_text(Path("plan/data.yaml"), limitations)

        collaborators = self._parse_collaborators(cols_text)
        if collaborators is None:
            limitations.append("Collaborator configuration is missing or malformed.")
        else:
            base["configured_collaborators"] = collaborators

        rounds = self._parse_rounds(plan_text)
        if rounds is None:
            limitations.append("Configured training rounds are missing or malformed.")
        else:
            base["configured_rounds"] = rounds

        if data_text is not None and collaborators is not None:
            configured_data = self._parse_data_mapping(data_text)
            missing_data = [name for name in collaborators if name not in configured_data]
            if missing_data:
                limitations.append("Dataset configuration is missing collaborators.")

        for name, relative_path in self._CHECKPOINTS:
            checkpoint = self._safe_child(relative_path)
            if checkpoint is not None and checkpoint.is_file():
                base["available_checkpoint_names"].append(name)

        database_path = self._safe_child(Path("local_state/tensor.db"))
        if database_path is not None and database_path.is_file():
            if self._database_is_readable(database_path):
                base["experiment_database_available"] = True
            else:
                limitations.append("OpenFL experiment database is unavailable or unreadable.")

        limitations.append(
            "Federation activity and result metrics are unknown; artifact presence does not prove a running or completed experiment."
        )
        return base

    def _safe_child(self, relative_path: Path) -> Path | None:
        candidate = (self.workspace_dir / relative_path).resolve()
        try:
            candidate.relative_to(self.workspace_dir)
        except ValueError:
            return None
        return candidate

    def _read_text(self, relative_path: Path, limitations: list[str]) -> str | None:
        path = self._safe_child(relative_path)
        if path is None:
            limitations.append("Configured OpenFL path is invalid.")
            return None
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            limitations.append(f"OpenFL configuration file {relative_path.as_posix()} is missing.")
        except (OSError, UnicodeError):
            limitations.append(f"OpenFL configuration file {relative_path.as_posix()} is unreadable.")
        return None

    @staticmethod
    def _parse_collaborators(text: str | None) -> list[str] | None:
        if text is None or "collaborators:" not in text:
            return None
        section = text.split("collaborators:", 1)[1]
        collaborators = []
        for line in section.splitlines():
            match = _COLLABORATOR_PATTERN.match(line)
            if match:
                collaborators.append(match.group(1))
            elif line.strip() and not line.startswith((" ", "\t")):
                break
        return collaborators or None

    @staticmethod
    def _parse_rounds(text: str | None) -> int | None:
        if text is None:
            return None
        match = _ROUND_PATTERN.search(text)
        return int(match.group(1)) if match else None

    @staticmethod
    def _parse_data_mapping(text: str) -> dict[str, str]:
        return {match.group(1): match.group(2) for match in _DATA_MAPPING_PATTERN.finditer(text)}

    @staticmethod
    def _database_is_readable(path: Path) -> bool:
        uri = f"file:{path.as_posix()}?mode=ro"
        try:
            with sqlite3.connect(uri, uri=True, timeout=1) as connection:
                connection.execute("PRAGMA query_only").fetchone()
                connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table' LIMIT 1"
                ).fetchone()
            return True
        except (sqlite3.Error, OSError):
            return False
