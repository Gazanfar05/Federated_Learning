from __future__ import annotations

import argparse
import json
from dataclasses import replace

from app.client import Hospital3Client


def main() -> int:
    parser = argparse.ArgumentParser(description="Hospital 3 federated learning client")
    parser.add_argument("--check", action="store_true", help="Validate configuration and dataset")
    parser.add_argument("--health", action="store_true", help="Check server health over TLS")
    parser.add_argument("--train", action="store_true", help="Run local training only")
    parser.add_argument("--resume", action="store_true", help="Resume from the latest checkpoint and continue polling")
    parser.add_argument("--round", type=int, default=None, help="Manually participate in a specific round")
    parser.add_argument("--dev-mode", action="store_true", help="Local-only development mode")
    args = parser.parse_args()

    client = Hospital3Client()
    if args.dev_mode:
        client.config = replace(client.config, dev_mode=True)

    if args.check:
        errors = client.validate()
        print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
        return 0 if not errors else 1

    if args.health:
        print(json.dumps(client.check_server_health(), indent=2, default=str))
        return 0

    if args.train:
        client.load_data()
        print(json.dumps(client.local_train_only(), indent=2, default=str))
        return 0

    if args.resume:
        client.restore_latest_checkpoint()
        client.run_forever()
        return 0

    if args.round is not None:
        result = client.participate_in_round(args.round)
        print(json.dumps(result, indent=2, default=str))
        return 0

    client.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
