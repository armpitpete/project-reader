from __future__ import annotations

import re
from urllib.parse import urlparse

from .assessment import assess_completion, assess_likelihood
from .interpretation import CandidateStatement, InterpretationBundle
from .models import (
    Claim,
    Evidence,
    EvidenceStrength,
    LikelihoodResult,
    LikelihoodSignals,
    ProjectReading,
    RepositoryLanguage,
    Technology,
    WorkItem,
    WorkState,
)


def _project_name(repository: str) -> str:
    name = repository.split("/", 1)[-1]
    return " ".join(part.capitalize() for part in re.split(r"[-_]+", name) if part)


def _statement_label(statement: CandidateStatement) -> str:
    text = statement.text
    for suffix in (
        " is recorded as complete.",
        " is recorded as unfinished.",
    ):
        if text.endswith(suffix):
            return text[: -len(suffix)]
    return text


def _reader_text(text: str) -> str:
    replacements = (
        ("selected owner-authority records", "selected progress records"),
        ("recognised owner-authority records", "recognised progress records"),
        ("owner-authority progress record", "progress record"),
        ("Owner-authority progress record", "Progress record"),
        ("owner-authority records", "progress records"),
        ("Owner-authority records", "Progress records"),
        ("owner-authority", "progress"),
        ("Owner-authority", "Progress"),
        ("authority-backed", "approved"),
        ("Authority-backed", "Approved"),
        ("authorised project stages", "planned parts"),
        ("Authorised project stages", "Planned parts"),
        ("authorised units", "planned parts"),
        ("Authorised units", "Planned parts"),
    )
    result = text
    for old, new in replacements:
        result = result.replace(old, new)
    return result


def _evidence_keys(*statements: CandidateStatement) -> tuple[str, ...]:
    keys: list[str] = []
    for statement in statements:
        keys.extend(statement.evidence_keys)
    return tuple(dict.fromkeys(keys))


def _technology(statement: CandidateStatement) -> Technology:
    name = statement.text.removeprefix("This repository uses ").removesuffix(".")
    explanations = {
        "Python": "A programming language designed to be readable.",
        "JavaScript or Node.js": "A common technology for interactive websites and server tools.",
        "TypeScript": "JavaScript with extra type checks.",
        "Docker": "A way to package software with the environment it needs.",
    }
    simple = explanations.get(
        name,
        "A technology declared by the repository.",
    )
    return Technology(
        name=name,
        simple_explanation=simple,
        use_here="Project-specific use is unknown from the collected evidence.",
        reason_used="No collected evidence explains why this technology was chosen.",
        reason_strength=EvidenceStrength.UNKNOWN,
        location=", ".join(
            key.removeprefix("file:") for key in statement.evidence_keys
        )
        or "The collected repository evidence.",
        why_it_matters="The claim is shown only because a collected repository file supports it.",
        evidence_keys=statement.evidence_keys,
    )


def _repository_language(statement: CandidateStatement) -> RepositoryLanguage:
    if (
        statement.language_name is None
        or statement.language_bytes is None
        or statement.language_percentage is None
    ):
        raise ValueError("Repository language statements must carry structured language data")
    return RepositoryLanguage(
        name=statement.language_name,
        percentage=statement.language_percentage,
        bytes=statement.language_bytes,
        evidence_keys=statement.evidence_keys,
    )


def _open_queue_keys(reading: InterpretationBundle) -> tuple[str, ...]:
    for item in reading.uncertainties:
        if item.key == "uncertainty:open-queues":
            return item.evidence_keys
    return ()


def validate_contact_url(value: str) -> str:
    candidate = value.strip()
    parsed = urlparse(candidate)
    if not candidate or candidate != value or any(ord(char) < 32 for char in candidate):
        raise ValueError("Contact URL must be a complete http, https or mailto URL.")
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return candidate
    if parsed.scheme == "mailto" and parsed.path:
        return candidate
    raise ValueError("Contact URL must be a complete http, https or mailto URL.")


def _authority_unknowns(reading: InterpretationBundle) -> tuple[CandidateStatement, ...]:
    return tuple(
        item
        for item in reading.uncertainties
        if item.owner_authority
        or item.topic in {"owner_authority", "work_state"}
        or item.key in {"uncertainty:done-authority", "uncertainty:remaining-authority"}
    )


def _completion_items(statement: CandidateStatement, fallback_state: WorkState) -> tuple[WorkItem, ...]:
    title = _reader_text(_statement_label(statement))
    if statement.completed_units is None or statement.total_units is None:
        return (WorkItem(title, fallback_state, evidence_keys=statement.evidence_keys),)

    completed = statement.completed_units
    remaining = statement.total_units - statement.completed_units
    items: list[WorkItem] = []
    if completed > 0:
        items.append(WorkItem(title, WorkState.DONE, completed, statement.evidence_keys))
    if remaining > 0:
        items.append(WorkItem(title, WorkState.TODO, remaining, statement.evidence_keys))
    return tuple(items)


