#!/usr/bin/env python3
"""
Zero-Dependency Python HTTP Server with CORS support for Secure Federated Learning Command Center.
Usage:
    python3 serve.py
    python3 serve.py --port 3000
    python3 serve.py --open
"""

import sys
import os
import argparse
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for local testing with FastAPI backend
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def main():
    parser = argparse.ArgumentParser(description="Serve the Secure Federated Learning Frontend Dashboard")
    parser.add_argument("--port", type=int, default=3000, help="Port to bind server (default: 3000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface to bind (default: 0.0.0.0)")
    parser.add_argument("--open", action="store_true", help="Automatically open default browser")
    args = parser.parse_args()

    # Change directory to this script's directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    server_address = (args.host, args.port)
    httpd = HTTPServer(server_address, CORSRequestHandler)

    url = f"http://localhost:{args.port}"
    print("=" * 65)
    print(" SECURE FEDERATED LEARNING IN HEALTHCARE — FRONTEND COMMAND CENTER")
    print("=" * 65)
    print(f" Serving dashboard from: {os.getcwd()}")
    print(f" Local URL:              {url}")
    print(f" Network LAN URL:        http://{args.host}:{args.port}")
    print(" Press Ctrl+C to terminate the dashboard server.")
    print("=" * 65)

    if args.open:
        webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down dashboard server gracefully. Goodbye!")
        httpd.server_close()

if __name__ == "__main__":
    main()
