from __future__ import annotations

import time

from client.api.authentication import heartbeat


def periodic_heartbeat(client_id: str, round_id: int, interval_seconds: int = 10, stop_event=None):
    while stop_event is None or not stop_event.is_set():
        result = heartbeat(client_id=client_id, round_id=round_id, status="active")
        if not result.get("ok"):
            print(f"Heartbeat failed: {result.get('error')}")
        time.sleep(interval_seconds)


__all__ = ["periodic_heartbeat"]
