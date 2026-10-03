from __future__ import annotations

import json
import time
from urllib.parse import urljoin

import requests

from client.config import CA_CERT, CLIENT_CERT, CLIENT_ID, CLIENT_KEY, SERVER_URL
from client.security.validation import ensure_no_patient_data


class ServerClient:
    def __init__(self, server_url: str = SERVER_URL, client_id: str = CLIENT_ID):
        self.server_url = server_url.rstrip("/") + "/"
        self.client_id = client_id
        self.session = requests.Session()
        self.session.verify = CA_CERT
        self.session.cert = (CLIENT_CERT, CLIENT_KEY)

    def health_check(self):
        try:
            resp = self.session.get(urljoin(self.server_url, "health"), timeout=10)
            resp.raise_for_status()
            return {"ok": True, "data": resp.json()}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def join_round(self, round_id: int | str):
        payload = {"client_id": self.client_id, "round_id": round_id, "status": "joined"}
        try:
            resp = self.session.post(urljoin(self.server_url, "training/join"), json=payload, timeout=15)
            resp.raise_for_status()
            return {"ok": True, "data": resp.json()}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def fetch_model(self, model_version: int | str = 0):
        try:
            resp = self.session.get(urljoin(self.server_url, f"training/model?model_version={model_version}"), timeout=15)
            resp.raise_for_status()
            return {"ok": True, "data": resp.json()}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def submit_update(self, payload: dict):
        if not ensure_no_patient_data(payload):
            raise ValueError("Patient data detected in outbound update payload")
        try:
            resp = self.session.post(urljoin(self.server_url, "training/update"), json=payload, timeout=20)
            resp.raise_for_status()
            return {"ok": True, "data": resp.json()}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def complete_round(self, payload: dict):
        try:
            resp = self.session.post(urljoin(self.server_url, "training/complete"), json=payload, timeout=20)
            resp.raise_for_status()
            return {"ok": True, "data": resp.json()}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def status(self):
        try:
            resp = self.session.get(urljoin(self.server_url, "training/status"), timeout=10)
            resp.raise_for_status()
            return {"ok": True, "data": resp.json()}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}


__all__ = ["ServerClient"]
