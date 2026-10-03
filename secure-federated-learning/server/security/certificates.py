from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def _generate_private_key(key_size: int = 2048) -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=key_size)


def _build_cert(subject_name: str, issuer_cert: x509.Certificate | None = None, issuer_key: rsa.RSAPrivateKey | None = None, is_ca: bool = False, san_dns: list[str] | None = None, san_ip: list[str] | None = None) -> tuple[x509.Certificate, rsa.RSAPrivateKey]:
    key = _generate_private_key()
    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, subject_name),
    ])
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject if issuer_cert is None else issuer_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc) - timedelta(days=1))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
    )
    if is_ca:
        builder = builder.add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        builder = builder.add_extension(x509.KeyUsage(digital_signature=True, key_encipherment=True, content_commitment=False, data_encipherment=False, key_agreement=False, key_cert_sign=True, crl_sign=True, encipher_only=False, decipher_only=False), critical=True)
    else:
        builder = builder.add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        builder = builder.add_extension(x509.KeyUsage(digital_signature=True, key_encipherment=True, content_commitment=False, data_encipherment=False, key_agreement=False, key_cert_sign=False, crl_sign=False, encipher_only=False, decipher_only=False), critical=True)
        builder = builder.add_extension(x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH, x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH]), critical=False)
        alt_names = []
        for dns_name in san_dns or []:
            alt_names.append(x509.DNSName(dns_name))
        for ip_name in san_ip or []:
            alt_names.append(x509.IPAddress(ip_name))
        if alt_names:
            builder = builder.add_extension(x509.SubjectAlternativeName(alt_names), critical=False)
    cert = builder.sign(issuer_key or key, hashes.SHA256())
    return cert, key


def generate_dev_certificates(base_dir: str | Path) -> dict[str, str]:
    """Generate CA, server certificate, and three hospital certs for local demos."""
    base = Path(base_dir)
    cert_dir = base / "certificates"
    cert_dir.mkdir(parents=True, exist_ok=True)

    ca_cert, ca_key = _build_cert("SecureFL-CA", is_ca=True)
    ca_cert_path = cert_dir / "ca.crt"
    ca_key_path = cert_dir / "ca.key"
    ca_cert_path.write_bytes(ca_cert.public_bytes(serialization.Encoding.PEM))
    ca_key_path.write_bytes(ca_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ))

    server_cert, server_key = _build_cert("server", issuer_cert=ca_cert, issuer_key=ca_key, san_dns=["localhost", "server"], san_ip=["127.0.0.1"])
    (cert_dir / "server.crt").write_bytes(server_cert.public_bytes(serialization.Encoding.PEM))
    (cert_dir / "server.key").write_bytes(server_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ))

    names = ["hospital_01", "hospital_02", "hospital_03"]
    for name in names:
        cert, key = _build_cert(name, issuer_cert=ca_cert, issuer_key=ca_key, san_dns=["localhost", name])
        (cert_dir / f"{name}.crt").write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        (cert_dir / f"{name}.key").write_bytes(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    return {
        "ca_cert": str(ca_cert_path),
        "server_cert": str(cert_dir / "server.crt"),
        "server_key": str(cert_dir / "server.key"),
    }
