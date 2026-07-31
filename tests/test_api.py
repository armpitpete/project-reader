from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from project_reader.api import APIConfig, ProjectReaderAPI, RateLimiter
from project_reader.evidence import EvidenceCollectionError, RepositorySizeLimitError


def config(**overrides) -> APIConfig:
    values = {
        "allowed_origins": frozenset({"https://armpitpete.github.io"}),
        "api_base_url": "https://reader-api.merrinworld.uk",
        "max_request_bytes": 256,
        "max_repository_size_kb": 500,
        "read_timeout_seconds": 2.0,
        "rate_limit_requests": 20,
        "rate_limit_window_seconds": 60,
        "github_token": "server-only-token",
    }
    values.update(overrides)
    return APIConfig(**values)


async def call(
    app: ProjectReaderAPI,
    *,
    method: str = "GET",
    path: str = "/",
    body: bytes = b"",
    headers: dict[str, str] | None = None,
    client: tuple[str, int] = ("127.0.0.1", 1234),
) -> tuple[int, dict[str, str], bytes]:
    active_headers = {key.casefold(): value for key, value in (headers or {}).items()}
    if body and "content-length" not in active_headers:
        active_headers["content-length"] = str(len(body))
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": [
            (key.encode("latin-1"), value.encode("latin-1"))
            for key, value in active_headers.items()
        ],
        "client": client,
    }
    messages = [{"type": "http.request", "body": body, "more_body": False}]
    sent: list[dict[str, Any]] = []

    async def receive() -> dict[str, Any]:
        return messages.pop(0)

    async def send(message: dict[str, Any]) -> None:
        sent.append(message)

    await app(scope, receive, send)
    start = sent[0]
    response_body = b"".join(message.get("body", b"") for message in sent[1:])
    response_headers = {
        key.decode("latin-1"): value.decode("latin-1")
        for key, value in start["headers"]
    }
    return start["status"], response_headers, response_body


def post_body(repository: str) -> bytes:
    return json.dumps({"repository": repository}).encode("utf-8")


def successful_pipeline(repository: str, active_config: APIConfig) -> dict[str, Any]:
    assert active_config.github_token == "server-only-token"
    return {
        "schema_version": 1,
        "repository": "example/project",
        "repository_url": "https://github.com/example/project",
        "source_commit": "a" * 40,
        "checked_at": "2026-07-30T12:00:00Z",
        "status": "Unknown",
        "completion": {
            "label": "Unknown",
            "percentage": None,
            "evidence_strength": "unknown",
            "explanation": "Completion cannot be measured.",
        },
        "likelihood": {
            "label": "Unknown",
            "confidence": "Low",
            "timeframe": "Insufficient evidence.",
        },
        "evidence_summary": {
            "important_file_count": 1,
            "progress_record_count": 0,
            "repository_language_count": 1,
            "open_issue_count": 0,
            "open_pull_request_count": 0,
        },
        "result_html": "<!doctype html><title>Project Reader result</title>",
        "limitations": ["Only public GitHub repositories are supported."],
    }


def test_status_describes_read_only_authority_pipeline() -> None:
    app = ProjectReaderAPI(config=config(), pipeline=successful_pipeline)

    status, headers, raw = asyncio.run(call(app, path="/api/v1/status"))
    payload = json.loads(raw)

    assert status == 200
    assert headers["content-type"] == "application/json; charset=utf-8"
    assert payload["service"] == "project-reader-api"
    assert payload["write_enabled"] is False
    assert payload["allowed_origins"] == ["https://armpitpete.github.io"]
    assert payload["api_base_url"] == "https://reader-api.merrinworld.uk"
    assert payload["deployed_commit"] is None
    assert payload["privacy"] == {
        "browser_credentials_required": False,
        "github_write_access": False,
        "persistent_user_data": False,
    }
    assert payload["authority_pipeline"] == [
        "project_reader.evidence.collect_public_evidence",
        "project_reader.interpretation.interpret_evidence_bundle",
        "project_reader.reading.build_project_reading",
        "project_reader.render.render_html_fragment",
    ]


def test_read_endpoint_returns_rendered_project_reader_result() -> None:
    seen: list[str] = []

    def pipeline(repository: str, active_config: APIConfig) -> dict[str, Any]:
        seen.append(repository)
        return successful_pipeline(repository, active_config)

    app = ProjectReaderAPI(config=config(), pipeline=pipeline)

    status, headers, raw = asyncio.run(
        call(
            app,
            method="POST",
            path="/api/v1/read",
            body=post_body("https://github.com/example/project"),
            headers={
                "content-type": "application/json",
                "origin": "https://armpitpete.github.io",
            },
        )
    )
    payload = json.loads(raw)

    assert status == 200
    assert headers["access-control-allow-origin"] == "https://armpitpete.github.io"
    assert seen == ["https://github.com/example/project"]
    assert payload["ok"] is True
    assert payload["repository"] == "example/project"
    assert payload["source_commit"] == "a" * 40
    assert payload["result_html"].startswith("<!doctype html>")


