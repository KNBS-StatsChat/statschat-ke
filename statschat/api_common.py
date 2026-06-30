"""Shared FastAPI hardening helpers for StatsChat API entrypoints."""

from __future__ import annotations

import hmac
import json
import logging
import os
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Deque

from fastapi import Depends, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
)

_RATE_LIMIT_BUCKETS: dict[str, Deque[float]] = defaultdict(deque)


class JsonLogFormatter(logging.Formatter):
    """Minimal JSON-lines formatter for production API logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key in (
            "method",
            "path",
            "status_code",
            "elapsed_ms",
            "client_host",
            "api_mode",
        ):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True)


def _parse_csv_env(name: str, default: tuple[str, ...] = ()) -> list[str]:
    raw_value = os.getenv(name)
    if raw_value is None:
        return list(default)

    stripped = raw_value.strip()
    if not stripped or stripped.lower() in {"off", "none", "false"}:
        return []

    return [item.strip() for item in stripped.split(",") if item.strip()]


def cors_origins_from_env() -> list[str]:
    """Return configured CORS origins.

    Defaults to local frontend origins for development. Set
    ``STATSCHAT_CORS_ORIGINS`` to a comma-separated list in production.
    """

    return _parse_csv_env("STATSCHAT_CORS_ORIGINS", DEFAULT_CORS_ORIGINS)


def configure_cors(app: Any) -> None:
    """Attach CORS middleware using environment-driven allowed origins."""

    origins = cors_origins_from_env()
    if not origins:
        return

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials="*" not in origins,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key"],
    )


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None

    prefix = "bearer "
    if authorization.lower().startswith(prefix):
        return authorization[len(prefix) :].strip()
    return None


async def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    authorization: str | None = Header(default=None),
) -> None:
    """Require an API key when ``STATSCHAT_API_KEY`` is configured."""

    expected = os.getenv("STATSCHAT_API_KEY", "").strip()
    if not expected:
        return

    provided = x_api_key or _extract_bearer_token(authorization)
    if provided and hmac.compare_digest(provided, expected):
        return

    raise HTTPException(status_code=401, detail="Missing or invalid API key")


def _rate_limit_per_minute() -> int:
    raw_value = os.getenv("STATSCHAT_RATE_LIMIT_PER_MINUTE", "0").strip()
    if not raw_value:
        return 0
    try:
        return max(int(raw_value), 0)
    except ValueError:
        return 0


def _rate_limit_window_seconds() -> int:
    raw_value = os.getenv("STATSCHAT_RATE_LIMIT_WINDOW_SECONDS", "60").strip()
    try:
        return max(int(raw_value), 1)
    except ValueError:
        return 60


def _client_identifier(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", maxsplit=1)[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


async def rate_limit(request: Request) -> None:
    """Simple in-process per-client request limiter.

    Disabled by default. Set ``STATSCHAT_RATE_LIMIT_PER_MINUTE`` to enable it.
    For multi-worker deployments this should be complemented by infrastructure
    rate limiting because process-local buckets are not shared.
    """

    limit = _rate_limit_per_minute()
    if limit <= 0:
        return

    window_seconds = _rate_limit_window_seconds()
    now = time.monotonic()
    bucket = _RATE_LIMIT_BUCKETS[_client_identifier(request)]

    while bucket and now - bucket[0] >= window_seconds:
        bucket.popleft()

    if len(bucket) >= limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    bucket.append(now)


def protected_endpoint_dependencies() -> list[Any]:
    """Dependencies used by query-costing endpoints."""

    return [Depends(require_api_key), Depends(rate_limit)]


def configure_api_logging(logger: logging.Logger, session_name: str) -> None:
    """Configure stdout logging plus optional JSON-lines file logging."""

    level_name = os.getenv("STATSCHAT_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=level, format=log_fmt, filemode="a")
    logger.setLevel(level)

    log_path = os.getenv("STATSCHAT_LOG_FILE", "").strip()
    log_dir = os.getenv("STATSCHAT_LOG_DIR", "").strip()
    if not log_path and log_dir:
        log_path = str(Path(log_dir) / f"{session_name}.jsonl")

    if not log_path:
        return

    resolved_log_path = Path(log_path)
    resolved_log_path.parent.mkdir(parents=True, exist_ok=True)
    if any(
        isinstance(handler, logging.FileHandler)
        and Path(handler.baseFilename) == resolved_log_path
        for handler in logger.handlers
    ):
        return

    handler = logging.FileHandler(resolved_log_path, mode="a", encoding="utf-8")
    handler.setLevel(level)
    handler.setFormatter(JsonLogFormatter())
    logger.addHandler(handler)


def configure_request_logging(app: Any, logger: logging.Logger, api_mode: str) -> None:
    """Log request completion metadata without logging request bodies."""

    if getattr(app.state, "statschat_request_logging_enabled", False):
        return
    app.state.statschat_request_logging_enabled = True

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.exception(
                "API request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "elapsed_ms": elapsed_ms,
                    "client_host": _client_identifier(request),
                    "api_mode": api_mode,
                },
            )
            raise

        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.info(
            "API request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "elapsed_ms": elapsed_ms,
                "client_host": _client_identifier(request),
                "api_mode": api_mode,
            },
        )
        return response


def build_health_payload(
    *,
    api_mode: str,
    config: dict[str, Any],
    model_name: str | None = None,
    provider: str | None = None,
    model_loaded: bool | None = None,
) -> dict[str, Any]:
    """Build a non-secret health payload for API liveness checks."""

    db_config = config.get("db", {}) if isinstance(config, dict) else {}
    faiss_roots: dict[str, dict[str, Any]] = {}
    for key in ("faiss_db_root", "faiss_db_root_latest"):
        value = db_config.get(key)
        if value:
            path = Path(str(value))
            faiss_roots[key] = {"path": str(path), "exists": path.exists()}

    if "faiss_db_root" in db_config and "faiss_db_root_latest" not in faiss_roots:
        latest_path = Path(str(db_config["faiss_db_root"]) + "_latest")
        faiss_roots["faiss_db_root_latest"] = {
            "path": str(latest_path),
            "exists": latest_path.exists(),
        }

    return {
        "status": "ok",
        "api_mode": api_mode,
        "model": model_name,
        "provider": provider,
        "model_loaded": model_loaded,
        "faiss": faiss_roots,
        "auth_enabled": bool(os.getenv("STATSCHAT_API_KEY", "").strip()),
        "rate_limit_per_minute": _rate_limit_per_minute(),
        "cors_origins": cors_origins_from_env(),
    }
