from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ModelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    client_id: str = Field(..., pattern=r"^hospital_\d{2}$")
    round_id: int = Field(..., ge=1)


class ModelResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    client_id: str
    model_version: int
    round_id: int
    architecture: str
    parameter_count: int
    update_hash: str


class AggregationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    round_id: int
    client_count: int
    total_samples: int
    global_model_version: int
    aggregation_time_ms: float
    accepted_clients: list[str]
