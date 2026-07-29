import pytest

from project_reader.assessment import assess_completion, assess_likelihood
from project_reader.models import EvidenceStrength, LikelihoodSignals, WorkItem, WorkState


def test_completion_counts_only_done_work() -> None:
    result = assess_completion(
        [
            WorkItem("Done", WorkState.DONE, 2),
            WorkItem("In progress", WorkState.IN_PROGRESS, 1),
            WorkItem("To do", WorkState.TODO, 1),
        ],
        finish_line_defined=True,
        evidence_strength=EvidenceStrength.CONFIRMED,
    )
    assert result.percentage == 50


def test_completion_is_unknown_without_finish_line() -> None:
    result = assess_completion(
        [WorkItem("Something", WorkState.DONE)],
        finish_line_defined=False,
        evidence_strength=EvidenceStrength.ESTIMATED,
    )
    assert result.percentage is None
    assert result.evidence_strength is EvidenceStrength.UNKNOWN


def test_completion_is_unknown_with_unresolved_authority() -> None:
    result = assess_completion(
        [WorkItem("Something", WorkState.DONE)],
        finish_line_defined=True,
        evidence_strength=EvidenceStrength.UNKNOWN,
    )
    assert result.percentage is None
    assert result.evidence_strength is EvidenceStrength.UNKNOWN
    assert "owner-authority evidence" in result.explanation


def test_likelihood_uses_broad_label_and_confidence() -> None:
    result = assess_likelihood(
        LikelihoodSignals(20, 18, 13, 15, 12, 8, 4, 0.85)
    )
    assert result.label == "Very likely"
    assert result.confidence == "High"
    assert result.range_high <= 95


def test_completed_project_is_not_given_a_future_forecast() -> None:
    result = assess_likelihood(
        LikelihoodSignals(20, 20, 15, 15, 15, 10, 5, 1),
        already_complete=True,
    )
    assert result.label == "Already complete"
    assert (result.range_low, result.range_high) == (100, 100)


def test_likelihood_rejects_invalid_signal() -> None:
    with pytest.raises(ValueError):
        assess_likelihood(LikelihoodSignals(21, 0, 0, 0, 0, 0, 0, 1))
