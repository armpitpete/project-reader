from __future__ import annotations

from dataclasses import dataclass

from gitingest import ingest


@dataclass(frozen=True)
class RepositoryDigest:
    summary: str
    tree: str
    content: str


def read_repository(
    source: str,
    *,
    token: str | None = None,
    include_patterns: set[str] | None = None,
) -> RepositoryDigest:
    """Read a repository through Gitingest without interpreting project status."""
    if not source.strip():
        raise ValueError("A repository URL or local path is required")

    summary, tree, content = ingest(
        source,
        token=token,
        include_patterns=include_patterns,
    )
    return RepositoryDigest(summary=summary, tree=tree, content=content)
