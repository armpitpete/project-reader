from __future__ import annotations

from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from gitingest import ingest


_SEPARATOR = "=" * 48


class RepositoryReadError(RuntimeError):
    """Raised when repository content cannot be read safely."""


@dataclass(frozen=True)
class RepositoryFileProvenance:
    path: str
    collection_method: str
    source_url: str


@dataclass(frozen=True)
class RepositoryDigest:
    summary: str
    tree: str
    content: str
    file_provenance: tuple[RepositoryFileProvenance, ...] = ()


def _exact_public_github_files(
    source: str,
    include_patterns: set[str] | None,
) -> tuple[tuple[str, str], ...]:
    """Return exact public file paths that can be fetched outside Gitingest."""
    if not include_patterns:
        return ()

    parsed = urlparse(source)
    parts = parsed.path.strip("/").split("/")
    if parsed.scheme != "https" or parsed.hostname != "github.com":
        return ()
    if len(parts) != 4 or parts[2] != "tree":
        return ()

    owner, repository, _, ref = parts
    files: list[tuple[str, str]] = []
    for pattern in sorted(include_patterns):
        if not pattern or any(marker in pattern for marker in "*?["):
            continue
        quoted_path = "/".join(quote(part, safe="") for part in pattern.split("/"))
        raw_url = (
            "https://raw.githubusercontent.com/"
            f"{quote(owner, safe='')}/{quote(repository, safe='')}/{quote(ref, safe='')}/"
            f"{quoted_path}"
        )
        files.append((pattern, raw_url))
    return tuple(files)


def _append_missing_exact_files(
    source: str,
    content: str,
    include_patterns: set[str] | None,
) -> tuple[str, tuple[RepositoryFileProvenance, ...]]:
    """Add exact public files that Gitingest omitted, including dot-directories."""
    result = content.rstrip()
    provenance: list[RepositoryFileProvenance] = []
    for path, raw_url in _exact_public_github_files(source, include_patterns):
        if f"\nFile: {path}\n" in f"\n{result}\n":
            continue

        request = Request(
            raw_url,
            headers={"User-Agent": "project-reader-ingest/0.3"},
        )
        try:
            with urlopen(request, timeout=20.0) as response:
                text = response.read().decode("utf-8")
        except HTTPError as error:
            if error.code == 404:
                continue
            raise RepositoryReadError(f"Could not read exact public file {path}") from error
        except (URLError, TimeoutError, UnicodeDecodeError) as error:
            raise RepositoryReadError(f"Could not read exact public file {path}") from error

        block = f"{_SEPARATOR}\nFile: {path}\n{_SEPARATOR}\n{text.rstrip()}"
        result = f"{result}\n\n{block}" if result else block
        provenance.append(
            RepositoryFileProvenance(
                path=path,
                collection_method="exact_public_file",
                source_url=raw_url,
            )
        )

    return result, tuple(provenance)


def read_repository(
    source: str,
    *,
    token: str | None = None,
    include_patterns: set[str] | None = None,
) -> RepositoryDigest:
    """Read a repository through Gitingest without interpreting project status."""
    if not source.strip():
        raise ValueError("A repository URL or local path is required")

    try:
        summary, tree, content = ingest(
            source,
            token=token,
            include_patterns=include_patterns,
        )
    except Exception as error:
        raise RepositoryReadError("Gitingest could not read repository content") from error

    content, file_provenance = _append_missing_exact_files(
        source,
        content,
        include_patterns,
    )
    return RepositoryDigest(
        summary=summary,
        tree=tree,
        content=content,
        file_provenance=file_provenance,
    )
