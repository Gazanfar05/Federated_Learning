from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server.security.certificates import generate_dev_certificates


if __name__ == "__main__":
    result = generate_dev_certificates(PROJECT_ROOT)
    print("Certificates generated successfully:")
    for key, value in result.items():
        print(f"{key}: {value}")
