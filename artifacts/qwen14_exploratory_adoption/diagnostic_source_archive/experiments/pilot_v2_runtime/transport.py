"""Fixed loopback HTTP transport. No redirects, proxies, tools or sample execution."""

from __future__ import annotations

import http.client
import base64
import json
import socket

MODEL = "qwen3.5:4b-q4_K_M"
ALLOWED = {"version", "tags", "ps", "show", "pull", "chat"}


class LocalOllama:
    def __init__(self, timeout=300):
        self.timeout = timeout
        self.connection = None

    def cancel(self):
        connection = self.connection
        if connection and connection.sock:
            try:
                connection.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

    def request(self, endpoint, payload=None):
        if endpoint not in ALLOWED:
            raise ValueError("Only the fixed local experiment endpoints are permitted")
        if payload is not None and payload.get("model", MODEL) != MODEL:
            raise ValueError("Only the authorized model is permitted")
        connection = http.client.HTTPConnection("127.0.0.1", 11434, timeout=self.timeout)
        self.connection = connection
        try:
            body = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
            connection.request("POST" if body is not None else "GET", "/api/" + endpoint,
                               body=body, headers={"Content-Type": "application/json"})
            response = connection.getresponse()
            raw = response.read()
            try:
                raw.decode("utf-8")
                utf8_valid = True
            except UnicodeDecodeError:
                utf8_valid = False
            return {"status": response.status, "raw": raw.decode("utf-8", errors="replace"),
                    "raw_utf8_valid": utf8_valid, "raw_bytes_base64": base64.b64encode(raw).decode("ascii")}
        finally:
            connection.close()
            self.connection = None

    def json(self, endpoint, payload=None):
        response = self.request(endpoint, payload)
        value = json.loads(response["raw"])
        if response["status"] != 200 or "error" in value:
            raise RuntimeError(f"Ollama {endpoint}: {response['status']} {value}")
        return value
