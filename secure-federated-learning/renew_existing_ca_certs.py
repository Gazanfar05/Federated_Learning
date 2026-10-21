from datetime import datetime, timedelta, timezone
from ipaddress import ip_address
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

CERT_DIR = Path(__file__).resolve().parent / "certificates"
CA_CERT_PATH = CERT_DIR / "ca.crt"
CA_KEY_PATH = CERT_DIR / "ca.key"
SERVER_IP = "10.250.3.162"


def write_key(path, key):
    path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    path.chmod(0o600)


def issue_certificate(name, ca_cert, ca_key, server=False):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.now(timezone.utc)

    builder = (
        x509.CertificateBuilder()
        .subject_name(
            x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)])
        )
        .issuer_name(ca_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
    )

    if server:
        sans = [
            x509.DNSName("localhost"),
            x509.DNSName("server"),
            x509.IPAddress(ip_address("127.0.0.1")),
            x509.IPAddress(ip_address(SERVER_IP)),
        ]
        usages = [ExtendedKeyUsageOID.SERVER_AUTH]
    else:
        sans = [x509.DNSName(name)]
        usages = [ExtendedKeyUsageOID.CLIENT_AUTH]

    cert = (
        builder
        .add_extension(x509.SubjectAlternativeName(sans), critical=False)
        .add_extension(x509.ExtendedKeyUsage(usages), critical=False)
        .sign(ca_key, hashes.SHA256())
    )
    return cert, key


def main():
    if not CA_CERT_PATH.is_file() or not CA_KEY_PATH.is_file():
        raise SystemExit("ERROR: Existing CA certificate or key is missing.")

    ca_cert = x509.load_pem_x509_certificate(CA_CERT_PATH.read_bytes())
    ca_key = serialization.load_pem_private_key(CA_KEY_PATH.read_bytes(), password=None)

    if ca_cert.subject != ca_cert.issuer:
        raise SystemExit("ERROR: CA certificate is not self-signed.")

    if ca_cert.public_key().public_numbers() != ca_key.public_key().public_numbers():
        raise SystemExit("ERROR: CA certificate and private key do not match.")

    constraints = ca_cert.extensions.get_extension_for_class(x509.BasicConstraints).value
    if not constraints.ca:
        raise SystemExit("ERROR: Existing certificate is not a CA.")

    targets = [
        ("server", True),
        ("hospital_01", False),
        ("hospital_02", False),
        ("hospital_03", False),
    ]

    print("Existing CA verified. Its certificate and private key will not be changed.")
    print("The following existing leaf certificate/key pairs will be replaced:")
    for name, _ in targets:
        print(f"  certificates/{name}.crt and certificates/{name}.key")

    answer = input("Type RENEW to continue, or anything else to cancel: ")
    if answer != "RENEW":
        raise SystemExit("Cancelled; no certificates were changed.")

    for name, is_server in targets:
        cert, key = issue_certificate(name, ca_cert, ca_key, server=is_server)
        cert_path = CERT_DIR / f"{name}.crt"
        key_path = CERT_DIR / f"{name}.key"
        cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        cert_path.chmod(0o644)
        write_key(key_path, key)
        print(f"Created {cert_path.name} and {key_path.name}")

    print("Done. Existing ca.crt and ca.key were preserved.")


if __name__ == "__main__":
    main()
