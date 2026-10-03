from __future__ import annotations

import ssl


def build_ssl_context(ca_file: str, cert_file: str, key_file: str) -> ssl.SSLContext:
    """Configure TLS 1.3 with mutual TLS verification for the server.

    IMPORTANT: TLS protects in-transit communication but not the confidentiality of a
    plaintext update once it is decrypted on the server. Secure aggregation is a
    separate layer.
    """
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.maximum_version = ssl.TLSVersion.TLSv1_3
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = False
    context.load_verify_locations(cafile=ca_file)
    context.load_cert_chain(certfile=cert_file, keyfile=key_file)
    context.set_ciphers("ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384")
    return context
