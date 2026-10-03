from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AnomalyResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id: str
    round_id: int
    anomaly_score: float
    threshold: float
    decision: str
    reason: str


class PrivacyMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    epsilon: float
    delta: float
    noise_multiplier: float
    clipping_norm: float
    rounds: int


class ServerMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    round_id: int
    client_count: int
    total_samples: int
    model_version: int
    loss: float | None = None
    accuracy: float | None = None
    f1_score: float | None = None


class ClientStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id: str
    certificate_identity: str
    status: str
    last_seen: str
    current_round: int
    submitted_updates: int
    connection_status: str
