from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin
import ssl
import time

import requests
from requests.adapters import HTTPAdapter

from .authentication import build_heartbeat_payload, build_registration_payload


class TLS13Adapter(HTTPAdapter):
    def __init__(self, ssl_context: ssl.SSLContext, *args: Any, **kwargs: Any) -> None:
        self.ssl_context = ssl_context
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, connections: int, maxsize: int, block: bool = False, **pool_kwargs: Any) -> None:
        pool_kwargs["ssl_context"] = self.ssl_context
        return super().init_poolmanager(connections, maxsize, block=block, **pool_kwargs)

    def proxy_manager_for(self, *args: Any, **kwargs: Any):
        kwargs["ssl_context"] = self.ssl_context
        return super().proxy_manager_for(*args, **kwargs)


class ClientError(RuntimeError):
    pass


class AuthenticationError(ClientError):
    pass


class InvalidRequestError(ClientError):
    pass


class ServerRejectedError(ClientError):
    pass


@dataclass
class APIResponse:
    ok: bool
    status_code: int | None = None
    data: dict[str, Any] | None = None
    error: str | None = None


class HospitalAPI:
    def __init__(self, server_url: str, client_id: str, certificate_identity: str, ca_cert: str, client_cert: str, client_key: str, timeout_seconds: int, max_retries: int, backoff_seconds: float) -> None:
        self.server_url = server_url.rstrip("/") + "/"
        self.client_id = client_id
        self.certificate_identity = certificate_identity
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.verify = ca_cert
        self.session.cert = (client_cert, client_key)
        context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=ca_cert)
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        context.maximum_version = ssl.TLSVersion.TLSv1_3
        self.session.mount("https://", TLS13Adapter(context))

    def _request(self, method: str, path: str, *, params: dict[str, Any] | None = None, json_payload: dict[str, Any] | None = None, expected_status: tuple[int, ...] = (200,)) -> APIResponse:
        url = urljoin(self.server_url, path.lstrip("/"))
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(method, url, params=params, json=json_payload, timeout=self.timeout_seconds)
                if response.status_code in expected_status:
                    try:
                        return APIResponse(True, response.status_code, response.json(), None)
                    except Exception:
                        return APIResponse(True, response.status_code, {"text": response.text}, None)
                if response.status_code in (401, 403):
                    raise AuthenticationError(response.text)
                if response.status_code == 422:
                    raise InvalidRequestError(response.text)
                raise ServerRejectedError(f"HTTP {response.status_code}: {response.text}")
            except (AuthenticationError, InvalidRequestError, ServerRejectedError):
                raise
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(self.backoff_seconds * (2**attempt))
        return APIResponse(False, error=str(last_error) if last_error else "Unknown request failure")

    def health(self) -> APIResponse:
        return self._request("GET", "/health")

    def register(self) -> APIResponse:
        return self._request("POST", "/auth/register", json_payload=build_registration_payload(self.client_id, self.certificate_identity))

    def heartbeat(self, status: str) -> APIResponse:
        return self._request("POST", "/auth/heartbeat", json_payload=build_heartbeat_payload(self.client_id, self.certificate_identity, status))

    def join_round(self, round_id: int) -> APIResponse:
        return self._request("POST", "/training/join", json_payload={"client_id": self.client_id, "round_id": round_id})

    def fetch_model_metadata(self) -> APIResponse:
        return self._request("GET", "/training/model", params={"client_id": self.client_id})

    def submit_update(self, payload: dict[str, Any]) -> APIResponse:
        return self._request("POST", "/training/update", json_payload=payload)

    def complete_round(self, round_id: int) -> APIResponse:
        return self._request("POST", "/training/complete", json_payload={"client_id": self.client_id, "round_id": round_id})

    def training_status(self) -> APIResponse:
        return self._request("GET", "/training/status")
