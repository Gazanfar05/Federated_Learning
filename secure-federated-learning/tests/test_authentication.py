from __future__ import annotations

from server.security.authentication import create_authenticator


def test_valid_vs_invalid_client_identity():
    authenticator = create_authenticator()
    assert authenticator.validate_client_id("hospital_01")
    assert not authenticator.validate_client_id("hospital_99")
    assert authenticator.validate_certificate_identity("hospital_01", "hospital_01")
    assert not authenticator.validate_certificate_identity("hospital_01", "unknown")
