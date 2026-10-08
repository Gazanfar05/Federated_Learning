from __future__ import annotations

import ssl
import time
from urllib.parse import urljoin

import requests

from client.communication.protocol import build_auth_payload
from client.config import CA_CERT, CLIENT_CERT, CLIENT_KEY, CLIENT_ID, SERVER_URL


def _verify_server_tls(base_url: str):
    cert = ssl.create_default_context(cafile=CA_CERT)
    cert.load_cert_chain(certfile=CLIENT_CERT, keyfile=CLIENT_KEY)
    return cert


def authenticate_client(server_url: str = SERVER_URL, client_id: str = CLIENT_ID):
    session = requests.Session()
    session.verify = CA_CERT
    session.cert = (CLIENT_CERT, CLIENT_KEY)
    payload = build_auth_payload(client_id=client_id, status=None)
    endpoint = urljoin(server_url.rstrip("/") + "/", "auth/register")
    try:
        response = session.post(endpoint, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        return {"ok": True, "response": data, "session": session}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "session": session}


def heartbeat(client_id: str = CLIENT_ID, round_id: int = 0, status: str = "connected"):
    session = requests.Session()
    session.verify = CA_CERT
    session.cert = (CLIENT_CERT, CLIENT_KEY)
    payload = build_auth_payload(client_id=client_id, round_id=round_id, status=status)
    endpoint = urljoin(SERVER_URL.rstrip("/") + "/", "auth/heartbeat")
    try:
        response = session.post(endpoint, json=payload, timeout=10)
        response.raise_for_status()
        return {"ok": True, "response": response.json()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


__all__ = ["authenticate_client", "heartbeat"]
