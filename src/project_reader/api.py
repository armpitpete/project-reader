from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass
from http import HTTPStatus
import json
import os
import time
from threading import Lock
from typing import Any, Awaitable, Callable, Deque, Mapping
from urllib.parse import urlparse
import re

from .evidence import (
    EvidenceCollectionError,
    RepositorySizeLimitError,
    collect_public_evidence,
    parse_repository_address,
)
from .interpretation import InterpretationError, interpret_evidence_bundle
from .reading import build_project_reading
from .render import render_html_string

DEFAULT_ALLOWED_ORIGINS = ("https://armpitpete.github.io",)
DEFAULT_API_BASE_URL = "https://reader-api.merrinworld.uk"
SHA = re.compile(r"^[0-9a-f]{40}$")

Receive = Callable[[], Awaitable[dict[str, Any]]]
Send = Callable[[dict[str, Any]], Awaitable[None]]
Pipeline = Callable[[str, "APIConfig"], dict[str, Any]]


@dataclass(frozen=True)
class APIConfig:
    allowed_origins: frozenset[str] = frozenset(DEFAULT_ALLOWED_ORIGINS)
    api_base_url: str = DEFAULT_API_BASE_URL
    max_request_bytes: int = 4096
    max_repository_size_kb: int = 50_000
    read_timeout_seconds: float = 120.0
    rate_limit_requests: int = 20
    rate_limit_window_seconds: int = 60
    github_token: str | None = None
    deployed_commit: str | None = None


class PublicAPIError(Exception):
    def __init__(
        self,
        status: HTTPStatus,
        code: str,
        detail: str,
        *,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(detail)
        self.status = status
        self.code = code
        self.detail = detail
        self.retry_after = retry_after


class RateLimiter:
    def __init__(self, *, requests: int, window_seconds: int, max_keys: int = 2048) -> None:
        self.requests = requests
        self.window_seconds = window_seconds
        self.max_keys = max_keys
        self._hits: dict[str, Deque[float]] = {}
        self._lock = Lock()

    def check(self, key: str, *, now: float | None = None) -> int | None:
        if self.requests <= 0 or self.window_seconds <= 0:
            return None
        active_now = time.monotonic() if now is None else now
        threshold = active_now - self.window_seconds
        with self._lock:
            if key not in self._hits and len(self._hits) >= self.max_keys:
                oldest_key = min(
                    self._hits,
                    key=lambda item: self._hits[item][0] if self._hits[item] else active_now,
                )
                self._hits.pop(oldest_key, None)
            hits = self._hits.setdefault(key, deque())
            while hits and hits[0] <= threshold:
                hits.popleft()
            if len(hits) >= self.requests:
                return max(1, int(hits[0] + self.window_seconds - active_now))
            hits.append(active_now)
        return None


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError as error:
        raise RuntimeError(f"{name} must be an integer") from error
    if value <= 0:
        raise RuntimeError(f"{name} must be greater than zero")
    return value


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = float(raw)
    except ValueError as error:
        raise RuntimeError(f"{name} must be a number") from error
    if value <= 0:
        raise RuntimeError(f"{name} must be greater than zero")
    return value


def _origin(value: str) -> str:
    parsed = urlparse(value.strip())
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.params
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
        or any(ord(char) < 32 for char in value)
    ):
        raise RuntimeError("PROJECT_READER_ALLOWED_ORIGINS must contain CORS origins only")
    return f"{parsed.scheme}://{parsed.netloc}"


def _api_base(value: str) -> str:
    parsed = urlparse(value.strip())
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.params
        or parsed.query
        or parsed.fragment
        or any(ord(char) < 32 for char in value)
    ):
        raise RuntimeError("PROJECT_READER_API_BASE_URL must be a complete https URL")
    return value.rstrip("/")


def _optional_sha(name: str) -> str | None:
    value = os.getenv(name)
    if value is None or not value.strip():
        return None
    candidate = value.strip()
    if not SHA.fullmatch(candidate):
        raise RuntimeError(f"{name} must be a 40-character lowercase Git SHA")
    return candidate


