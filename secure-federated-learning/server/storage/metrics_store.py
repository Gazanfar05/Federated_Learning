from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MetricRecord:
    round_id: int
    loss: float | None = None
    accuracy: float | None = None
    f1_score: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class MetricsStore:
    def __init__(self) -> None:
        self._metrics: dict[int, MetricRecord] = {}

    def set(self, round_id: int, **kwargs: Any) -> MetricRecord:
        record = self._metrics.get(round_id)
        if record is None:
            record = MetricRecord(round_id=round_id)
            self._metrics[round_id] = record
        for key, value in kwargs.items():
            setattr(record, key, value)
        return record

    def get(self, round_id: int) -> MetricRecord | None:
        return self._metrics.get(round_id)

    def latest(self) -> MetricRecord | None:
        if not self._metrics:
            return None
        return self._metrics[max(self._metrics)]
