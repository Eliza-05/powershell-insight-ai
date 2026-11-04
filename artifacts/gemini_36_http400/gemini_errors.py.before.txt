"""Closed diagnostic vocabulary. Never stringify exceptions, requests or response bodies."""
import errno
import socket
import ssl

import httpx

from app.services.pipelines.resources import OperationalFailure


def safe_failure(exc, http_status=None):
    chain, pending, seen = [], [exc], set()
    while pending and len(chain) < 16:
        item = pending.pop(0)
        if id(item) in seen:
            continue
        seen.add(id(item))
        chain.append(item)
        pending.extend(cause for cause in (item.__cause__, item.__context__) if isinstance(cause, BaseException))
    status = http_status if type(http_status) is int and 100 <= http_status <= 599 else None
    for item in chain:
        if isinstance(item, httpx.HTTPStatusError):
            status = item.response.status_code
        value = getattr(item, "code", None)
        if type(value) is int and 100 <= value <= 599:
            status = value
    os_codes = [v for item in chain for v in (getattr(item, "winerror", None), getattr(item, "errno", None))
                if type(v) is int]
    if isinstance(exc, OperationalFailure):
        code = exc.code  # Internal errors are constructed from constant categories only.
    elif any(isinstance(e, socket.gaierror) for e in chain):
        code = "gemini_dns_failure"
    elif any(isinstance(e, ssl.SSLCertVerificationError) for e in chain):
        code = "gemini_tls_certificate_error"
    elif any(isinstance(e, ssl.SSLError) for e in chain):
        code = "gemini_tls_handshake_error"
    elif any(isinstance(e, httpx.DecodingError) for e in chain):
        code = "gemini_response_decoding_error"
    elif any(isinstance(e, (TimeoutError, httpx.TimeoutException)) for e in chain):
        code = "gemini_timeout"
    elif any(isinstance(e, ConnectionRefusedError) for e in chain) or 10061 in os_codes:
        code = "gemini_connection_refused"
    elif any(isinstance(e, PermissionError) for e in chain) or 10013 in os_codes:
        code = "gemini_network_access_denied"
    elif any(c in {errno.ENETUNREACH, errno.EHOSTUNREACH, 10051, 10065} for c in os_codes):
        code = "gemini_network_unreachable"
    elif status in {400, 401, 403, 404, 408, 429}:
        code = {400: "gemini_invalid_request", 401: "gemini_authentication_error", 403: "gemini_permission_denied",
                404: "gemini_model_unavailable", 408: "gemini_timeout", 429: "gemini_quota_exhausted"}[status]
    elif status is not None and 500 <= status <= 599:
        code = "gemini_http_server_error"
    elif status is not None and 300 <= status <= 399:
        code = "gemini_redirect_rejected"
    elif any(isinstance(e, httpx.ConnectError) for e in chain):
        code = "gemini_connection_error"
    elif any(isinstance(e, httpx.ProxyError) for e in chain):
        code = "gemini_proxy_error"
    elif any(isinstance(e, httpx.ProtocolError) for e in chain):
        code = "gemini_http_protocol_error"
    elif isinstance(exc, (ValueError, TypeError, AttributeError, RuntimeError)):
        code = "gemini_local_client_error"
    else:
        code = "gemini_transport_error"
    return {"category": code, "http_status": status}