def config_from_env() -> APIConfig:
    origins_raw = os.getenv("PROJECT_READER_ALLOWED_ORIGINS")
    origins = (
        tuple(_origin(item) for item in origins_raw.split(",") if item.strip())
        if origins_raw
        else DEFAULT_ALLOWED_ORIGINS
    )
    if not origins:
        raise RuntimeError("PROJECT_READER_ALLOWED_ORIGINS must not be empty")
    return APIConfig(
        allowed_origins=frozenset(origins),
        api_base_url=_api_base(os.getenv("PROJECT_READER_API_BASE_URL", DEFAULT_API_BASE_URL)),
        max_request_bytes=_env_int("PROJECT_READER_MAX_REQUEST_BYTES", 4096),
        max_repository_size_kb=_env_int("PROJECT_READER_MAX_REPOSITORY_SIZE_KB", 50_000),
        read_timeout_seconds=_env_float("PROJECT_READER_READ_TIMEOUT_SECONDS", 120.0),
        rate_limit_requests=_env_int("PROJECT_READER_RATE_LIMIT_REQUESTS", 20),
        rate_limit_window_seconds=_env_int("PROJECT_READER_RATE_LIMIT_WINDOW_SECONDS", 60),
        github_token=os.getenv("PROJECT_READER_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN"),
        deployed_commit=_optional_sha("PROJECT_READER_DEPLOYED_COMMIT"),
    )


def _completion_label(percentage: int | None) -> str:
    if percentage is None:
        return "Unknown"
    return f"{percentage}%"


def default_pipeline(repository: str, config: APIConfig) -> dict[str, Any]:
    evidence = collect_public_evidence(
        repository,
        token=config.github_token,
        max_repository_size_kb=config.max_repository_size_kb,
    )
    interpretation = interpret_evidence_bundle(evidence)
    reading = build_project_reading(interpretation)
    return {
        "schema_version": 1,
        "repository": evidence.repository,
        "repository_url": evidence.repository_url,
        "source_commit": evidence.source_commit,
        "checked_at": evidence.checked_at,
        "status": reading.status,
        "completion": {
            "label": _completion_label(reading.completion.percentage),
            "percentage": reading.completion.percentage,
            "evidence_strength": reading.completion.evidence_strength.value,
            "explanation": reading.completion.explanation,
        },
        "likelihood": {
            "label": reading.likelihood.label,
            "confidence": reading.likelihood.confidence,
            "timeframe": reading.likelihood.timeframe,
        },
        "evidence_summary": {
            "important_file_count": len(evidence.important_files),
            "progress_record_count": len(evidence.progress_records),
            "repository_language_count": len(evidence.repository_languages),
            "open_issue_count": len(evidence.open_issues),
            "open_pull_request_count": len(evidence.open_pull_requests),
        },
        "result_html": render_html_string(reading),
        "limitations": [
            "Only public GitHub repositories are supported.",
            "Completion and likelihood stay unknown unless current owner-authority evidence supports them.",
            "The service does not read private repositories or write to GitHub.",
        ],
    }


def _headers(scope: Mapping[str, Any]) -> dict[str, str]:
    return {
        key.decode("latin-1").casefold(): value.decode("latin-1")
        for key, value in scope.get("headers", [])
    }


def _local_peer(scope: Mapping[str, Any]) -> bool:
    client = scope.get("client")
    if not isinstance(client, tuple) or not client:
        return False
    return client[0] in {"127.0.0.1", "::1", "localhost"}


def _client_key(scope: Mapping[str, Any], headers: Mapping[str, str]) -> str:
    if _local_peer(scope):
        for name in ("cf-connecting-ip", "x-forwarded-for"):
            value = headers.get(name, "")
            first = value.split(",", 1)[0].strip()
            if first and len(first) <= 64:
                return first
    client = scope.get("client")
    if isinstance(client, tuple) and client:
        return str(client[0])[:64]
    return "unknown"


