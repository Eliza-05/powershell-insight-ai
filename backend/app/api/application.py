"""Loopback MVP API. No sample storage, model downloads, or changes to pipeline policy."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.contracts import AnalysisRequest, ErrorResponse, PENDING
from app.api.transport import WebTransport
from app.schemas.pipeline import ComparisonResult, PipelineResult
from app.services.pipelines.config import PipelineSettings
from app.services.pipelines.ollama import LocalTransport, OllamaAdapter
from app.services.pipelines.service import AnalysisService

APP_VERSION = "0.3.0"
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ORIGINS = ("http://127.0.0.1:5173", "http://localhost:5173", "http://127.0.0.1:8000", "http://localhost:8000")


def error_response(code, message, status=400, details=None):
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message, "details": details or []}})


class LocalBoundary:
    """Bound bodies before JSON parsing and deny cross-origin submissions explicitly."""
    def __init__(self, app, *, max_body_bytes, origins):
        self.app, self.max_body_bytes, self.origins = app, max_body_bytes, set(origins)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = {k.lower(): v for k, v in scope["headers"]}
        if scope["path"].startswith("/api/") and scope["method"] == "POST":
            origin = headers.get(b"origin", b"").decode("latin-1")
            if origin and origin not in self.origins:
                return await error_response("origin_forbidden", "Origen no autorizado para la aplicación local.", 403)(scope, receive, send)
            if headers.get(b"content-type", b"").split(b";", 1)[0].strip().lower() != b"application/json":
                return await error_response("content_type", "Envía el script como JSON UTF-8.", 415)(scope, receive, send)
            try:
                declared = int(headers.get(b"content-length", b"0"))
            except ValueError:
                return await error_response("invalid_length", "Content-Length inválido.")(scope, receive, send)
            if declared > self.max_body_bytes or declared < 0:
                return await error_response("body_too_large", "La solicitud supera el tamaño permitido.", 413)(scope, receive, send)
            chunks, total = [], 0
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                chunk = message.get("body", b"")
                total += len(chunk)
                if total > self.max_body_bytes:
                    return await error_response("body_too_large", "La solicitud supera el tamaño permitido.", 413)(scope, receive, send)
                chunks.append(chunk)
                if not message.get("more_body", False):
                    break
            raw = b"".join(chunks)
            consumed = False

            async def replay():
                nonlocal consumed
                if not consumed:
                    consumed = True
                    return {"type": "http.request", "body": raw, "more_body": False}
                return await receive()
            await self.app(scope, replay, send)
            return
        await self.app(scope, receive, send)


PROFILES = ("qwen14", "qwen3coder-v2")


def selected_profile():
    """PSI_LLM_PROFILE picks exactly one local profile; unknown values fail (no silent fallback)."""
    profile = os.environ.get("PSI_LLM_PROFILE", "qwen14")
    if profile not in PROFILES:
        raise ValueError(f"PSI_LLM_PROFILE must be one of {PROFILES}")
    return profile


def load_pipeline_settings():
    if selected_profile() == "qwen3coder-v2":
        from app.services.llm.qwen3coder_prototype import load_settings
    else:
        from app.services.llm.qwen14_prototype import load_settings
    return load_settings()


def create_app(*, service: AnalysisService | None = None, status_provider=None, frontend_dir: Path | None = None):
    if service is None:
        if selected_profile() == "qwen3coder-v2":
            from app.services.llm.qwen3coder_prototype import create_service
            service = create_service()
        else:
            from app.services.llm.qwen14_prototype import PrototypeAdapter
            settings = load_pipeline_settings()
            service = AnalysisService(settings, adapter=PrototypeAdapter(settings))
    cfg = service.settings
    provider_metadata = getattr(service.adapter, "public_metadata", lambda: {})()
    status_provider = status_provider or (service.status if provider_metadata else
        OllamaAdapter(cfg, transport_factory=lambda: LocalTransport(cfg.port, timeout=3)).status)
    app = FastAPI(title="PowerShell Insight AI", version=APP_VERSION, docs_url=None, redoc_url=None,
                  description="Static local analysis. LLM provisional; no scientific validation implied.")
    # These locks bound admitted work, not an unbounded waiting queue. Phase 2 retains its OS inference gate.
    app.state.a_slots = asyncio.Semaphore(2)
    app.state.llm_slot = asyncio.Semaphore(1)
    app.state.status_slot = asyncio.Semaphore(1)
    app.state.analysis_service = service
    origins = list(DEFAULT_ORIGINS)
    app.add_middleware(LocalBoundary, max_body_bytes=cfg.max_input_bytes * 6 + 4096, origins=origins)
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False,
                       allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])

    @app.middleware("http")
    async def response_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_payload(request, exc):
        details = [{"loc": list(e["loc"]), "message": e["msg"], "type": e["type"]} for e in exc.errors()]
        return error_response("invalid_payload", "Revisa el formato de la solicitud.", 422, details)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request, exc):
        code = {404: "not_found", 405: "method_not_allowed"}.get(exc.status_code, "http_error")
        message = {404: "Recurso no encontrado.", 405: "Método no permitido para este recurso."}.get(exc.status_code, "La solicitud no pudo completarse.")
        return error_response(code, message, exc.status_code)

    @app.exception_handler(Exception)
    async def unexpected(request, exc):
        # Never echo a traceback, local paths, request body or model response in HTTP errors.
        return error_response("internal_error", "No se pudo completar la solicitud. Revisa el servicio local.", 500)

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "version": APP_VERSION, "analysis_active": app.state.llm_slot.locked(),
                "storage": "request_memory_only", "static_only": True}

    @app.get("/api/metadata")
    async def metadata():
        return {"name": "PowerShell Insight AI", "version": APP_VERSION, "phase": "3",
                "llm_status": "provisional", "pilot_v2": "PENDIENTE / INCONCLUSO", "phase4_started": False,
                "pending_phase4": PENDING, "schemas": {"result": "pipeline-v1", "comparison": "comparison-v1"},
                **provider_metadata.get("research_status", {})}

    @app.get("/api/capabilities")
    async def capabilities():
        return {"configurations": ["A", "B", "C", "ABC"], "max_input_bytes": cfg.max_input_bytes,
                "model": cfg.model, "expected_digest": cfg.expected_digest,
                "options": cfg.options.model_dump(), "think": cfg.think, "timeout_seconds": cfg.timeout_seconds,
                "maximum_parallel_inferences": 1, "maximum_parallel_A": 2,
                "minimum_margin_bytes": cfg.minimum_margin_bytes, "automatic_sample_storage": False,
                **provider_metadata,
                "semantic_validation": False, "execution_of_samples": False,
                "mode_descriptions": {"A": "Desofuscación y reglas deterministas; funciona sin Ollama.",
                    "B": "LLM sobre el original, sin evidencia del motor.",
                    "C": "LLM sobre original y recuperación de 1A; sin etiquetas de 1B.",
                    "ABC": "Tres resultados independientes; no mide calidad científica."}}

    @app.get("/api/provider/status")
    @app.get("/api/ollama/status")
    async def ollama_status():
        if app.state.status_slot.locked():
            return error_response("status_busy", "Ya hay una consulta de estado en curso.", 409)
        async with app.state.status_slot:
            state = await run_in_threadpool(status_provider)
            return {"model": cfg.model, "expected_digest": cfg.expected_digest,
                    **provider_metadata, "provisional": True, "analysis_active": app.state.llm_slot.locked(), **state}

    def validate_input(payload):
        try:
            raw = payload.script.encode("utf-8")
        except UnicodeError:
            return error_response("invalid_unicode", "El texto contiene caracteres Unicode inválidos.", 422)
        if len(raw) > cfg.max_input_bytes:
            return error_response("input_too_large", f"El límite es {cfg.max_input_bytes} bytes UTF-8.", 413)
        if not payload.script.strip():
            return error_response("empty_input", "Pega o carga un script antes de analizar.", 422)
        return None

    async def execute(payload, configuration):
        failure = validate_input(payload)
        if failure is not None:
            return failure
        slot = app.state.a_slots if configuration == "A" else app.state.llm_slot
        if slot.locked():
            return error_response("analysis_busy", "Hay un análisis en curso. Espera a que termine; no se reintentará automáticamente.", 409)
        async with slot:
            if configuration == "ABC":
                return await run_in_threadpool(service.compare, payload.script)
            return await run_in_threadpool(service.analyze, payload.script, configuration)

    errors = {409: {"model": ErrorResponse}, 413: {"model": ErrorResponse}, 422: {"model": ErrorResponse}}

    @app.post("/api/analyze/{configuration}", response_model=PipelineResult, responses=errors)
    async def analyze(configuration: Literal["A", "B", "C"], payload: AnalysisRequest):
        return await execute(payload, configuration)

    @app.post("/api/compare", response_model=ComparisonResult, responses=errors)
    async def compare(payload: AnalysisRequest):
        return await execute(payload, "ABC")

    # Optional single-origin production build. Does not expose the repository or arbitrary paths.
    dist = frontend_dir if frontend_dir is not None else ROOT / "frontend/dist"
    if (dist / "index.html").is_file():
        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
    return app
