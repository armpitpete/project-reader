from __future__ import annotations

import re

from .assessment import assess_completion, assess_likelihood
from .interpretation import CandidateStatement, InterpretationBundle
from .models import (
    Claim,
    Evidence,
    EvidenceStrength,
    LikelihoodSignals,
    ProjectReading,
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


def _evidence_keys(*statements: CandidateStatement) -> tuple[str, ...]:
    keys: list[str] = []
    for statement in statements:
        keys.extend(statement.evidence_keys)
    return tuple(dict.fromkeys(keys))


def _technology(statement: CandidateStatement) -> Technology:
    name = statement.text.removeprefix("This repository uses ").removesuffix(".")
    explanations = {
        "Python": (
            "A programming language designed to be readable.",
            "It usually runs collection, interpretation, validation or rendering code.",
        ),
        "JavaScript or Node.js": (
            "A common technology for interactive websites and server tools.",
            "It usually supports browser code, build scripts or web services.",
        ),
        "TypeScript": (
            "JavaScript with extra type checks.",
            "It usually helps larger browser or server code stay consistent.",
        ),
        "Docker": (
            "A way to package software with the environment it needs.",
            "It usually makes setup and deployment more repeatable.",
        ),
    }
    simple, use_here = explanations.get(
        name,
        (
            "A technology declared by the repository.",
            "It supports part of the project implementation.",
        ),
    )
    return Technology(
        name=name,
        simple_explanation=simple,
        use_here=use_here,
        reason_used=statement.basis,
        reason_strength=EvidenceStrength.CONFIRMED,
        location=", ".join(
            key.removeprefix("file:") for key in statement.evidence_keys
        )
        or "The collected repository evidence.",
        why_it_matters="The claim is shown only because a collected repository file supports it.",
        evidence_keys=statement.evidence_keys,
    )


def _open_queue_keys(reading: InterpretationBundle) -> tuple[str, ...]:
    for item in reading.uncertainties:
        if item.key == "uncertainty:open-queues":
            return item.evidence_keys
    return ()


def build_project_reading(
    interpretation: InterpretationBundle,
    *,
    project_name: str | None = None,
    contact_url: str | None = None,
) -> ProjectReading:
    """Build the ordinary-reader page model from one interpreted evidence bundle."""
    done_work = [
        WorkItem(
            _statement_label(item),
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
    remaining_work = [
        WorkItem(
            _statement_label(item),
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
    authority_keys = _evidence_keys(*authority_statements)
    finish_line_defined = bool(done_work or remaining_work or no_remaining)
    evidence_strength = (
        EvidenceStrength.CONFIRMED
        if finish_line_defined and not interpretation.conflicts
        else EvidenceStrength.UNKNOWN
    )
    completion = assess_completion(
        [*done_work, *remaining_work],
        finish_line_defined=finish_line_defined,
        evidence_strength=evidence_strength,
        evidence_keys=authority_keys,
        scope_label="of readable authority items",
    )
    complete = bool(done_work) and not remaining_work and no_remaining is not None
    if complete:
        status = "Complete"
        next_step = Claim(
            "Decide whether to archive the project as complete or define a new milestone before starting more development.",
            authority_keys,
        )
    elif remaining_work:
        status = "Active"
        next_step = Claim(
            f"Complete the next owner-authority item: {remaining_work[0].title}.",
            remaining_work[0].evidence_keys,
        )
    else:
        status = "Unknown"
        queue_keys = _open_queue_keys(interpretation)
        next_step = Claim(
            "Add or review an owner-authority progress record so completion can be assessed.",
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
        likelihood = assess_likelihood(
            LikelihoodSignals(
                finish_line_clarity=20 if finish_line_defined else 5,
                recent_progress=14 if done_work else 0,
                bounded_remaining_work=12 if remaining_work else 4,
                next_step_clarity=15 if remaining_work else 8,
                manageable_blockers=8 if interpretation.conflicts else 12,
                delivery_history=6 if done_work else 0,
                repository_health=3 if interpretation.conflicts else 5,
                evidence_coverage=0.75 if finish_line_defined else 0.35,
            ),
            timeframe="Current defined milestone within 12 months.",
            evidence_keys=authority_keys or _open_queue_keys(interpretation),
        )

    owner = interpretation.repository.split("/", 1)[0]
    evidence = tuple(
        Evidence(
            key=item.key,
            label=(
                item.path
                if item.role.startswith("open_")
                else f"{item.path} ({item.role.replace('_', ' ')})"
            ),
            source=item.source_url,
            strength=EvidenceStrength.CONFIRMED if item.usable else EvidenceStrength.UNKNOWN,
        )
        for item in interpretation.evidence
    )
    remaining_empty = (
        Claim(
            "Nothing currently listed in the recognised owner-authority records.",
            no_remaining.evidence_keys,
        )
        if no_remaining is not None
        else None
    )
    return ProjectReading(
        name=project_name or _project_name(interpretation.repository),
        explanation=Claim(
            interpretation.purpose.text,
            interpretation.purpose.evidence_keys,
        ),
        status=status,  # type: ignore[arg-type]
        status_evidence_keys=authority_keys,
        completion=completion,
        likelihood=likelihood,
        done=tuple(Claim(item.text, item.evidence_keys) for item in interpretation.done),
        remaining=tuple(Claim(item.text, item.evidence_keys) for item in remaining_authority),
        remaining_empty=remaining_empty,
        next_step=next_step,
        technologies=tuple(_technology(item) for item in interpretation.technologies),
        evidence=evidence,
        source_commit=interpretation.source_commit,
        assessed_at=interpretation.evidence_checked_at,
        open_work_checked_at=interpretation.evidence_checked_at,
        project_url=interpretation.repository_url,
        contact_url=contact_url or f"https://github.com/{owner}",
    )
