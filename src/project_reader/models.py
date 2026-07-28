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
    label: str
    source: str
    strength: EvidenceStrength = EvidenceStrength.CONFIRMED


@dataclass(frozen=True)
class WorkItem:
    title: str
    state: WorkState
    weight: float = 1.0
    evidence: tuple[Evidence, ...] = ()

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


@dataclass(frozen=True)
class CompletionResult:
    percentage: int | None
    evidence_strength: EvidenceStrength
    explanation: str


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


@dataclass(frozen=True)
class ProjectReading:
    name: str
    explanation: str
    status: Literal["Active", "Paused", "Blocked", "Complete", "Archived", "Unknown"]
    completion: CompletionResult
    likelihood: LikelihoodResult
    done: tuple[str, ...]
    remaining: tuple[str, ...]
    next_step: str
    technologies: tuple[Technology, ...] = field(default_factory=tuple)
    project_url: str | None = None
    contact_url: str | None = None