def _unknown_likelihood(evidence_keys: tuple[str, ...]) -> LikelihoodResult:
    return LikelihoodResult(
        score=0,
        label="Unknown",
        range_low=0,
        range_high=0,
        confidence="Low",
        timeframe="Insufficient evidence for an evidence-backed likelihood forecast.",
        evidence_keys=evidence_keys,
    )


def build_project_reading(
    interpretation: InterpretationBundle,
    *,
    project_name: str | None = None,
    contact_url: str | None = None,
) -> ProjectReading:
    """Build the ordinary-reader page model from one interpreted evidence bundle."""
    done_work = [
        WorkItem(
            _reader_text(_statement_label(item)),
            WorkState.DONE,
            evidence_keys=item.evidence_keys,
        )
        for item in interpretation.done
        if item.owner_authority
    ]
    remaining_authority = [
        item
        for item in interpretation.remaining
        if item.owner_authority and item.key != "remaining:none-listed"
    ]
    completion_work = [
        unit
        for item in interpretation.done
        if item.owner_authority
        for unit in _completion_items(item, WorkState.DONE)
    ] + [
        unit
        for item in remaining_authority
        for unit in _completion_items(item, WorkState.TODO)
    ]
    remaining_work = [
        WorkItem(
            _reader_text(_statement_label(item)),
            WorkState.TODO,
            evidence_keys=item.evidence_keys,
        )
        for item in remaining_authority
    ]
    no_remaining = next(
        (
            item
            for item in interpretation.remaining
            if item.key == "remaining:none-listed"
        ),
        None,
    )
    authority_statements = [*interpretation.done, *remaining_authority]
    if no_remaining is not None:
        authority_statements.append(no_remaining)
    authority_unknowns = _authority_unknowns(interpretation)
    authority_keys = _evidence_keys(*authority_statements, *authority_unknowns)
    finish_line_defined = bool(done_work or remaining_work or no_remaining) and not authority_unknowns
    evidence_strength = (
        EvidenceStrength.CONFIRMED
        if finish_line_defined
        else EvidenceStrength.UNKNOWN
    )
    completion = assess_completion(
        completion_work,
        finish_line_defined=finish_line_defined,
        evidence_strength=evidence_strength,
        evidence_keys=authority_keys,
        scope_label="of readable authority items",
    )
    complete = finish_line_defined and bool(done_work) and not remaining_work and no_remaining is not None
    if complete:
        status = "Complete"
        next_step = Claim(
            "Decide whether to archive the project as complete or define a new milestone before starting more development.",
            authority_keys,
        )
    elif finish_line_defined and remaining_work:
        status = "Active"
        next_step = Claim(
            _reader_text(f"Complete the next owner-authority item: {remaining_work[0].title}."),
            remaining_work[0].evidence_keys,
        )
    else:
        status = "Unknown"
        queue_keys = _open_queue_keys(interpretation)
        next_step = Claim(
            _reader_text(
                "Add or review an owner-authority progress record so completion can be assessed."
            ),
            queue_keys,
        )

    if complete:
        likelihood = assess_likelihood(
            LikelihoodSignals(20, 20, 15, 15, 15, 10, 5, 1.0),
            timeframe="The current defined work has already been reached.",
            already_complete=True,
            evidence_keys=authority_keys,
        )
    else:
        likelihood = _unknown_likelihood(authority_keys or _open_queue_keys(interpretation))

    owner = interpretation.repository.split("/", 1)[0]
    safe_contact_url = (
        validate_contact_url(contact_url)
        if contact_url is not None
        else f"https://github.com/{owner}"
    )
    evidence = tuple(
        Evidence(
            key=item.key,
            label=(
                item.path
                if item.role.startswith("open_")
                else item.path
                if item.role == "repository_language"
                else f"{item.path} ({item.role.replace('_', ' ')})"
            ),
            source=item.source_url,
            strength=EvidenceStrength.CONFIRMED if item.usable else EvidenceStrength.UNKNOWN,
        )
        for item in interpretation.evidence
    )
    remaining_empty = (
        Claim(
            _reader_text(no_remaining.text),
            no_remaining.evidence_keys,
        )
        if no_remaining is not None
        else None
    )
    return ProjectReading(
        name=project_name or _project_name(interpretation.repository),
        explanation=Claim(
            _reader_text(interpretation.purpose.text),
            interpretation.purpose.evidence_keys,
        ),
        status=status,  # type: ignore[arg-type]
        status_evidence_keys=authority_keys,
        completion=completion,
        likelihood=likelihood,
        done=tuple(Claim(_reader_text(item.text), item.evidence_keys) for item in interpretation.done),
        remaining=tuple(Claim(_reader_text(item.text), item.evidence_keys) for item in remaining_authority),
        remaining_empty=remaining_empty,
        next_step=next_step,
        repository_languages=tuple(
            _repository_language(item) for item in interpretation.repository_languages
        ),
        technologies=tuple(_technology(item) for item in interpretation.technologies),
        evidence=evidence,
        source_commit=interpretation.source_commit,
        assessed_at=interpretation.evidence_checked_at,
        open_work_checked_at=interpretation.evidence_checked_at,
        project_url=interpretation.repository_url,
        contact_url=safe_contact_url,
    )
