from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ClientRecord:
    client_id: str
    certificate_identity: str = ""
    status: str = "REGISTERED"
    last_seen: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    current_round: int = 0
    submitted_updates: int = 0
    connection_status: str = "DISCONNECTED"
    metadata: dict[str, Any] = field(default_factory=dict)


class ClientRegistry:
    def __init__(self) -> None:
        self._clients: dict[str, ClientRecord] = {}

    def register(self, client_id: str, certificate_identity: str = "") -> ClientRecord:
        record = self._clients.get(client_id)
        if record is None:
            record = ClientRecord(client_id=client_id, certificate_identity=certificate_identity)
            self._clients[client_id] = record
        record.certificate_identity = certificate_identity or record.certificate_identity
        record.status = "REGISTERED"
        record.connection_status = "CONNECTED"
        record.last_seen = datetime.now(timezone.utc).isoformat()
        return record

    def update_heartbeat(self, client_id: str, status: str = "CONNECTED") -> ClientRecord | None:
        record = self._clients.get(client_id)
        if record is None:
            return None
        record.status = status
        record.connection_status = "CONNECTED" if status in {"CONNECTED", "TRAINING", "SUBMITTED"} else "DROPPED"
        record.last_seen = datetime.now(timezone.utc).isoformat()
        return record

    def get(self, client_id: str) -> ClientRecord | None:
        return self._clients.get(client_id)

    def list(self) -> list[ClientRecord]:
        return list(self._clients.values())

    def set_status(self, client_id: str, status: str) -> ClientRecord | None:
        record = self._clients.get(client_id)
        if record is None:
            return None
        record.status = status
        return record

    def mark_update(self, client_id: str) -> ClientRecord | None:
        record = self._clients.get(client_id)
        if record is None:
            return None
        record.submitted_updates += 1
        record.last_seen = datetime.now(timezone.utc).isoformat()
        return record
