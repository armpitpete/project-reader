from datetime import datetime as RealDateTime
import importlib
import json

import pytest

from project_reader.evidence import (
    EvidenceCollectionError,
    RepositorySizeLimitError,
    collect_public_evidence,
    extract_gitingest_files,
    parse_repository_address,
)
from project_reader.ingest import RepositoryDigest, RepositoryFileProvenance


evidence_module = importlib.import_module("project_reader.evidence")
HEAD = "a" * 40
SEPARATOR = "=" * 48
DIGEST_CONTENT = f"""{SEPARATOR}
File: README.md
{SEPARATOR}
# Example

A project.

{SEPARATOR}
File: .project/progress.json
{SEPARATOR}
{{"schema_version": 1, "stages": [{{"id": "one"}}], "overall": {{"enabled": false}}}}

{SEPARATOR}
File: pyproject.toml
{SEPARATOR}
[project]
name = "example"
requires-python = ">=3.12"

{SEPARATOR}
File: src/app.py
{SEPARATOR}
print("hello")

"""


class FakeClient:
    def __init__(self, *, private: bool = False, size: int = 120) -> None:
        self.private = private
        self.size = size
        self.calls: list[str] = []

    def repository(self, address):
        return {"private": self.private, "default_branch": "main", "size": self.size}

    def commit(self, address, ref):
        assert ref == "main"
        return {"sha": HEAD}

    def languages(self, address):
        self.calls.append("languages")
        return {
            "Python": 256862,
            "SourcePawn": 39847,
            "C++": 29503,
            "Pawn": 7835,
            "Shell": 6272,
            "PowerShell": 3603,
        }

    def open_issues(self, address):
        self.calls.append("issues")
        return [
            {
                "number": 3,
                "title": "Open work",
                "html_url": "https://github.com/example/project/issues/3",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-02T00:00:00Z",
                "labels": [{"name": "work"}],
            }
        ]

    def open_pull_requests(self, address):
        self.calls.append("pull_requests")
        return [
            {
                "number": 4,
                "title": "Draft change",
                "html_url": "https://github.com/example/project/pull/4",
                "created_at": "2026-01-03T00:00:00Z",
                "updated_at": "2026-01-04T00:00:00Z",
                "labels": [],
                "draft": True,
            }
        ]


def fake_reader(source: str, *, token=None, include_patterns=None) -> RepositoryDigest:
    assert source == f"https://github.com/example/project/tree/{HEAD}"
    assert token is None
    assert ".project/progress.json" in include_patterns
    assert "README.md" in include_patterns
    assert "pyproject.toml" in include_patterns
    assert "package.json" in include_patterns
    assert "Cargo.toml" in include_patterns
    assert "go.mod" in include_patterns
    assert "Gemfile" in include_patterns
    assert "Dockerfile" in include_patterns
    assert "requirements*.txt" in include_patterns
    return RepositoryDigest(
        summary=f"Repository: example/project\nCommit: {HEAD}",
        tree=(
            "Directory structure:\n"
            "├── README.md\n"
            "├── pyproject.toml\n"
            "└── .project/progress.json"
        ),
        content=DIGEST_CONTENT,
        file_provenance=(
            RepositoryFileProvenance(
                path=".project/progress.json",
                collection_method="exact_public_file",
                source_url=(
                    f"https://raw.githubusercontent.com/example/project/{HEAD}/"
                    ".project/progress.json"
                ),
            ),
        ),
    )


def test_parse_repository_address_accepts_url_and_slug() -> None:
    assert parse_repository_address("example/project").full_name == "example/project"
    assert (
        parse_repository_address("https://github.com/example/project.git").full_name
        == "example/project"
    )


def test_parse_repository_address_rejects_other_hosts() -> None:
    with pytest.raises(ValueError):
        parse_repository_address("https://example.com/example/project")


def test_extract_gitingest_files_uses_file_blocks() -> None:
    files = extract_gitingest_files(DIGEST_CONTENT)
    assert files["README.md"].startswith("# Example")
    assert json.loads(files[".project/progress.json"])["schema_version"] == 1
    assert "requires-python" in files["pyproject.toml"]


def test_collect_public_evidence_uses_exact_commit_and_facts() -> None:
    bundle = collect_public_evidence(
        "https://github.com/example/project",
        client=FakeClient(),
        repository_reader=fake_reader,
        token="api-only-token",
    )
    assert bundle.source_commit == HEAD
    assert bundle.source_url.endswith(HEAD)
    assert bundle.checked_at.endswith("Z")
    assert [item.path for item in bundle.important_files] == [
        ".project/progress.json",
        "pyproject.toml",
        "README.md",
    ]

    files = {item.path: item for item in bundle.important_files}
    progress_file = files[".project/progress.json"]
    assert progress_file.collection_method == "exact_public_file"
    assert progress_file.source_commit == HEAD
    assert progress_file.source_url.endswith(f"{HEAD}/.project/progress.json")

    readme = files["README.md"]
    assert readme.collection_method == "gitingest"
    assert readme.source_commit == HEAD
    assert readme.source_url == (
        f"https://github.com/example/project/blob/{HEAD}/README.md"
    )

    manifest = files["pyproject.toml"]
    assert manifest.role == "technology_manifest"
    assert manifest.source_url == (
        f"https://github.com/example/project/blob/{HEAD}/pyproject.toml"
    )

    assert bundle.progress_records[0].path == ".project/progress.json"
    assert bundle.progress_records[0].authority_rank == 1
    assert bundle.progress_records[0].valid_json is True
    assert bundle.progress_records[0].stage_count == 1
    assert bundle.progress_records[0].overall_enabled is False
    assert [item.name for item in bundle.repository_languages] == [
        "Python",
        "SourcePawn",
        "C++",
        "Pawn",
        "Shell",
        "PowerShell",
    ]
    assert [item.percentage for item in bundle.repository_languages] == [
        74.7,
        11.6,
        8.6,
        2.3,
        1.8,
        1.0,
    ]
    assert bundle.repository_languages[0].source_url == (
        "https://api.github.com/repos/example/project/languages"
    )
    assert bundle.repository_languages[0].source_commit == HEAD
    assert bundle.open_issues[0].number == 3
    assert bundle.open_pull_requests[0].draft is True


