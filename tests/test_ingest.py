import importlib
from urllib.error import URLError

import pytest

from project_reader.ingest import RepositoryReadError, read_repository


ingest_module = importlib.import_module("project_reader.ingest")
HEAD = "a" * 40


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self) -> bytes:
        return b'{"schema_version": 1, "stages": []}'


def test_exact_hidden_public_file_is_recovered(monkeypatch) -> None:
    monkeypatch.setattr(
        ingest_module,
        "ingest",
        lambda source, token=None, include_patterns=None: (
            "Repository: example/project",
            "Directory structure:\nREADME.md",
            "================================================\n"
            "File: README.md\n"
            "================================================\n"
            "# Example",
        ),
    )
    requested_urls: list[str] = []

    def fake_urlopen(request, timeout):
        requested_urls.append(request.full_url)
        return FakeResponse()

    monkeypatch.setattr(ingest_module, "urlopen", fake_urlopen)

    digest = read_repository(
        f"https://github.com/example/project/tree/{HEAD}",
        include_patterns={"README.md", ".project/progress.json"},
    )

    assert "File: .project/progress.json" in digest.content
    assert '"schema_version": 1' in digest.content
    assert requested_urls == [
        f"https://raw.githubusercontent.com/example/project/{HEAD}/.project/progress.json"
    ]
    assert digest.file_provenance[0].path == ".project/progress.json"
    assert digest.file_provenance[0].collection_method == "exact_public_file"
    assert digest.file_provenance[0].source_url == requested_urls[0]


def test_wildcard_patterns_are_left_to_gitingest(monkeypatch) -> None:
    monkeypatch.setattr(
        ingest_module,
        "ingest",
        lambda source, token=None, include_patterns=None: ("summary", "tree", "content"),
    )
    monkeypatch.setattr(
        ingest_module,
        "urlopen",
        lambda request, timeout: (_ for _ in ()).throw(AssertionError("unexpected raw fetch")),
    )

    digest = read_repository(
        f"https://github.com/example/project/tree/{HEAD}",
        include_patterns={"docs/**/*status*"},
    )

    assert digest.content == "content"
    assert digest.file_provenance == ()


def test_gitingest_failure_is_controlled(monkeypatch) -> None:
    monkeypatch.setattr(
        ingest_module,
        "ingest",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("clone failed")),
    )

    with pytest.raises(RepositoryReadError, match="Gitingest"):
        read_repository("https://github.com/example/project")


def test_exact_file_network_failure_is_controlled(monkeypatch) -> None:
    monkeypatch.setattr(
        ingest_module,
        "ingest",
        lambda source, token=None, include_patterns=None: ("summary", "tree", ""),
    )
    monkeypatch.setattr(
        ingest_module,
        "urlopen",
        lambda request, timeout: (_ for _ in ()).throw(URLError("offline")),
    )

    with pytest.raises(RepositoryReadError, match=r"\.project/progress\.json"):
        read_repository(
            f"https://github.com/example/project/tree/{HEAD}",
            include_patterns={".project/progress.json"},
        )
