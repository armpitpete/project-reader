from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal


class EvidenceStrength(StrEnum):
    CONFIRMED = "confirmed"
    ESTIMATED = "estimated"
    UNKNOWN = "unknown"


class WorkState(StrEnum):
    DONE = "done"
    IN_PROGRESS = "in_progress"
    TODO = "todo"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Evidence:
    key: str
    label: str
    source: str
    strength: EvidenceStrength = EvidenceStrength.CONFIRMED

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("Evidence key must not be empty")
        if not self.label.strip():
            raise ValueError("Evidence label must not be empty")
        if not self.source.strip():
            raise ValueError("Evidence source must not be empty")


@dataclass(frozen=True)
class Claim:
    text: str
    evidence_keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("Claim text must not be empty")


@dataclass(frozen=True)
class WorkItem:
    title: str
    state: WorkState
    weight: float = 1.0
    evidence_keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.weight <= 0:
            raise ValueError("Work item weight must be greater than zero")


@dataclass(frozen=True)
class Technology:
    name: str
    simple_explanation: str
    use_here: str
    reason_used: str
    reason_strength: EvidenceStrength
    location: str
    why_it_matters: str
    evidence_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class CompletionResult:
    percentage: int | None
    evidence_strength: EvidenceStrength
    explanation: str
    evidence_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class LikelihoodSignals:
    finish_line_clarity: int
    recent_progress: int
    bounded_remaining_work: int
    next_step_clarity: int
    manageable_blockers: int
    delivery_history: int
    repository_health: int
    evidence_coverage: float


@dataclass(frozen=True)
class LikelihoodResult:
    score: int
    label: str
    range_low: int
    range_high: int
    confidence: Literal["Low", "Medium", "High"]
    timeframe: str
    evidence_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProjectReading:
    name: str
    explanation: Claim
    status: Literal["Active", "Paused", "Blocked", "Complete", "Archived", "Unknown"]
    status_evidence_keys: tuple[str, ...]
    completion: CompletionResult
    likelihood: LikelihoodResult
    done: tuple[Claim, ...]
    remaining: tuple[Claim, ...]
    next_step: Claim
    technologies: tuple[Technology, ...] = field(default_factory=tuple)
    evidence: tuple[Evidence, ...] = field(default_factory=tuple)
    project_url: str | None = None
    contact_url: str | None = None

    def __post_init__(self) -> None:
        keys = [item.key for item in self.evidence]
        if len(keys) != len(set(keys)):
            raise ValueError("Evidence keys must be unique")

        known = set(keys)
        references: list[str] = []
        references.extend(self.explanation.evidence_keys)
        references.extend(self.status_evidence_keys)
        references.extend(self.completion.evidence_keys)
        references.extend(self.likelihood.evidence_keys)
        references.extend(self.next_step.evidence_keys)
        for claim in (*self.done, *self.remaining):
            references.extend(claim.evidence_keys)
        for technology in self.technologies:
            references.extend(technology.evidence_keys)

        missing = sorted(set(references) - known)
        if missing:
            raise ValueError(f"Unknown evidence keys: {', '.join(missing)}")
