from pathlib import Path
import runpy

import pytest

from project_reader.models import (
    Claim,
    CompletionResult,
    EvidenceStrength,
    LikelihoodResult,
    ProjectReading,
)
from project_reader.render import render_html


def test_public_proof_renders_citations_and_complete_state(tmp_path: Path) -> None:
    namespace = runpy.run_path("examples/project_status_engine.py")
    destination = tmp_path / "proof.html"
    render_html(namespace["reading"], destination)
    html = destination.read_text(encoding="utf-8")

    assert "Project Status Engine" in html
    assert "100% of defined stages" in html
    assert '<p class="big">100% complete</p>' not in html
    assert "no overall project percentage is authorised" in html
    assert "Already complete" in html
    assert "Contact the project owner" in html
    assert 'href="#evidence-completion"' in html
    assert ".project/progress.json" in html
    assert "Nothing currently listed." in html
    assert "<span aria-hidden='true'>○</span> Nothing currently listed." not in html
    assert "28 July 2026 at 12:02 BST" in html
    assert "d24e979e1747206f0c1ac3c66d3999f479f7ab72" in html
    assert "<details open>" not in html
    assert "How was this made?" in html
    assert "Why should this assessment be trusted?" in html


def test_unknown_likelihood_does_not_render_numeric_range(tmp_path: Path) -> None:
    reading = ProjectReading(
        name="Project",
        explanation=Claim("The collected evidence does not state a clear purpose."),
        status="Unknown",
        status_evidence_keys=(),
        completion=CompletionResult(
            None,
            EvidenceStrength.UNKNOWN,
            "Completion cannot be measured.",
        ),
        likelihood=LikelihoodResult(
            0,
            "Unknown",
            0,
            0,
            "Low",
            "Insufficient evidence for an evidence-backed likelihood forecast.",
        ),
        done=(),
        remaining=(),
        next_step=Claim("Add or review authority evidence."),
        project_url="https://github.com/example/project",
        contact_url="https://github.com/example",
    )
    destination = tmp_path / "unknown.html"
    render_html(reading, destination)
    html = destination.read_text(encoding="utf-8")

    assert "Likelihood is not measurable from the collected evidence." in html
    assert "Estimated range: 0" not in html


@pytest.mark.parametrize("field", ["project_url", "contact_url"])
def test_render_rejects_unsafe_action_urls(tmp_path: Path, field: str) -> None:
    values = {
        "project_url": "https://github.com/example/project",
        "contact_url": "https://github.com/example",
        field: "javascript:alert(1)",
    }
    reading = ProjectReading(
        name="Project",
        explanation=Claim("The collected evidence does not state a clear purpose."),
        status="Unknown",
        status_evidence_keys=(),
        completion=CompletionResult(
            None,
            EvidenceStrength.UNKNOWN,
            "Completion cannot be measured.",
        ),
        likelihood=LikelihoodResult(
            0,
            "Unknown",
            0,
            0,
            "Low",
            "Insufficient evidence for an evidence-backed likelihood forecast.",
        ),
        done=(),
        remaining=(),
        next_step=Claim("Add or review authority evidence."),
        **values,
    )

    with pytest.raises(ValueError, match="Rendered URLs"):
        render_html(reading, tmp_path / "unsafe.html")
