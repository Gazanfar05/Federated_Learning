from __future__ import annotations

from app.config import load_config
from app.networking import HospitalAPI


def test_certificate_configuration_and_tls_version():
    config = load_config()
    assert config.client_id == "hospital_02"
    assert config.client_cert.name == "hospital2.crt"
    assert config.client_key.name == "hospital2.key"
    assert config.ca_cert.name == "ca.crt"

    api = HospitalAPI(
        server_url=config.server_url,
        client_id=config.client_id,
        certificate_identity=config.client_id,
        ca_cert=str(config.ca_cert),
        client_cert=str(config.client_cert),
        client_key=str(config.client_key),
        timeout_seconds=config.request_timeout,
        max_retries=config.max_retries,
        backoff_seconds=config.retry_backoff_seconds,
    )
    adapter = api.session.get_adapter("https://")
    assert adapter.ssl_context.minimum_version.name == "TLSv1_3"