def test_read_endpoint_rejects_malformed_and_unsafe_repository_without_pipeline_call() -> None:
    seen: list[str] = []
    app = ProjectReaderAPI(
        config=config(),
        pipeline=lambda repository, active_config: seen.append(repository) or {},
    )

    status, _, raw = asyncio.run(
        call(
            app,
            method="POST",
            path="/api/v1/read",
            body=post_body("javascript:alert(1)"),
            headers={"content-type": "application/json"},
        )
    )
    payload = json.loads(raw)

    assert status == 422
    assert payload["code"] == "invalid_repository"
    assert "owner/name" in payload["detail"]
    assert seen == []


def test_read_endpoint_rejects_non_repository_github_paths() -> None:
    app = ProjectReaderAPI(config=config(), pipeline=successful_pipeline)

    status, _, raw = asyncio.run(
        call(
            app,
            method="POST",
            path="/api/v1/read",
            body=post_body("https://github.com/example/project/issues/1"),
            headers={"content-type": "application/json"},
        )
    )
    payload = json.loads(raw)

    assert status == 422
    assert payload["code"] == "invalid_repository"


def test_read_endpoint_safely_maps_private_or_unreadable_repository_errors() -> None:
    def failed_pipeline(repository: str, active_config: APIConfig) -> dict[str, Any]:
        raise EvidenceCollectionError(
            "GitHub returned HTTP 404 for https://api.github.com/repos/example/project?token=x"
        )

    app = ProjectReaderAPI(config=config(), pipeline=failed_pipeline)

    status, _, raw = asyncio.run(
        call(
            app,
            method="POST",
            path="/api/v1/read",
            body=post_body("example/project"),
            headers={"content-type": "application/json"},
        )
    )
    payload = json.loads(raw)

    assert status == 422
    assert payload["code"] == "repository_unreadable"
    assert "api.github.com" not in payload["detail"]
    assert "token" not in payload["detail"].casefold()


def test_read_endpoint_maps_repository_size_limit() -> None:
    def failed_pipeline(repository: str, active_config: APIConfig) -> dict[str, Any]:
        raise RepositorySizeLimitError("Repository exceeds the size limit")

    app = ProjectReaderAPI(config=config(), pipeline=failed_pipeline)

    status, _, raw = asyncio.run(
        call(
            app,
            method="POST",
            path="/api/v1/read",
            body=post_body("example/project"),
            headers={"content-type": "application/json"},
        )
    )
    payload = json.loads(raw)

    assert status == 413
    assert payload["code"] == "repository_too_large"


def test_read_endpoint_enforces_request_body_limit() -> None:
    app = ProjectReaderAPI(config=config(max_request_bytes=10), pipeline=successful_pipeline)

    status, _, raw = asyncio.run(
        call(
            app,
            method="POST",
            path="/api/v1/read",
            body=post_body("example/project"),
            headers={"content-type": "application/json"},
        )
    )
    payload = json.loads(raw)

    assert status == 413
    assert payload["code"] == "request_too_large"


def test_read_endpoint_times_out_slow_pipeline() -> None:
    def slow_pipeline(repository: str, active_config: APIConfig) -> dict[str, Any]:
        time.sleep(.05)
        return successful_pipeline(repository, active_config)

    app = ProjectReaderAPI(
        config=config(read_timeout_seconds=.01),
        pipeline=slow_pipeline,
    )

    status, _, raw = asyncio.run(
        call(
            app,
            method="POST",
            path="/api/v1/read",
            body=post_body("example/project"),
            headers={"content-type": "application/json"},
        )
    )
    payload = json.loads(raw)

    assert status == 504
    assert payload["code"] == "read_timeout"


def test_preflight_only_allows_configured_pages_origin() -> None:
    app = ProjectReaderAPI(config=config(), pipeline=successful_pipeline)

    ok_status, ok_headers, _ = asyncio.run(
        call(
            app,
            method="OPTIONS",
            path="/api/v1/read",
            headers={"origin": "https://armpitpete.github.io"},
        )
    )
    bad_status, bad_headers, raw = asyncio.run(
        call(
            app,
            method="OPTIONS",
            path="/api/v1/read",
            headers={"origin": "https://example.com"},
        )
    )

    assert ok_status == 204
    assert ok_headers["access-control-allow-origin"] == "https://armpitpete.github.io"
    assert ok_headers["access-control-allow-methods"] == "POST, OPTIONS"
    assert bad_status == 403
    assert "access-control-allow-origin" not in bad_headers
    assert json.loads(raw)["code"] == "origin_not_allowed"


def test_rate_limiter_returns_retry_after() -> None:
    app = ProjectReaderAPI(
        config=config(rate_limit_requests=1),
        pipeline=successful_pipeline,
        rate_limiter=RateLimiter(requests=1, window_seconds=60),
    )
    request = {
        "method": "POST",
        "path": "/api/v1/read",
        "body": post_body("example/project"),
        "headers": {"content-type": "application/json"},
    }

    first_status, _, _ = asyncio.run(call(app, **request))
    second_status, headers, raw = asyncio.run(call(app, **request))
    payload = json.loads(raw)

    assert first_status == 200
    assert second_status == 429
    assert int(headers["retry-after"]) >= 1
    assert payload["code"] == "rate_limited"