def test_collect_public_evidence_keeps_repository_reader_unauthenticated() -> None:
    seen: dict[str, str | None] = {}

    def token_reader(source: str, *, token=None, include_patterns=None):
        seen["token"] = token
        return fake_reader(
            source,
            token=token,
            include_patterns=include_patterns,
        )

    collect_public_evidence(
        "example/project",
        client=FakeClient(),
        repository_reader=token_reader,
        token="api-only-token",
    )

    assert seen["token"] is None


def test_collect_public_evidence_prefers_project_reader_token_env(monkeypatch) -> None:
    seen: dict[str, str | None] = {}

    class TokenClient(FakeClient):
        def __init__(self, *, token: str | None = None) -> None:
            super().__init__()
            seen["token"] = token

    monkeypatch.setattr(evidence_module, "GitHubRestClient", TokenClient)
    monkeypatch.setenv("GITHUB_TOKEN", "github-token")
    monkeypatch.setenv("PROJECT_READER_GITHUB_TOKEN", "project-reader-token")

    collect_public_evidence(
        "example/project",
        repository_reader=fake_reader,
    )

    assert seen["token"] == "project-reader-token"


def test_checked_at_is_recorded_after_live_queues(monkeypatch) -> None:
    client = FakeClient()

    class OrderedDateTime:
        @classmethod
        def now(cls, tz):
            assert client.calls == ["languages", "issues", "pull_requests"]
            return RealDateTime(2026, 7, 28, 12, 30, tzinfo=tz)

    monkeypatch.setattr(evidence_module, "datetime", OrderedDateTime)
    bundle = collect_public_evidence(
        "example/project",
        client=client,
        repository_reader=fake_reader,
    )
    assert bundle.checked_at == "2026-07-28T12:30:00Z"


def test_collect_public_evidence_handles_single_language_repository() -> None:
    class SingleLanguageClient(FakeClient):
        def languages(self, address):
            self.calls.append("languages")
            return {"Python": 120}

    bundle = collect_public_evidence(
        "example/project",
        client=SingleLanguageClient(),
        repository_reader=fake_reader,
    )

    assert [(item.name, item.bytes, item.percentage) for item in bundle.repository_languages] == [
        ("Python", 120, 100.0)
    ]


def test_collect_public_evidence_handles_empty_language_result() -> None:
    class EmptyLanguageClient(FakeClient):
        def languages(self, address):
            self.calls.append("languages")
            return {}

    bundle = collect_public_evidence(
        "example/project",
        client=EmptyLanguageClient(),
        repository_reader=fake_reader,
    )

    assert bundle.repository_languages == ()


def test_collect_public_evidence_rejects_private_repository() -> None:
    with pytest.raises(EvidenceCollectionError, match="public repositories"):
        collect_public_evidence(
            "example/project",
            client=FakeClient(private=True),
            repository_reader=fake_reader,
        )


def test_collect_public_evidence_rejects_oversized_repository() -> None:
    with pytest.raises(RepositorySizeLimitError, match="size limit"):
        collect_public_evidence(
            "example/project",
            client=FakeClient(size=501),
            repository_reader=fake_reader,
            max_repository_size_kb=500,
        )


def test_collect_public_evidence_rejects_invalid_size_limit() -> None:
    with pytest.raises(ValueError, match="size limit"):
        collect_public_evidence(
            "example/project",
            client=FakeClient(),
            repository_reader=fake_reader,
            max_repository_size_kb=0,
        )


def test_repository_reader_failure_is_controlled() -> None:
    def failed_reader(*args, **kwargs):
        raise RuntimeError("network failed")

    with pytest.raises(
        EvidenceCollectionError, match="Could not read repository content"
    ):
        collect_public_evidence(
            "example/project",
            client=FakeClient(),
            repository_reader=failed_reader,
        )


def test_bundle_json_is_structured_and_stable() -> None:
    bundle = collect_public_evidence(
        "example/project",
        client=FakeClient(),
        repository_reader=fake_reader,
    )
    payload = bundle.to_dict()
    assert payload["schema_version"] == 1
    assert payload["repository"] == "example/project"
    assert isinstance(payload["repository_languages"], list)
    assert isinstance(payload["important_files"], list)
    assert payload["progress_records"][0]["kind"] == "machine_progress"
    files = {item["path"]: item for item in payload["important_files"]}
    assert files[".project/progress.json"]["collection_method"] == "exact_public_file"
    assert files["pyproject.toml"]["role"] == "technology_manifest"
    assert json.loads(bundle.to_json()) == payload
