from __future__ import annotations

from typing import Iterable


DEFAULT_CLIENT_IDS = ("hospital_01", "hospital_02", "hospital_03")


class ClientAuthenticator:
    """Simple identity validator for the classroom federated system.

    In production we would verify X.509 certificate subjects and mTLS identities
    from the TLS stack. This implementation keeps the logic deterministic and easy
    for the hospital clients to implement while still rejecting unknown devices.
    """

    def __init__(self, trusted_clients: Iterable[str] | None = None) -> None:
        self.trusted_clients = set(trusted_clients or DEFAULT_CLIENT_IDS)

    def validate_client_id(self, client_id: str) -> bool:
        return client_id in self.trusted_clients

    def validate_certificate_identity(self, client_id: str, certificate_identity: str | None) -> bool:
        if not self.validate_client_id(client_id):
            return False
        if certificate_identity is None:
            return False
        return certificate_identity == client_id or certificate_identity.endswith(client_id)


def create_authenticator() -> ClientAuthenticator:
    return ClientAuthenticator(DEFAULT_CLIENT_IDS)
