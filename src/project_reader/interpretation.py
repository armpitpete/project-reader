from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
import json
from pathlib import Path
import re
import tomllib
from typing import Any, Mapping
from urllib.parse import unquote, urlparse

_SHA = re.compile(r"^[0-9a-f]{40}$")
_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_TASK = re.compile(r"^\s*[-*]\s+\[(?P<mark>[ xX])\]\s+(?P<label>.+?)\s*$")
_PURPOSE_ACTION = re.compile(
    r"\b(help|helps|helping|allow|allows|enable|enables|let|lets|provide|provides|"
    r"offer|offers|create|creates|build|builds|track|tracks|collect|collects|"
    r"explain|explains|turn|turns|generate|generates|manage|manages|report|"
    r"reports|analyse|analyses|analyze|analyzes)\b",
    re.IGNORECASE,
)
_PURPOSE_NOUN = re.compile(
    r"\b(tool|app|application|service|library|project|system|platform|engine|"
    r"website|dashboard|repository|repositories|workflow|reader|collector)\b",
    re.IGNORECASE,
)
_PURPOSE_NEGATIVE = re.compile(
    r"\b(support|sponsor|sponsorship|donate|donation|fund|funding|copyright|"
    r"licen[cs]e|warranty|disclaimer|security|contribut|warning|caution|notice|"
    r"ko-fi|patreon)\b",
    re.IGNORECASE,
)


class InterpretationError(ValueError):
    """Raised when one v0.3 evidence bundle cannot be interpreted safely."""


class StatementKind(StrEnum):
    FACT = "fact"
    INTERPRETATION = "interpretation"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class CandidateStatement:
    key: str
    topic: str
    text: str
    kind: StatementKind
    basis: str
    evidence_keys: tuple[str, ...] = ()
    owner_authority: bool = False


@dataclass(frozen=True)
class AuthorityRecord:
    path: str
    kind: str
    authority_rank: int
    source_url: str
    source_commit: str
    valid: bool | None
    primary: bool
    declared_authority: str | None = None


@dataclass(frozen=True)
class EvidenceReference:
    key: str
    path: str
    source_url: str
    source_commit: str
    role: str
    authority_rank: int | None
    usable: bool
    exclusion_reason: str | None = None


@dataclass(frozen=True)
class Conflict:
    key: str
    topic: str
    description: str
    evidence_keys: tuple[str, ...]
    resolution: str


@dataclass(frozen=True)
class Refusal:
    topic: str
    reason: str


