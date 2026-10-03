from __future__ import annotations

from pathlib import Path

from server.security.certificates import generate_dev_certificates


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parents[1]
    result = generate_dev_certificates(base_dir)
    print("Certificates generated successfully:")
    for key, value in result.items():
        print(f"{key}: {value}")
