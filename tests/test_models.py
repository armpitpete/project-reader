import pytest

from project_reader.models import (
    Claim,
    CompletionResult,
    Evidence,
    EvidenceStrength,
    LikelihoodResult,
    ProjectReading,
    RepositoryLanguage,
    WorkItem,
    WorkState,
)


def test_work_item_requires_positive_weight() -> None:
    with pytest.raises(ValueError):
        WorkItem("Invalid", WorkState.TODO, 0)


def test_repository_language_requires_valid_percentage() -> None:
    with pytest.raises(ValueError, match="between 0 and 100"):
        RepositoryLanguage("Python", 120.0, 10)


def test_project_reading_rejects_unknown_evidence_key() -> None:
    with pytest.raises(ValueError, match="Unknown evidence keys"):
        ProjectReading(
            name="Test",
            explanation=Claim("Explanation", ("missing",)),
            status="Unknown",
            status_evidence_keys=(),
            completion=CompletionResult(None, EvidenceStrength.UNKNOWN, "Unknown"),
            likelihood=LikelihoodResult(50, "Uncertain", 40, 60, "Low", "Within a year"),
            done=(),
            remaining=(),
            next_step=Claim("Find evidence"),
            evidence=(Evidence("known", "Known", "https://example.com"),),
        )
