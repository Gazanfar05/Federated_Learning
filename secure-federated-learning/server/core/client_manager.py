from __future__ import annotations

from server.security.authentication import ClientAuthenticator
from server.storage.client_registry import ClientRegistry, ClientRecord


class ClientManager:
    def __init__(self, trusted_clients: tuple[str, ...] | None = None) -> None:
        self.registry = ClientRegistry()
        self.authenticator = ClientAuthenticator(trusted_clients or ("hospital_01", "hospital_02", "hospital_03"))

    def register_client(self, client_id: str, certificate_identity: str = "") -> bool:
        if not self.authenticator.validate_client_id(client_id):
            return False
        self.registry.register(client_id, certificate_identity)
        return True

    def heartbeat(self, client_id: str, certificate_identity: str = "") -> ClientRecord | None:
        if not self.authenticator.validate_client_id(client_id):
            return None
        if not self.authenticator.validate_certificate_identity(client_id, certificate_identity):
            return None
        return self.registry.update_heartbeat(client_id, "CONNECTED")

    def get_client(self, client_id: str) -> ClientRecord | None:
        return self.registry.get(client_id)

    def list_clients(self) -> list[ClientRecord]:
        return self.registry.list()
