from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Callable, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from .ingest import RepositoryDigest, read_repository


_GITHUB_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")
_SEPARATOR = "=" * 48
_FILE_BLOCK = re.compile(
    rf"{re.escape(_SEPARATOR)}\nFile: (?P<path>[^\n]+)\n"
    rf"{re.escape(_SEPARATOR)}\n(?P<content>.*?)(?=\n{re.escape(_SEPARATOR)}\nFile: |\Z)",
    re.DOTALL,
)
_PROGRESS_RULES = (
    (".project/progress.json", "machine_progress", 1),
    ("PROJECT_STATUS.md", "project_status", 2),
    ("STATUS.md", "project_status", 2),
    ("ROADMAP.md", "roadmap", 3),
    ("MILESTONES.md", "milestones", 3),
)
_IMPORTANT_NAMES = {
    "README.md": "project_overview",
    "CONTRIBUTING.md": "contribution_guide",
    "PROJECT_STATUS.md": "project_status",
    "STATUS.md": "project_status",
    "ROADMAP.md": "roadmap",
    "MILESTONES.md": "milestones",
}
_MAX_IMPORTANT_FILE_CHARS = 30_000


class EvidenceCollectionError(RuntimeError):
    """Raised when public evidence cannot be collected safely."""


@dataclass(frozen=True)
class RepositoryAddress:
    owner: str
    name: str

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"

    @property
    def url(self) -> str:
        return f"https://github.com/{self.full_name}"


@dataclass(frozen=True)
class WorkItemFact:
    number: int
    title: str
    url: str
    created_at: str
    updated_at: str
    labels: tuple[str, ...] = ()
    draft: bool | None = None


@dataclass(frozen=True)
class ImportantFileFact:
    path: str
    role: str
    sha256: str
    characters: int
    content: str
    truncated: bool


@dataclass(frozen=True)
class ProgressRecordFact:
    path: str
    kind: str
    authority_rank: int
    sha256: str
    valid_json: bool | None = None
    schema_version: int | str | None = None
    stage_count: int | None = None
    overall_enabled: bool | None = None


