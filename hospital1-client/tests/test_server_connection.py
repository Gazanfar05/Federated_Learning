from __future__ import annotations

from client.api.server_client import ServerClient


def test_server_client_init_uses_tls_config():
    client = ServerClient()
    assert client.session.verify.endswith('ca.crt')
    assert client.session.cert[0].endswith('hospital1.crt')
