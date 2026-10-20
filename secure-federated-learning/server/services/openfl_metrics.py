from __future__ import annotations

import math
import sqlite3
from pathlib import Path
from typing import Any


class OpenFLMetrics:
    """Read-only access to verified scalar metrics persisted by OpenFL."""

    def __init__(self, workspace_dir: Path | str) -> None:
        self.workspace_dir = Path(workspace_dir).expanduser().resolve()

    def inspect(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "metrics_available": False,
            "experiment_identity": None,
            "metric_name": None,
            "metric_description": None,
            "metric_semantics_verified": False,
            "source_description": (
                "OpenFL 1.9 PersistentTensorDB key_value_store, read-only"
            ),
            "round_results": [],
            "best_observed_result": None,
            "limitations": [],
        }

        database = (self.workspace_dir / "local_state" / "tensor.db").resolve()
        try:
            database.relative_to(self.workspace_dir)
        except ValueError:
            result["limitations"].append("OpenFL database path is invalid.")
            return result

        if not self.workspace_dir.is_dir():
            result["limitations"].append("OpenFL workspace is unavailable.")
            return result
        if not database.is_file():
            result["limitations"].append("OpenFL experiment database is missing.")
            return result

        values = self._read_scalar_values(database, result["limitations"])
        if values is None:
            return result

        round_number = values.get("round_number")
        best_score = values.get("best_score")
        if round_number is None or best_score is None:
            result["limitations"].append(
                "The database does not contain both round_number and best_score."
            )
            return result
        if not self._is_integral_nonnegative(round_number):
            result["limitations"].append("Persisted round_number is invalid.")
            return result
        if not math.isfinite(best_score):
            result["limitations"].append("Persisted best_score is not finite.")
            return result

        result.update(
            {
                "metrics_available": True,
                "metric_name": "accuracy",
                "metric_description": (
                    "Best-so-far weighted aggregated validation accuracy "
                    "from the global validation task."
                ),
                "metric_semantics_verified": True,
                "best_observed_result": {
                    "value": best_score,
                    "round": None,
                },
            }
        )
        result["limitations"].extend(
            [
                "OpenFL persists only the current round and best_score here; "
                "historical per-round metric values are unavailable.",
                "The persisted best_score does not record the round in which "
                "the best value was first observed.",
            ]
        )
        return result

    @staticmethod
    def _is_integral_nonnegative(value: float) -> bool:
        return value >= 0 and value.is_integer()

    @staticmethod
    def _read_scalar_values(
        database: Path, limitations: list[str]
    ) -> dict[str, float] | None:
        uri = f"file:{database.as_posix()}?mode=ro"
        try:
            with sqlite3.connect(uri, uri=True, timeout=1) as connection:
                rows = connection.execute(
                    "SELECT key, value FROM key_value_store "
                    "WHERE key IN ('round_number', 'best_score')"
                ).fetchall()
        except (sqlite3.Error, OSError):
            limitations.append("OpenFL metric database is unavailable or unreadable.")
            return None

        values: dict[str, float] = {}
        for key, value in rows:
            if isinstance(value, (int, float)):
                values[key] = float(value)
        return values
