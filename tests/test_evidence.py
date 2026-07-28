from datetime import datetime as RealDateTime
import importlib
import json

import pytest

from project_reader.evidence import (
    EvidenceCollectionError,
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
File: src/app.py
{SEPARATOR}
print("hello")

"""


class FakeClient:
    def __init__(self, *, private: bool = False) -> None:
        self.private = private
        self.calls: list[str] = []

    def repository(self, address):
        return {"private": self.private, "default_branch": "main"}

    def commit(self, address, ref):
        assert ref == "main"
        return {"sha": HEAD}

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
    return RepositoryDigest(
        summary=f"Repository: example/project\nCommit: {HEAD}",
        tree="Directory structure:\n├── README.md\n└── .project/progress.json",
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
    assert parse_repository_address("https://github.com/example/project.git").full_name == "example/project"


def test_parse_repository_address_rejects_other_hosts() -> None:
    with pytest.raises(ValueError):
        parse_repository_address("https://example.com/example/project")


def test_extract_gitingest_files_uses_file_blocks() -> None:
    files = extract_gitingest_files(DIGEST_CONTENT)
    assert files["README.md"].startswith("# Example")
    assert json.loads(files[".project/progress.json"])["schema_version"] == 1


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
    assert [item.path for item in bundle.important_files] == [".project/progress.json", "README.md"]

    progress_file = bundle.important_files[0]
    assert progress_file.collection_method == "exact_public_file"
    assert progress_file.source_commit == HEAD
    assert progress_file.source_url.endswith(f"{HEAD}/.project/progress.json")

    readme = bundle.important_files[1]
    assert readme.collection_method == "gitingest"
    assert readme.source_commit == HEAD
    assert readme.source_url == f"https://github.com/example/project/blob/{HEAD}/README.md"

    assert bundle.progress_records[0].path == ".project/progress.json"
    assert bundle.progress_records[0].authority_rank == 1
    assert bundle.progress_records[0].valid_json is True
    assert bundle.progress_records[0].stage_count == 1
    assert bundle.progress_records[0].overall_enabled is False
    assert bundle.open_issues[0].number == 3
    assert bundle.open_pull_requests[0].draft is True


def test_checked_at_is_recorded_after_live_queues(monkeypatch) -> None:
    client = FakeClient()

    class OrderedDateTime:
        @classmethod
        def now(cls, tz):
            assert client.calls == ["issues", "pull_requests"]
            return RealDateTime(2026, 7, 28, 12, 30, tzinfo=tz)

    monkeypatch.setattr(evidence_module, "datetime", OrderedDateTime)
    bundle = collect_public_evidence(
        "example/project",
        client=client,
        repository_reader=fake_reader,
    )
    assert bundle.checked_at == "2026-07-28T12:30:00Z"


def test_collect_public_evidence_rejects_private_repository() -> None:
    with pytest.raises(EvidenceCollectionError, match="public repositories"):
        collect_public_evidence(
            "example/project",
            client=FakeClient(private=True),
            repository_reader=fake_reader,
        )


def test_repository_reader_failure_is_controlled() -> None:
    def failed_reader(*args, **kwargs):
        raise RuntimeError("network failed")

    with pytest.raises(EvidenceCollectionError, match="Could not read repository content"):
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
    payload = json.loads(bundle.to_json())
    assert payload["schema_version"] == 1
    assert payload["repository"] == "example/project"
    assert payload["progress_records"][0]["kind"] == "machine_progress"
    assert payload["important_files"][0]["collection_method"] == "exact_public_file"
