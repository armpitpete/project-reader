from __future__ import annotations

from .models import (
    CompletionResult,
    EvidenceStrength,
    LikelihoodResult,
    LikelihoodSignals,
    WorkItem,
    WorkState,
)


def assess_completion(
    work_items: list[WorkItem],
    *,
    finish_line_defined: bool,
    evidence_strength: EvidenceStrength,
    evidence_keys: tuple[str, ...] = (),
    scope_label: str = "complete",
) -> CompletionResult:
    """Calculate accepted completion without treating activity as progress."""
    if not finish_line_defined or not work_items:
        return CompletionResult(
            percentage=None,
            evidence_strength=EvidenceStrength.UNKNOWN,
            explanation="Completion cannot be measured because the finish line is not defined.",
            scope_label=scope_label,
            evidence_keys=evidence_keys,
        )

    total_weight = sum(item.weight for item in work_items)
    done_weight = sum(item.weight for item in work_items if item.state is WorkState.DONE)
    percentage = round((done_weight / total_weight) * 100)

    return CompletionResult(
        percentage=percentage,
        evidence_strength=evidence_strength,
        explanation=f"{done_weight:g} of {total_weight:g} defined work units are accepted as done.",
        scope_label=scope_label,
        evidence_keys=evidence_keys,
    )


def _validate_signals(signals: LikelihoodSignals) -> None:
    limits = {
        "finish_line_clarity": 20,
        "recent_progress": 20,
        "bounded_remaining_work": 15,
        "next_step_clarity": 15,
        "manageable_blockers": 15,
        "delivery_history": 10,
        "repository_health": 5,
    }
    for name, maximum in limits.items():
        value = getattr(signals, name)
        if not 0 <= value <= maximum:
            raise ValueError(f"{name} must be between 0 and {maximum}")
    if not 0 <= signals.evidence_coverage <= 1:
        raise ValueError("evidence_coverage must be between 0 and 1")


def assess_likelihood(
    signals: LikelihoodSignals,
    *,
    timeframe: str = "Current milestone within 12 months",
    already_complete: bool = False,
    evidence_keys: tuple[str, ...] = (),
) -> LikelihoodResult:
    """Return a broad, evidence-labelled forecast rather than false precision."""
    _validate_signals(signals)

    if signals.evidence_coverage >= 0.8:
        confidence = "High"
        margin = 5
    elif signals.evidence_coverage >= 0.5:
        confidence = "Medium"
        margin = 10
    else:
        confidence = "Low"
        margin = 15

    if already_complete:
        return LikelihoodResult(
            score=100,
            label="Already complete",
            range_low=100,
            range_high=100,
            confidence=confidence,
            timeframe=timeframe,
            evidence_keys=evidence_keys,
        )

    score = (
        signals.finish_line_clarity
        + signals.recent_progress
        + signals.bounded_remaining_work
        + signals.next_step_clarity
        + signals.manageable_blockers
        + signals.delivery_history
        + signals.repository_health
    )

    if score >= 85:
        label = "Very likely"
    elif score >= 70:
        label = "Likely"
    elif score >= 50:
        label = "Uncertain"
    elif score >= 30:
        label = "Unlikely"
    else:
        label = "Very unlikely"

    return LikelihoodResult(
        score=score,
        label=label,
        range_low=max(5, score - margin),
        range_high=min(95, score + margin),
        confidence=confidence,
        timeframe=timeframe,
        evidence_keys=evidence_keys,
    )
