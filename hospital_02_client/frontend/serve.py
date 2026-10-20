#!/usr/bin/env python3
"""
Lightweight static server for Hospital 02 frontend.
Usage:
  python3 serve.py
  python3 serve.py --port 3002 --open
"""

from __future__ import annotations

import argparse
import os
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler


class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self.end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve Hospital 02 frontend")
    parser.add_argument("--port", type=int, default=3002)
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    server = HTTPServer((args.host, args.port), CORSRequestHandler)
    local_url = f"http://localhost:{args.port}"

    print("=" * 68)
    print(" HOSPITAL 02 - DATASET QUALITY AND EVALUATION PORTAL")
    print("=" * 68)
    print(f" Serving from: {os.getcwd()}")
    print(f" Local URL:    {local_url}")
    print(" Press Ctrl+C to stop")
    print("=" * 68)

    if args.open:
        webbrowser.open(local_url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down frontend server.")
        server.server_close()


if __name__ == "__main__":
    main()
