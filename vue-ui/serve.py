#!/usr/bin/env python3
"""
serve.py — Pure Python static file server + API proxy for Qwen3-TTS Vue UI.
Works correctly over TailScale (unlike Node.js on macOS utun).

Usage: python3 serve.py
"""
import http.server
import socketserver
import urllib.request
import urllib.error
import os
import json
from pathlib import Path

PORT = 5174
DIST_DIR = Path(__file__).parent / "dist"
API_BASE = "http://127.0.0.1:8765"  # Backend on localhost

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js":   "application/javascript",
    ".css":  "text/css",
    ".json": "application/json",
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg":  "image/svg+xml",
    ".ico":  "image/x-icon",
    ".woff2":"font/woff2",
    ".woff": "font/woff",
    ".mp3":  "audio/mpeg",
    ".wav":  "audio/wav",
    ".ogg":  "audio/ogg",
}

API_PATHS = ("/generate", "/models", "/health", "/download", "/api/")


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    """Static file handler that knows our DIST_DIR."""

    def __init__(self, *args, **kwargs):
        # Pass directory explicitly to parent
        super().__init__(*args, directory=str(DIST_DIR), **kwargs)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_GET(self):
        if self.path.startswith(API_PATHS):
            self.proxy()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith(API_PATHS):
            self.proxy()
        else:
            self.send_error(404, "Not Found")

    def proxy(self):
        """Proxy request to backend and return response."""
        target = API_BASE + self.path
        headers = {k: v for k, v in self.headers.items()
                   if k.lower() not in ("host", "connection")}

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else None

            req = urllib.request.Request(
                target,
                data=body,
                headers=headers,
                method=self.command,
            )

            with urllib.request.urlopen(req, timeout=300) as resp:
                response_body = resp.read()
                response_headers = dict(resp.headers)

                self.send_response(resp.status)
                for k, v in response_headers.items():
                    if k.lower() not in ("transfer-encoding", "connection"):
                        self.send_header(k, v)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                if response_body:
                    self.wfile.write(response_body)

        except urllib.error.HTTPError as e:
            body = e.read() if e.fp else b""
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            if body:
                self.wfile.write(body)
        except Exception as ex:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(ex)}).encode())

    def guess_type(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext in MIME_TYPES:
            return MIME_TYPES[ext]
        return super().guess_type(path)

    def log_message(self, format, *args):
        print(f"[serve.py] {args[0]}")


class ReuseAddrTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    print(f"Serving {DIST_DIR} on http://0.0.0.0:{PORT}")
    print(f"API proxy → {API_BASE}")
    with ReuseAddrTCPServer(("0.0.0.0", PORT), QuietHandler) as httpd:
        httpd.serve_forever()