@dataclass(frozen=True)
class InterpretationBundle:
    schema_version: int
    source_evidence_schema_version: int
    repository: str
    repository_url: str
    source_commit: str
    evidence_checked_at: str
    purpose: CandidateStatement
    owner_authority_records: tuple[AuthorityRecord, ...]
    done: tuple[CandidateStatement, ...]
    remaining: tuple[CandidateStatement, ...]
    technologies: tuple[CandidateStatement, ...]
    uncertainties: tuple[CandidateStatement, ...]
    conflicts: tuple[Conflict, ...]
    evidence: tuple[EvidenceReference, ...]
    refusals: tuple[Refusal, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


@dataclass(frozen=True)
class _Work:
    label: str
    state: str
    rank: int
    path: str
    detail: str


def _key(path: str) -> str:
    return f"file:{path}"


def _queue_key(kind: str, number: int) -> str:
    return f"{kind}:{number}"


def _payload(value: Mapping[str, Any] | Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if callable(getattr(value, "to_dict", None)):
        result = value.to_dict()
        if isinstance(result, dict):
            return result
    raise InterpretationError("Expected one v0.3 evidence bundle")


def _validate_queue(data: dict[str, Any], name: str, segment: str) -> None:
    seen: set[int] = set()
    for item in data[name]:
        if not isinstance(item, dict):
            raise InterpretationError(f"The evidence bundle contains an invalid {name} item")
        number = item.get("number")
        url = item.get("url")
        if not isinstance(number, int) or isinstance(number, bool) or number <= 0:
            raise InterpretationError(f"The evidence bundle contains an invalid {name} number")
        if number in seen:
            raise InterpretationError(f"The evidence bundle contains a duplicate {name} number")
        seen.add(number)
        expected = f"{data['repository_url']}/{segment}/{number}"
        if url != expected:
            raise InterpretationError(
                f"The evidence bundle contains an uninspectable {name} URL"
            )


def _validate(data: dict[str, Any]) -> None:
    if data.get("schema_version") != 1:
        raise InterpretationError(
            "Automatic Interpretation Contract v0.4 requires evidence schema version 1"
        )
    repository = data.get("repository")
    if not isinstance(repository, str) or not _REPOSITORY.fullmatch(repository):
        raise InterpretationError("The evidence bundle has no repository name")
    if data.get("repository_url") != f"https://github.com/{repository}":
        raise InterpretationError(
            "The evidence bundle has no supported public repository URL"
        )
    if not isinstance(data.get("source_commit"), str) or not _SHA.fullmatch(
        data["source_commit"]
    ):
        raise InterpretationError("The evidence bundle has no exact source commit")
    if not isinstance(data.get("checked_at"), str) or not data["checked_at"].strip():
        raise InterpretationError("The evidence bundle has no live-queue check time")
    for name in (
        "important_files",
        "progress_records",
        "open_issues",
        "open_pull_requests",
    ):
        if not isinstance(data.get(name), list):
            raise InterpretationError(
                f"The evidence bundle has no {name.replace('_', '-')} list"
            )
    _validate_queue(data, "open_issues", "issues")
    _validate_queue(data, "open_pull_requests", "pull")


def _plain(text: str) -> str:
    text = re.sub(r"!\[[^]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[`*_]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _normal(text: str) -> str:
    return _plain(text).casefold().rstrip(".:")


def _paragraphs(markdown: str) -> tuple[str, ...]:
    paragraphs: list[str] = []
    current: list[str] = []
    fenced = False
    for raw in markdown.splitlines():
        line = raw.strip()
        if line.startswith(("```", "~~~")):
            fenced = not fenced
            continue
        if fenced:
            continue
        excluded = (
            not line
            or line.startswith(("#", "|", ">"))
            or bool(re.match(r"^[-*+]\s+", line))
            or bool(re.match(r"^\d+[.)]\s+", line))
        )
        if excluded:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(line)
    if current:
        paragraphs.append(" ".join(current))
    return tuple(
        value
        for raw in paragraphs
        if 20 <= len(value := _plain(raw)) <= 500
    )


def _purpose_score(text: str) -> int:
    score = 0
    if _PURPOSE_ACTION.search(text):
        score += 4
    if _PURPOSE_NOUN.search(text):
        score += 3
    if re.search(r"\b(for|to)\b", text, re.IGNORECASE):
        score += 2
    if _PURPOSE_NEGATIVE.search(text):
        score -= 8
    return score


def _purpose_paragraph(markdown: str) -> str | None:
    ranked = [
        (_purpose_score(text), -index, text)
        for index, text in enumerate(_paragraphs(markdown))
    ]
    if not ranked:
        return None
    score, _, text = max(ranked)
    return text if score >= 4 else None


def _valid_file_path(path: str) -> bool:
    parts = path.split("/")
    return bool(path) and not path.startswith("/") and all(
        part not in {"", ".", ".."} for part in parts
    )


def _source_url_matches(
    repository: str, source_commit: str, path: str, source_url: Any
) -> bool:
    if not _valid_file_path(path) or not isinstance(source_url, str):
        return False
    parsed = urlparse(source_url)
    if parsed.scheme != "https" or parsed.query or parsed.fragment:
        return False
    parts = [unquote(part) for part in parsed.path.strip("/").split("/")]
    owner, name = repository.split("/", 1)
    if parsed.hostname in {"github.com", "www.github.com"}:
        if len(parts) < 5 or parts[2] != "blob":
            return False
        url_owner, url_name, _, url_commit, *url_path = parts
    elif parsed.hostname == "raw.githubusercontent.com":
        if len(parts) < 4:
            return False
        url_owner, url_name, url_commit, *url_path = parts
    else:
        return False
    return (
        url_owner.casefold() == owner.casefold()
        and url_name.casefold() == name.casefold()
        and url_commit == source_commit
        and "/".join(url_path) == path
    )


def _files(
    data: dict[str, Any],
) -> tuple[
    dict[str, dict[str, Any]],
    tuple[EvidenceReference, ...],
    list[Conflict],
    list[CandidateStatement],
]:
    source_commit = data["source_commit"]
    ranks = {
        item.get("path"): item.get("authority_rank")
        for item in data["progress_records"]
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }
    usable: dict[str, dict[str, Any]] = {}
    references: list[EvidenceReference] = []
    conflicts: list[Conflict] = []
    unknowns: list[CandidateStatement] = []
    seen: set[str] = set()

    for index, raw in enumerate(data["important_files"]):
        if not isinstance(raw, dict) or not isinstance(raw.get("path"), str):
            continue
        path = raw["path"].strip()
        if not path or path in seen:
            continue
        seen.add(path)
        commit = raw.get("source_commit")
        url = raw.get("source_url")
        exact = commit == source_commit and _source_url_matches(
            data["repository"], source_commit, path, url
        )
        reason = None
        if commit != source_commit:
            reason = "source commit does not match the bundle"
        elif not _source_url_matches(data["repository"], source_commit, path, url):
            reason = "source URL does not match the bundle repository, commit, and path"
        references.append(
            EvidenceReference(
                key=_key(path),
                path=path,
                source_url=str(url or ""),
                source_commit=str(commit or ""),
                role=str(raw.get("role", "unknown")),
                authority_rank=(
                    ranks.get(path) if isinstance(ranks.get(path), int) else None
                ),
                usable=exact,
                exclusion_reason=reason,
            )
        )
        if not exact:
            conflicts.append(
                Conflict(
                    key=f"stale:{path}",
                    topic="stale_evidence",
                    description=f"{path} {reason}.",
                    evidence_keys=(_key(path),),
                    resolution="excluded from interpretation",
                )
            )
            continue
        usable[path] = raw
        if raw.get("truncated") is True:
            unknowns.append(
                CandidateStatement(
                    key=f"uncertainty:truncated:{index}",
                    topic="evidence",
                    text=f"Only part of {path} is present in the evidence bundle.",
                    kind=StatementKind.UNKNOWN,
                    basis="The collector marked this file as truncated.",
                    evidence_keys=(_key(path),),
                )
            )
    return (
        usable,
        tuple(sorted(references, key=lambda item: item.path.casefold())),
        conflicts,
        unknowns,
    )


def _queue_references(
    data: dict[str, Any],
) -> tuple[tuple[EvidenceReference, ...], tuple[str, ...]]:
    references: list[EvidenceReference] = []
    keys: list[str] = []
    for name, kind, segment, role in (
        ("open_issues", "issue", "issues", "open_issue"),
        ("open_pull_requests", "pull_request", "pull", "open_pull_request"),
    ):
        for item in data[name]:
            number = item["number"]
            key = _queue_key(kind, number)
            keys.append(key)
            references.append(
                EvidenceReference(
                    key=key,
                    path=f"{segment}/{number}",
                    source_url=item["url"],
                    source_commit="",
                    role=role,
                    authority_rank=None,
                    usable=True,
                )
            )
    return tuple(references), tuple(keys)


def _purpose(files: dict[str, dict[str, Any]]) -> CandidateStatement:
    order = sorted(
        files,
        key=lambda path: (0 if path == "README.md" else 1, path.casefold()),
    )
    for path in order:
        raw = files[path]
        if raw.get("truncated") is True:
            continue
        if path != "README.md" and raw.get("role") not in {
            "project_overview",
            "project_status",
        }:
            continue
        if isinstance(raw.get("content"), str) and (
            text := _purpose_paragraph(raw["content"])
        ):
            return CandidateStatement(
                key="purpose",
                topic="purpose",
                text=text,
                kind=(
                    StatementKind.FACT
                    if path == "README.md"
                    else StatementKind.INTERPRETATION
                ),
                basis=(
                    "The repository states this in README.md."
                    if path == "README.md"
                    else f"This is the strongest purpose-like statement in {path}."
                ),
                evidence_keys=(_key(path),),
            )
    return CandidateStatement(
        key="purpose",
        topic="purpose",
        text=(
            "The repository does not state a clear project purpose in the collected "
            "evidence."
        ),
        kind=StatementKind.UNKNOWN,
        basis="No complete, purpose-like plain-language paragraph was found.",
    )


def _authorities(
    files: dict[str, dict[str, Any]], records: list[Any]
) -> tuple[AuthorityRecord, ...]:
    items = [
        item
        for item in records
        if isinstance(item, dict)
        and item.get("path") in files
        and isinstance(item.get("authority_rank"), int)
    ]
    if not items:
        return ()
    primary = min(item["authority_rank"] for item in items)
    result: list[AuthorityRecord] = []
    for item in sorted(
        items,
        key=lambda value: (value["authority_rank"], value["path"].casefold()),
    ):
        path = item["path"]
        declared = None
        if path.endswith(".json"):
            try:
                parsed = json.loads(str(files[path].get("content", "")))
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, dict) and isinstance(parsed.get("authority"), str):
                declared = parsed["authority"]
        result.append(
            AuthorityRecord(
                path=path,
                kind=str(item.get("kind", "unknown")),
                authority_rank=item["authority_rank"],
                source_url=str(files[path].get("source_url", "")),
                source_commit=str(files[path].get("source_commit", "")),
                valid=item.get("valid_json") if path.endswith(".json") else True,
                primary=item["authority_rank"] == primary,
                declared_authority=declared,
            )
        )
    return tuple(result)


def _machine(
    path: str, raw: dict[str, Any], rank: int
) -> tuple[list[_Work], list[CandidateStatement]]:
    try:
        data = json.loads(str(raw.get("content", "")))
    except json.JSONDecodeError:
        return [], [
            CandidateStatement(
                key=f"uncertainty:invalid-json:{path}",
                topic="owner_authority",
                text=(
                    f"{path} is not valid JSON, so its work claims were not "
                    "interpreted."
                ),
                kind=StatementKind.UNKNOWN,
                basis="The owner-authority record could not be parsed.",
                evidence_keys=(_key(path),),
                owner_authority=True,
            )
        ]
    if not isinstance(data, dict) or not isinstance(data.get("stages"), list):
        return [], [
            CandidateStatement(
                key=f"uncertainty:no-stages:{path}",
                topic="owner_authority",
                text=f"{path} does not contain a readable stages list.",
                kind=StatementKind.UNKNOWN,
                basis="The expected owner-authority structure is absent.",
                evidence_keys=(_key(path),),
                owner_authority=True,
            )
        ]
    work: list[_Work] = []
    unknowns: list[CandidateStatement] = []
    for index, stage in enumerate(data["stages"]):
        if not isinstance(stage, dict):
            continue
        label = stage.get("label") or stage.get("id")
        completed, total = stage.get("completed"), stage.get("total")
        numbers = all(
            isinstance(value, (int, float)) and not isinstance(value, bool)
            for value in (completed, total)
        )
        if (
            not isinstance(label, str)
            or not label.strip()
            or not numbers
            or total <= 0
            or completed < 0
            or completed > total
        ):
            unknowns.append(
                CandidateStatement(
                    key=f"uncertainty:invalid-stage:{path}:{index}",
                    topic="owner_authority",
                    text=f"A stage in {path} has invalid label or count data.",
                    kind=StatementKind.UNKNOWN,
                    basis="Its work state cannot be read safely.",
                    evidence_keys=(_key(path),),
                    owner_authority=True,
                )
            )
            continue
        work.append(
            _Work(
                label=label.strip(),
                state="done" if completed == total else "remaining",
                rank=rank,
                path=path,
                detail=(
                    f"{completed:g} of {total:g} authorised units are recorded as "
                    "complete"
                ),
            )
        )
    return work, unknowns


def _markdown(path: str, content: str, rank: int) -> list[_Work]:
    result: list[_Work] = []
    for line in content.splitlines():
        if not (match := _TASK.match(line)):
            continue
        label = _plain(match.group("label"))
        if label:
            state = "done" if match.group("mark").lower() == "x" else "remaining"
            result.append(
                _Work(
                    label,
                    state,
                    rank,
                    path,
                    "marked complete" if state == "done" else "listed as unfinished",
                )
            )
    return result


def _work(
    files: dict[str, dict[str, Any]], authorities: tuple[AuthorityRecord, ...]
) -> tuple[
    tuple[CandidateStatement, ...],
    tuple[CandidateStatement, ...],
    list[Conflict],
    list[CandidateStatement],
]:
    if not authorities:
        return (), (), [], [
            CandidateStatement(
                "uncertainty:done-authority",
                "done",
                "Completed work is unknown because no recognised owner-authority record is present.",
                StatementKind.UNKNOWN,
                "Open issues and activity are not completion evidence.",
            ),
            CandidateStatement(
                "uncertainty:remaining-authority",
                "remaining",
                "Remaining work is unknown because no recognised owner-authority record is present.",
                StatementKind.UNKNOWN,
                "Open queues are not automatically the project finish line.",
            ),
        ]
    observations: list[_Work] = []
    unknowns: list[CandidateStatement] = []
    incomplete = False
    for authority in authorities:
        raw = files[authority.path]
        if raw.get("truncated") is True:
            incomplete = True
            unknowns.append(
                CandidateStatement(
                    f"uncertainty:truncated-authority:{authority.path}",
                    "owner_authority",
                    f"{authority.path} is truncated, so its work items were not interpreted.",
                    StatementKind.UNKNOWN,
                    "A partial owner-authority record cannot safely define done or remaining work.",
                    (_key(authority.path),),
                    True,
                )
            )
        elif authority.kind == "machine_progress" or authority.path.endswith(".json"):
            found, more = _machine(
                authority.path, raw, authority.authority_rank
            )
            observations.extend(found)
            unknowns.extend(more)
        elif isinstance(raw.get("content"), str):
            observations.extend(
                _markdown(authority.path, raw["content"], authority.authority_rank)
            )

    groups: dict[str, list[_Work]] = {}
    for item in observations:
        groups.setdefault(_normal(item.label), []).append(item)
    done: list[CandidateStatement] = []
    remaining: list[CandidateStatement] = []
    conflicts: list[Conflict] = []
    unresolved = False
    for index, label in enumerate(sorted(groups)):
        group = sorted(
            groups[label], key=lambda item: (item.rank, item.path.casefold())
        )
        best_rank = group[0].rank
        best = [item for item in group if item.rank == best_rank]
        best_states = {item.state for item in best}
        all_states = {item.state for item in group}
        keys = tuple(dict.fromkeys(_key(item.path) for item in group))
        if len(all_states) > 1:
            conflicts.append(
                Conflict(
                    f"work-conflict:{index}",
                    "work_state",
                    (
                        "Owner-authority records disagree about whether "
                        f"{group[0].label!r} is complete."
                    ),
                    keys,
                    (
                        "unresolved because equal-ranked records disagree"
                        if len(best_states) > 1
                        else (
                            f"the rank-{best_rank} record is used while the "
                            "disagreement remains visible"
                        )
                    ),
                )
            )
        if len(best_states) > 1:
            unresolved = True
            unknowns.append(
                CandidateStatement(
                    f"uncertainty:work-conflict:{index}",
                    "work_state",
                    (
                        f"The state of {group[0].label!r} is unknown because "
                        "equal-ranked authority records disagree."
                    ),
                    StatementKind.UNKNOWN,
                    "Equal-ranked owner-authority records have no deterministic winner.",
                    keys,
                    True,
                )
            )
            continue
        chosen = best[0]
        candidate = CandidateStatement(
            f"{chosen.state}:{index}",
            chosen.state,
            (
                f"{chosen.label} is recorded as "
                f"{'complete' if chosen.state == 'done' else 'unfinished'}."
            ),
            StatementKind.FACT,
            f"{chosen.detail} in {chosen.path}.",
            (_key(chosen.path),),
            True,
        )
        (done if chosen.state == "done" else remaining).append(candidate)

    if not observations:
        unknowns.append(
            CandidateStatement(
                "uncertainty:no-work-items",
                "work_state",
                (
                    "The recognised owner-authority records do not contain readable "
                    "work items."
                ),
                StatementKind.UNKNOWN,
                "No stage counts or Markdown tasks could be interpreted safely.",
                tuple(_key(item.path) for item in authorities),
                True,
            )
        )
    elif (
        not remaining
        and not unresolved
        and not incomplete
        and not any(item.state == "remaining" for item in observations)
    ):
        remaining.append(
            CandidateStatement(
                "remaining:none-listed",
                "remaining",
                (
                    "No unfinished work item is listed in the recognised "
                    "owner-authority records."
                ),
                StatementKind.FACT,
                "Every readable authority item is recorded as complete.",
                tuple(dict.fromkeys(_key(item.path) for item in observations)),
                True,
            )
        )
    return tuple(done), tuple(remaining), conflicts, unknowns


def _technologies(
    files: dict[str, dict[str, Any]],
) -> tuple[tuple[CandidateStatement, ...], list[CandidateStatement]]:
    found: dict[str, CandidateStatement] = {}

    def add(name: str, path: str, basis: str) -> None:
        found.setdefault(
            name,
            CandidateStatement(
                "technology:"
                + re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-"),
                "technology",
                f"This repository uses {name}.",
                StatementKind.FACT,
                basis,
                (_key(path),),
            ),
        )

    for path, raw in files.items():
        if raw.get("truncated") is True or not isinstance(raw.get("content"), str):
            continue
        lower, content = path.casefold(), raw["content"]
        if lower == "pyproject.toml":
            try:
                project = tomllib.loads(content).get("project")
            except tomllib.TOMLDecodeError:
                project = None
            if isinstance(project, dict):
                version = project.get("requires-python")
                add(
                    "Python",
                    path,
                    (
                        f"pyproject.toml declares requires-python {version}."
                        if isinstance(version, str)
                        else "pyproject.toml defines a Python project."
                    ),
                )
        elif lower == "package.json":
            try:
                package = json.loads(content)
            except json.JSONDecodeError:
                package = None
            if isinstance(package, dict):
                add(
                    "JavaScript or Node.js",
                    path,
                    "package.json defines the JavaScript package.",
                )
                dependencies = {
                    name.casefold()
                    for field in ("dependencies", "devDependencies")
                    if isinstance(package.get(field), dict)
                    for name in package[field]
                }
                if "typescript" in dependencies:
                    add(
                        "TypeScript",
                        path,
                        "package.json lists TypeScript as a dependency.",
                    )
        elif lower == "cargo.toml":
            add("Rust", path, "Cargo.toml defines the Rust package.")
        elif lower == "go.mod":
            add("Go", path, "go.mod defines the Go module.")
        elif lower == "gemfile":
            add("Ruby", path, "Gemfile defines Ruby dependencies.")
        elif lower == "dockerfile" or lower.endswith("/dockerfile"):
            add("Docker", path, "Dockerfile defines a container build.")
        elif Path(lower).name.startswith("requirements") and lower.endswith(".txt"):
            add("Python", path, f"{path} lists Python dependencies.")
    if found:
        return tuple(found[name] for name in sorted(found, key=str.casefold)), []
    return (), [
        CandidateStatement(
            "uncertainty:technology",
            "technology",
            "The collected evidence does not contain a recognised technology manifest.",
            StatementKind.UNKNOWN,
            (
                "Technology claims are refused unless a collected repository file "
                "directly supports them."
            ),
        )
    ]


def interpret_evidence_bundle(value: Mapping[str, Any] | Any) -> InterpretationBundle:
    """Produce reviewable candidate statements from one factual v0.3 bundle."""
    data = _payload(value)
    _validate(data)
    files, file_evidence, stale, unknowns = _files(data)
    queue_evidence, queue_keys = _queue_references(data)
    authorities = _authorities(files, data["progress_records"])
    done, remaining, work_conflicts, work_unknowns = _work(files, authorities)
    technologies, technology_unknowns = _technologies(files)
    unknowns.extend(work_unknowns)
    unknowns.extend(technology_unknowns)
    if queue_keys:
        issue_count = len(data["open_issues"])
        pull_count = len(data["open_pull_requests"])
        unknowns.append(
            CandidateStatement(
                "uncertainty:open-queues",
                "remaining",
                (
                    f"The evidence bundle records {issue_count} open issue(s) and "
                    f"{pull_count} open pull request(s), but they are not automatically "
                    "treated as the project finish line."
                ),
                StatementKind.UNKNOWN,
                (
                    "The cited queue entries are inspectable, but queue state does not "
                    "prove owner-authorised remaining work."
                ),
                queue_keys,
            )
        )
    evidence = tuple(sorted((*file_evidence, *queue_evidence), key=lambda item: item.key))
    return InterpretationBundle(
        schema_version=1,
        source_evidence_schema_version=1,
        repository=data["repository"],
        repository_url=data["repository_url"],
        source_commit=data["source_commit"],
        evidence_checked_at=data["checked_at"],
        purpose=_purpose(files),
        owner_authority_records=authorities,
        done=done,
        remaining=remaining,
        technologies=technologies,
        uncertainties=tuple(sorted(unknowns, key=lambda item: item.key)),
        conflicts=tuple(sorted(stale + work_conflicts, key=lambda item: item.key)),
        evidence=evidence,
        refusals=(
            Refusal(
                "completion_percentage",
                "v0.4 does not calculate completion percentages.",
            ),
            Refusal(
                "likelihood_assessment",
                "v0.4 does not forecast whether the project will be finished.",
            ),
            Refusal(
                "final_status",
                "v0.4 produces candidate statements, not a final project judgement.",
            ),
        ),
    )


def write_interpretation_bundle(
    bundle: InterpretationBundle, destination: Path
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(bundle.to_json(), encoding="utf-8")
