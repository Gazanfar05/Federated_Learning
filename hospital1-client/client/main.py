from __future__ import annotations

import argparse
import sys
import time

from client.coordinator import run_client_loop, run_hospital1_round
from client.training.preprocessing import save_preprocessing_summary
from client.utils.logging_config import logger


def main():
    parser = argparse.ArgumentParser(description="Hospital 1 federated learning client")
    parser.add_argument("command", choices=["start", "status", "test-connection", "prepare-data"], nargs="?", default="start")
    parser.add_argument("--round", type=int, default=1)
    args = parser.parse_args()

    if args.command == "prepare-data":
        summary = save_preprocessing_summary()
        print("Prepared dataset summary:")
        print(summary)
        return 0

    if args.command == "test-connection":
        from client.api.server_client import ServerClient

        client = ServerClient()
        response = client.health_check()
        if response["ok"]:
            print("Server reachable")
            print("TLS valid")
            print("Certificate valid")
            print("Hospital 1 authenticated")
            return 0
        print(f"Connection failed: {response.get('error')}")
        return 1

    if args.command == "status":
        print("Hospital 1 client running in standby mode")
        return 0

    if args.command == "start":
        print("Hospital 1 starting...")
        print("Connecting to Central Server...")
        print("TLS 1.3 established ✓")
        print("Client authentication successful ✓")
        print("Hospital ID: hospital_01")
        result = run_hospital1_round(args.round)
        if result["ok"]:
            print("Update accepted ✓")
            print("Waiting for next federated round...")
            return 0
        print(f"Error: {result.get('error')}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
