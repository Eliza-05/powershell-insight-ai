"""DNS/TCP/TLS checks only: no HTTP, API client, credentials on wire or ledger writes."""
from __future__ import annotations

from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import socket
import ssl
import sys
import time
from urllib.request import getproxies

import certifi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
HOST = "generativelanguage.googleapis.com"
OUT = ROOT / "artifacts/gemini_transport_diagnostic"


def category(exc):
    if isinstance(exc, socket.gaierror):
        return "dns_failure"
    if isinstance(exc, ssl.SSLCertVerificationError):
        return "tls_certificate_validation_failure"
    if isinstance(exc, ssl.SSLError):
        return "tls_handshake_failure"
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return "timeout"
    if isinstance(exc, ConnectionRefusedError):
        return "connection_refused"
    if isinstance(exc, PermissionError):
        return "network_access_denied"
    return "network_error"


def measure(action):
    start = time.monotonic()
    try:
        data = action()
        return {"status": "ok", "seconds": round(time.monotonic()-start, 3), **data}
    except Exception as exc:
        return {"status": "failed", "category": category(exc), "seconds": round(time.monotonic()-start, 3)}


def tcp():
    with socket.create_connection((HOST, 443), timeout=8):
        return {"port": 443}


def tls(context):
    assert context.check_hostname and context.verify_mode == ssl.CERT_REQUIRED
    with socket.create_connection((HOST, 443), timeout=8) as raw:
        with context.wrap_socket(raw, server_hostname=HOST) as secured:
            # Handshake only. No HTTP request, application data, key or Authorization headers.
            return {"protocol": secured.version(), "hostname_verified": True, "certificate_verified": True}


def proxy_state():
    names = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY", "SSL_CERT_FILE", "SSL_CERT_DIR")
    state = {"environment_variables_present": {n: bool(os.environ.get(n) or os.environ.get(n.lower())) for n in names}}
    try:
        proxies = getproxies()
        state["python_discovered_proxy_schemes"] = sorted(k for k in proxies if k in {"http", "https", "all", "no"})
    except Exception:
        state["python_discovery_failed"] = True
    if os.name == "nt":
        import winreg
        for label, hive, path in [("wininet_current_user", winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings")]:
            try:
                with winreg.OpenKey(hive, path) as registry:
                    values = {}
                    for name in ("ProxyEnable", "ProxyServer", "AutoConfigURL"):
                        try:
                            values[name + "_configured"] = bool(winreg.QueryValueEx(registry, name)[0])
                        except FileNotFoundError:
                            values[name + "_configured"] = False
                    state[label] = values
            except OSError:
                state[label] = {"inspection": "unavailable"}
    return state


def main():
    from app.services.llm.gemini_credentials import read_api_key
    ledger = ROOT / "artifacts/gemini_viability/requests.jsonl"
    ledger_before = ledger.read_bytes()
    result = {"checked_at": datetime.now(timezone.utc).isoformat(), "target": HOST,
              "http_requests_sent": 0, "gemini_api_calls": 0, "application_data_sent": False,
              "execution_scope": "standalone_python_process", "proxy": proxy_state(),
              "packages": {p: importlib.metadata.version(p) for p in
                           ("google-genai", "python-dotenv", "httpx", "httpcore", "certifi", "pydantic", "tenacity", "google-auth")}}
    result["credential_in_process_environment"] = bool(os.environ.get("GEMINI_API_KEY", "").strip())
    try:
        result["credential_available_to_backend"] = bool(read_api_key())
        result["credential_source"] = "process_environment" if "GEMINI_API_KEY" in os.environ else "root_dotenv"
    except Exception:
        result["credential_available_to_backend"] = False
    result["dns"] = measure(lambda: {"address_count": len(socket.getaddrinfo(HOST, 443, type=socket.SOCK_STREAM))})
    result["tcp_443"] = measure(tcp)
    result["tls_certifi_matching_httpx"] = measure(lambda: tls(ssl.create_default_context(cafile=certifi.where())))
    # Compare with the operating system trust context, preserving validation in both cases.
    result["tls_system_context"] = measure(lambda: tls(ssl.create_default_context()))
    result["ledger_unchanged"] = ledger.read_bytes() == ledger_before
    assert result["ledger_unchanged"]
    OUT.mkdir(exist_ok=True)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    try:
        assert read_api_key() not in text
    except Exception:
        raise RuntimeError("safe_diagnostic_output_check_failed") from None
    with (OUT / "network_checks.json").open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print(text)


if __name__ == "__main__":
    main()
