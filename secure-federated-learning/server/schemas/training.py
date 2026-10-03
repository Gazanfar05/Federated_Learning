from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TrainingJoinRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id: str = Field(..., pattern=r"^hospital_\d{2}$")
    round_id: int = Field(..., ge=1)


class ModelUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    client_id: str = Field(..., pattern=r"^hospital_\d{2}$")
    round_id: int = Field(..., ge=1)
    model_version: int = Field(..., ge=1)
    num_samples: int = Field(..., ge=1)
    update_hash: str = Field(..., min_length=10)
    protected_update: list[float] = Field(..., min_length=1)
    timestamp: datetime


class TrainingCompleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id: str = Field(..., pattern=r"^hospital_\d{2}$")
    round_id: int = Field(..., ge=1)