class ProjectReaderAPI:
    def __init__(
        self,
        *,
        config: APIConfig | None = None,
        pipeline: Pipeline = default_pipeline,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        self.config = config or config_from_env()
        self.pipeline = pipeline
        self.rate_limiter = rate_limiter or RateLimiter(
            requests=self.config.rate_limit_requests,
            window_seconds=self.config.rate_limit_window_seconds,
        )

    async def __call__(self, scope: dict[str, Any], receive: Receive, send: Send) -> None:
        scope_type = scope.get("type")
        if scope_type == "lifespan":
            await self._lifespan(receive, send)
            return
        if scope_type != "http":
            raise RuntimeError("Project Reader API only supports HTTP")

        method = str(scope.get("method", "GET")).upper()
        path = str(scope.get("path", "/"))
        headers = _headers(scope)
        try:
            if method == "OPTIONS" and path == "/api/v1/read":
                await self._preflight(scope, send, headers)
                return
            if path == "/health" and method == "GET":
                await self._json(scope, send, HTTPStatus.OK, {"status": "ok"})
                return
            if path == "/ready" and method == "GET":
                await self._json(
                    scope,
                    send,
                    HTTPStatus.OK,
                    {"ready": True, "service": "project-reader-api"},
                )
                return
            if path == "/api/v1/status" and method == "GET":
                await self._json(scope, send, HTTPStatus.OK, self._status_payload())
                return
            if path == "/api/v1/read" and method == "POST":
                retry_after = self.rate_limiter.check(_client_key(scope, headers))
                if retry_after is not None:
                    raise PublicAPIError(
                        HTTPStatus.TOO_MANY_REQUESTS,
                        "rate_limited",
                        "Too many reads from this client. Try again shortly.",
                        retry_after=retry_after,
                    )
                await self._read_repository(scope, receive, send, headers)
                return
            raise PublicAPIError(
                HTTPStatus.NOT_FOUND,
                "not_found",
                "That Project Reader API route is not available.",
            )
        except PublicAPIError as error:
            extra = {"retry-after": str(error.retry_after)} if error.retry_after else None
            await self._json(
                scope,
                send,
                error.status,
                {"ok": False, "code": error.code, "detail": error.detail},
                extra_headers=extra,
            )

    async def _lifespan(self, receive: Receive, send: Send) -> None:
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return

    def _status_payload(self) -> dict[str, Any]:
        return {
            "service": "project-reader-api",
            "schema_version": 1,
            "api_base_url": self.config.api_base_url,
            "deployed_commit": self.config.deployed_commit,
            "write_enabled": False,
            "authority_pipeline": [
                "project_reader.evidence.collect_public_evidence",
                "project_reader.interpretation.interpret_evidence_bundle",
                "project_reader.reading.build_project_reading",
                "project_reader.render.render_html_string",
            ],
            "routes": ["/health", "/ready", "/api/v1/status", "/api/v1/read"],
            "allowed_origins": sorted(self.config.allowed_origins),
            "limits": {
                "max_request_bytes": self.config.max_request_bytes,
                "max_repository_size_kb": self.config.max_repository_size_kb,
                "read_timeout_seconds": self.config.read_timeout_seconds,
                "rate_limit_requests": self.config.rate_limit_requests,
                "rate_limit_window_seconds": self.config.rate_limit_window_seconds,
            },
            "privacy": {
                "persistent_user_data": False,
                "browser_credentials_required": False,
                "github_write_access": False,
            },
        }

    async def _preflight(
        self,
        scope: Mapping[str, Any],
        send: Send,
        headers: Mapping[str, str],
    ) -> None:
        origin = headers.get("origin")
        if origin and origin not in self.config.allowed_origins:
            await self._json(
                scope,
                send,
                HTTPStatus.FORBIDDEN,
                {"ok": False, "code": "origin_not_allowed", "detail": "This origin is not allowed."},
            )
            return
        response_headers = {
            "access-control-allow-methods": "POST, OPTIONS",
            "access-control-allow-headers": "content-type",
            "access-control-max-age": "600",
        }
        await self._empty(scope, send, HTTPStatus.NO_CONTENT, extra_headers=response_headers)

    async def _read_repository(
        self,
        scope: Mapping[str, Any],
        receive: Receive,
        send: Send,
        headers: Mapping[str, str],
    ) -> None:
        content_type = headers.get("content-type", "").split(";", 1)[0].strip().casefold()
        if content_type != "application/json":
            raise PublicAPIError(
                HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                "unsupported_media_type",
                "Send a JSON body with a repository field.",
            )
        body = await self._body(receive, headers)
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise PublicAPIError(
                HTTPStatus.BAD_REQUEST,
                "invalid_json",
                "The request body must be valid JSON.",
            ) from error
        if not isinstance(payload, dict):
            raise PublicAPIError(
                HTTPStatus.BAD_REQUEST,
                "invalid_json",
                "The request body must be a JSON object.",
            )
        repository = payload.get("repository")
        if not isinstance(repository, str) or len(repository) > 300:
            raise PublicAPIError(
                HTTPStatus.UNPROCESSABLE_ENTITY,
                "invalid_repository",
                "Use a public GitHub repository in the form owner/name or https://github.com/owner/name.",
            )
        try:
            parse_repository_address(repository)
        except ValueError as error:
            raise PublicAPIError(
                HTTPStatus.UNPROCESSABLE_ENTITY,
                "invalid_repository",
                "Use a public GitHub repository in the form owner/name or https://github.com/owner/name.",
            ) from error

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(self.pipeline, repository, self.config),
                timeout=self.config.read_timeout_seconds,
            )
        except asyncio.TimeoutError as error:
            raise PublicAPIError(
                HTTPStatus.GATEWAY_TIMEOUT,
                "read_timeout",
                "Project Reader did not finish reading that repository before the public timeout.",
            ) from error
        except RepositorySizeLimitError as error:
            raise PublicAPIError(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                "repository_too_large",
                "That repository is larger than the public Project Reader size limit.",
            ) from error
        except EvidenceCollectionError as error:
            raise PublicAPIError(
                HTTPStatus.UNPROCESSABLE_ENTITY,
                "repository_unreadable",
                "Project Reader could not safely read that public GitHub repository.",
            ) from error
        except (InterpretationError, ValueError) as error:
            raise PublicAPIError(
                HTTPStatus.UNPROCESSABLE_ENTITY,
                "reading_unavailable",
                "Project Reader could not produce a supported reading for that repository.",
            ) from error
        except Exception as error:
            raise PublicAPIError(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "read_failed",
                "Project Reader could not complete the reading.",
            ) from error

        await self._json(scope, send, HTTPStatus.OK, {"ok": True, **result})

    async def _body(self, receive: Receive, headers: Mapping[str, str]) -> bytes:
        length = headers.get("content-length")
        if length:
            try:
                content_length = int(length)
            except ValueError:
                content_length = self.config.max_request_bytes + 1
            if content_length > self.config.max_request_bytes:
                raise PublicAPIError(
                    HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                    "request_too_large",
                    "The request body is larger than the public API limit.",
                )

        chunks: list[bytes] = []
        total = 0
        more = True
        while more:
            message = await receive()
            if message["type"] != "http.request":
                continue
            chunk = message.get("body", b"")
            if chunk:
                total += len(chunk)
                if total > self.config.max_request_bytes:
                    raise PublicAPIError(
                        HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                        "request_too_large",
                        "The request body is larger than the public API limit.",
                    )
                chunks.append(chunk)
            more = bool(message.get("more_body", False))
        return b"".join(chunks)

    def _response_headers(
        self,
        scope: Mapping[str, Any],
        *,
        content_type: str | None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> list[tuple[bytes, bytes]]:
        request_headers = _headers(scope)
        origin = request_headers.get("origin")
        headers: dict[str, str] = {
            "cache-control": "no-store",
            "x-content-type-options": "nosniff",
            "referrer-policy": "no-referrer",
            "vary": "Origin",
        }
        if content_type is not None:
            headers["content-type"] = content_type
        if origin in self.config.allowed_origins:
            headers["access-control-allow-origin"] = origin
        if extra_headers:
            headers.update(extra_headers)
        return [(key.encode("latin-1"), value.encode("latin-1")) for key, value in headers.items()]

    async def _empty(
        self,
        scope: Mapping[str, Any],
        send: Send,
        status: HTTPStatus,
        *,
        extra_headers: Mapping[str, str] | None = None,
    ) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": status.value,
                "headers": self._response_headers(
                    scope,
                    content_type=None,
                    extra_headers=extra_headers,
                ),
            }
        )
        await send({"type": "http.response.body", "body": b""})

    async def _json(
        self,
        scope: Mapping[str, Any],
        send: Send,
        status: HTTPStatus,
        payload: Mapping[str, Any],
        *,
        extra_headers: Mapping[str, str] | None = None,
    ) -> None:
        encoded = (
            json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": status.value,
                "headers": self._response_headers(
                    scope,
                    content_type="application/json; charset=utf-8",
                    extra_headers=extra_headers,
                ),
            }
        )
        await send({"type": "http.response.body", "body": encoded})


app = ProjectReaderAPI()
