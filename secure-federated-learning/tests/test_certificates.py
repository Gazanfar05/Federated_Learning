from pathlib import Path

from server.security.certificates import generate_dev_certificates


def test_generate_dev_certificates_creates_tls_files(tmp_path: Path) -> None:
    result = generate_dev_certificates(tmp_path)

    assert tmp_path.joinpath("certificates", "ca.crt").exists()
    assert tmp_path.joinpath("certificates", "server.crt").exists()
    assert tmp_path.joinpath("certificates", "server.key").exists()
    assert tmp_path.joinpath("certificates", "hospital_01.crt").exists()
    assert tmp_path.joinpath("certificates", "hospital_02.crt").exists()
    assert tmp_path.joinpath("certificates", "hospital_03.crt").exists()
    assert "ca_cert" in result
    assert "server_cert" in result