@dataclass(frozen=True)
class PublicEvidenceBundle:
    schema_version: int
    checked_at: str
    repository: str
    repository_url: str
    default_branch: str
    source_commit: str
    source_url: str
    gitingest_summary: str
    important_files: tuple[ImportantFileFact, ...]
    progress_records: tuple[ProgressRecordFact, ...]
    open_issues: tuple[WorkItemFact, ...]
    open_pull_requests: tuple[WorkItemFact, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


class PublicGitHubClient(Protocol):
    def repository(self, address: RepositoryAddress) -> dict[str, Any]: ...
    def commit(self, address: RepositoryAddress, ref: str) -> dict[str, Any]: ...
    def open_issues(self, address: RepositoryAddress) -> list[dict[str, Any]]: ...
    def open_pull_requests(self, address: RepositoryAddress) -> list[dict[str, Any]]: ...


class GitHubRestClient:
    """Small read-only GitHub REST client for public repository facts."""

    def __init__(self, *, token: str | None = None, timeout: float = 20.0) -> None:
        self.token = token
        self.timeout = timeout

    def _request(self, url: str) -> tuple[Any, dict[str, str]]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "project-reader-evidence/0.3",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(url, headers=headers)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
                response_headers = {key.lower(): value for key, value in response.headers.items()}
                return payload, response_headers
        except HTTPError as error:
            raise EvidenceCollectionError(f"GitHub returned HTTP {error.code} for {url}") from error
        except (URLError, TimeoutError, json.JSONDecodeError) as error:
            raise EvidenceCollectionError(f"Could not read GitHub evidence from {url}") from error

    def _get(self, path: str) -> Any:
        payload, _ = self._request(f"https://api.github.com{path}")
        return payload

    def _all(self, path: str) -> list[dict[str, Any]]:
        url = f"https://api.github.com{path}"
        items: list[dict[str, Any]] = []
        while url:
            payload, headers = self._request(url)
            if not isinstance(payload, list):
                raise EvidenceCollectionError(f"Expected a list from {url}")
            items.extend(item for item in payload if isinstance(item, dict))
            url = _next_link(headers.get("link", ""))
        return items

    def repository(self, address: RepositoryAddress) -> dict[str, Any]:
        payload = self._get(f"/repos/{address.full_name}")
        if not isinstance(payload, dict):
            raise EvidenceCollectionError("Repository metadata was not an object")
        return payload

    def commit(self, address: RepositoryAddress, ref: str) -> dict[str, Any]:
        payload = self._get(f"/repos/{address.full_name}/commits/{quote(ref, safe='')}")
        if not isinstance(payload, dict):
            raise EvidenceCollectionError("Commit metadata was not an object")
        return payload

    def open_issues(self, address: RepositoryAddress) -> list[dict[str, Any]]:
        issues = self._all(f"/repos/{address.full_name}/issues?state=open&per_page=100")
        return [item for item in issues if "pull_request" not in item]

    def open_pull_requests(self, address: RepositoryAddress) -> list[dict[str, Any]]:
        return self._all(f"/repos/{address.full_name}/pulls?state=open&per_page=100")


def parse_repository_address(source: str) -> RepositoryAddress:
    value = source.strip()
    if not value:
        raise ValueError("A public GitHub repository address is required")

    if "://" not in value:
        parts = value.removesuffix(".git").strip("/").split("/")
    else:
        parsed = urlparse(value)
        if parsed.scheme != "https" or parsed.hostname not in {"github.com", "www.github.com"}:
            raise ValueError("Only https://github.com public repository addresses are supported")
        parts = parsed.path.removesuffix(".git").strip("/").split("/")

    if len(parts) != 2 or not all(_GITHUB_NAME.fullmatch(part or "") for part in parts):
        raise ValueError("Use a repository address in the form owner/name or https://github.com/owner/name")
    return RepositoryAddress(parts[0], parts[1])


def _next_link(value: str) -> str:
    for item in value.split(","):
        sections = [section.strip() for section in item.split(";")]
        if len(sections) >= 2 and sections[1] == 'rel="next"':
            return sections[0].strip("<>")
    return ""


def extract_gitingest_files(content: str) -> dict[str, str]:
    """Return path-to-content mappings from Gitingest's documented file blocks."""
    return {
        match.group("path").strip(): match.group("content").rstrip()
        for match in _FILE_BLOCK.finditer(content)
    }


def _file_role(path: str) -> str | None:
    if path == ".project/progress.json":
        return "machine_progress"
    name = Path(path).name
    if name in _IMPORTANT_NAMES:
        return _IMPORTANT_NAMES[name]
    lower = path.lower()
    if lower.startswith("docs/") and ("status" in lower or "roadmap" in lower or "milestone" in lower):
        return "supporting_progress"
    return None


def _important_file(path: str, role: str, text: str) -> ImportantFileFact:
    encoded = text.encode("utf-8")
    truncated = len(text) > _MAX_IMPORTANT_FILE_CHARS
    return ImportantFileFact(
        path=path,
        role=role,
        sha256=hashlib.sha256(encoded).hexdigest(),
        characters=len(text),
        content=text[:_MAX_IMPORTANT_FILE_CHARS],
        truncated=truncated,
    )


def _progress_record(file: ImportantFileFact, original_text: str) -> ProgressRecordFact | None:
    match = next((rule for rule in _PROGRESS_RULES if file.path == rule[0]), None)
    if match is None and file.role != "supporting_progress":
        return None

    kind = match[1] if match else "supporting_progress"
    rank = match[2] if match else 4
    valid_json: bool | None = None
    schema_version: int | str | None = None
    stage_count: int | None = None
    overall_enabled: bool | None = None

    if file.path.endswith(".json"):
        try:
            data = json.loads(original_text)
            valid_json = True
        except json.JSONDecodeError:
            valid_json = False
        else:
            if isinstance(data, dict):
                schema_version = data.get("schema_version")
                stages = data.get("stages")
                if isinstance(stages, list):
                    stage_count = len(stages)
                overall = data.get("overall")
                if isinstance(overall, dict) and isinstance(overall.get("enabled"), bool):
                    overall_enabled = overall["enabled"]

    return ProgressRecordFact(
        path=file.path,
        kind=kind,
        authority_rank=rank,
        sha256=file.sha256,
        valid_json=valid_json,
        schema_version=schema_version,
        stage_count=stage_count,
        overall_enabled=overall_enabled,
    )


def _work_item(item: dict[str, Any], *, pull_request: bool) -> WorkItemFact:
    labels = tuple(
        label["name"]
        for label in item.get("labels", [])
        if isinstance(label, dict) and isinstance(label.get("name"), str)
    )
    return WorkItemFact(
        number=int(item["number"]),
        title=str(item.get("title", "")),
        url=str(item.get("html_url", "")),
        created_at=str(item.get("created_at", "")),
        updated_at=str(item.get("updated_at", "")),
        labels=labels,
        draft=bool(item.get("draft", False)) if pull_request else None,
    )


def collect_public_evidence(
    source: str,
    *,
    client: PublicGitHubClient | None = None,
    repository_reader: Callable[..., RepositoryDigest] = read_repository,
    token: str | None = None,
    checked_at: str | None = None,
) -> PublicEvidenceBundle:
    """Collect facts for one public GitHub repository without interpreting them."""
    address = parse_repository_address(source)
    active_client = client or GitHubRestClient(token=token or os.getenv("GITHUB_TOKEN"))

    repository = active_client.repository(address)
    if repository.get("private") is not False:
        raise EvidenceCollectionError("Only public repositories are supported in v0.3")

    default_branch = repository.get("default_branch")
    if not isinstance(default_branch, str) or not default_branch:
        raise EvidenceCollectionError("The repository has no readable default branch")

    commit = active_client.commit(address, default_branch)
    source_commit = commit.get("sha")
    if not isinstance(source_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise EvidenceCollectionError("GitHub did not return a full source commit")

    source_url = f"{address.url}/tree/{source_commit}"
    digest = repository_reader(source_url, token=token or os.getenv("GITHUB_TOKEN"))
    files = extract_gitingest_files(digest.content)

    important = tuple(
        sorted(
            (
                _important_file(path, role, text)
                for path, text in files.items()
                if (role := _file_role(path)) is not None
            ),
            key=lambda item: item.path.lower(),
        )
    )
    progress = tuple(
        sorted(
            (record for file in important if (record := _progress_record(file, files[file.path])) is not None),
            key=lambda item: (item.authority_rank, item.path.lower()),
        )
    )

    timestamp = checked_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    issues = tuple(
        _work_item(item, pull_request=False)
        for item in sorted(active_client.open_issues(address), key=lambda value: int(value["number"]))
    )
    pull_requests = tuple(
        _work_item(item, pull_request=True)
        for item in sorted(active_client.open_pull_requests(address), key=lambda value: int(value["number"]))
    )

    return PublicEvidenceBundle(
        schema_version=1,
        checked_at=timestamp,
        repository=address.full_name,
        repository_url=address.url,
        default_branch=default_branch,
        source_commit=source_commit,
        source_url=source_url,
        gitingest_summary=digest.summary,
        important_files=important,
        progress_records=progress,
        open_issues=issues,
        open_pull_requests=pull_requests,
    )


def write_evidence_bundle(bundle: PublicEvidenceBundle, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(bundle.to_json(), encoding="utf-8")
