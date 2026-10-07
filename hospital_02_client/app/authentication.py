from __future__ import annotations


def build_registration_payload(client_id: str, certificate_identity: str) -> dict[str, str]:
    return {"client_id": client_id, "certificate_identity": certificate_identity}


def build_heartbeat_payload(client_id: str, certificate_identity: str, status: str) -> dict[str, str]:
    return {"client_id": client_id, "certificate_identity": certificate_identity, "status": status}
