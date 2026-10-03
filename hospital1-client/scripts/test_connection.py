from __future__ import annotations

from client.api.server_client import ServerClient


if __name__ == "__main__":
    client = ServerClient()
    health = client.health_check()
    if health["ok"]:
        print("Server reachable")
        print("TLS valid")
        print("Certificate valid")
        print("Hospital 1 authenticated")
    else:
        print(f"Connection failed: {health.get('error')}")
