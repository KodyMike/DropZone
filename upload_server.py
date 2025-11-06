#!/usr/bin/env python3
"""
Write-only HTTP upload server.

- Accepts POST /upload with multipart/form-data.
- Saves uploaded files to TARGET_BASE_DIR (env) if set, otherwise to the script directory.
- JSON, XML, and CSV files are stored under <base>/data/ by default.
"""

import os
import re
import http.server
import socketserver
from datetime import datetime

PORT = int(os.environ.get("PORT", "9090"))
MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB limit
UPLOAD_SUBDIR = os.environ.get("UPLOAD_SUBDIR", "data")
TARGET_BASE_DIR = os.environ.get("TARGET_BASE_DIR")

class UploadOnlyHandler(http.server.BaseHTTPRequestHandler):
    server_version = "UploadOnlyServer/1.1"

    def do_POST(self):
        if self.path != "/upload":
            self._send_not_found()
            return

        try:
            content_type = self.headers.get("Content-Type")
            if not content_type or "multipart/form-data" not in content_type:
                self._send_error(400, "Expected multipart/form-data")
                return

            boundary = None
            if "boundary=" in content_type:
                boundary = content_type.split("boundary=")[1].split(";")[0]
            if not boundary:
                self._send_error(400, "No boundary in multipart data")
                return

            content_length_header = self.headers.get("Content-Length")
            if not content_length_header:
                self._send_error(411, "Content-Length required")
                return

            try:
                content_length = int(content_length_header)
            except ValueError:
                self._send_error(400, "Invalid Content-Length")
                return

            if MAX_UPLOAD_BYTES is not None and content_length > MAX_UPLOAD_BYTES:
                self._send_error(413, "Payload too large")
                self.rfile.read(content_length)  # drain body
                return

            body = self.rfile.read(content_length)
            parts = body.split(f"--{boundary}".encode())

            filename = None
            file_data = None
            for part in parts:
                if b"Content-Disposition" in part and b"filename=" in part:
                    match = re.search(b'filename="([^"]+)"', part)
                    if match and b"\r\n\r\n" in part:
                        filename = match.group(1).decode("utf-8", errors="ignore")
                        file_data = part.split(b"\r\n\r\n", 1)[1]
                        if file_data.endswith(b"\r\n"):
                            file_data = file_data[:-2]
                        break

            if not filename or file_data is None:
                self._send_error(400, "No file uploaded")
                return

            filename_clean = os.path.basename(filename)
            if not filename_clean:
                self._send_error(400, "Empty filename")
                return
            if os.sep in filename_clean or (os.altsep and os.altsep in filename_clean):
                self._send_error(400, "Invalid filename")
                return

            base_dir = os.path.abspath(TARGET_BASE_DIR) if TARGET_BASE_DIR else os.getcwd()
            if filename_clean.endswith((".json", ".xml", ".csv")):
                target_dir = os.path.join(base_dir, UPLOAD_SUBDIR)
            else:
                target_dir = base_dir

            os.makedirs(target_dir, exist_ok=True)
            filepath = os.path.join(target_dir, filename_clean)

            with open(filepath, "wb") as f:
                f.write(file_data)

            self.send_response(201)
            self.send_header("Content-Length", "0")
            self.send_header("Connection", "close")
            self.end_headers()

        except Exception as exc:
            self._send_error(500, "Upload failed")
            print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] upload error: {exc}")

    # Reject other verbs
    def do_GET(self): self._send_method_not_allowed()
    def do_HEAD(self): self._send_method_not_allowed()
    def do_PUT(self): self._send_method_not_allowed()
    def do_DELETE(self): self._send_method_not_allowed()
    def do_OPTIONS(self): self._send_method_not_allowed()
    def do_PATCH(self): self._send_method_not_allowed()
    def do_TRACE(self): self._send_method_not_allowed()
    def do_CONNECT(self): self._send_method_not_allowed()

    def log_message(self, format, *args):
        # comment out to silence base-class logging entirely
        super().log_message(format, *args)

    # Helper responses
    def _send_not_found(self):
        msg = b"Not found\n"
        self.send_response(404)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(msg)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(msg)

    def _send_method_not_allowed(self):
        msg = b"Method not allowed\n"
        self.send_response(405)
        self.send_header("Allow", "POST")
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(msg)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(msg)

    def _send_error(self, code, message):
        body = (str(message) + "\n").encode("utf-8", errors="ignore")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    base_dir = os.path.abspath(TARGET_BASE_DIR) if TARGET_BASE_DIR else script_dir
    json_dir = os.path.join(base_dir, UPLOAD_SUBDIR)

    print(f"Upload server listening on 0.0.0.0:{PORT}")
    print(f"POST files to /upload (JSON/XML/CSV stored under {json_dir})")

    with socketserver.TCPServer(("", PORT), UploadOnlyHandler) as httpd:
        httpd.serve_forever()
