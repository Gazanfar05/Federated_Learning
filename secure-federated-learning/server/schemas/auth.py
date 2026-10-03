from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ClientRegistration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id: str = Field(..., pattern=r"^hospital_\d{2}$")
    certificate_identity: str = Field(default="")


class ClientHeartbeat(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id: str = Field(..., pattern=r"^hospital_\d{2}$")
    certificate_identity: str = Field(default="")
    status: str = Field(default="CONNECTED")
