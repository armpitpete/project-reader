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
from project_reader.render import render_html, render_html_string


def _primary_flow(html: str) -> str:
    _, primary = html.split('<section class="reader-flow"', 1)
    primary, _ = primary.split('<section class="disclosures"', 1)
    return primary


def test_public_proof_renders_simple_nd_yp_first_screen(tmp_path: Path) -> None:
    namespace = runpy.run_path("examples/project_status_engine.py")
    destination = tmp_path / "proof.html"
    render_html(namespace["reading"], destination)
    html = destination.read_text(encoding="utf-8")
    primary = _primary_flow(html)

    assert "Project Status Engine" in html
    assert "What is this project?" in primary
    assert "What has been finished?" in primary
    assert "What is still to do?" in primary
    assert "Will the current plan be finished?" in primary
    assert "What happens next?" in primary
    assert "100% of planned parts" in primary
    assert "The current plan is finished" in primary
    assert "Already complete" not in primary
    assert "defined stages" not in primary
    assert "defined work units" not in primary
    assert "Status:" not in primary
    assert "How complete?" not in primary
    assert "Likely to finish?" not in primary
    assert "authority" not in primary.casefold()
    assert "authorised" not in primary.casefold()
    assert '<p class="big">100% complete</p>' not in html
    assert "Contact the project owner" in html
    assert "Nothing currently listed." in html
    assert "<span aria-hidden='true'>○</span> Nothing currently listed." not in html
    assert "<details open>" not in html


def test_render_html_string_matches_written_document(tmp_path: Path) -> None:
    namespace = runpy.run_path("examples/project_status_engine.py")
    destination = tmp_path / "proof.html"
    render_html(namespace["reading"], destination)

    assert render_html_string(namespace["reading"]) == destination.read_text(
        encoding="utf-8"
    )


def test_primary_flow_has_no_hashes_timestamps_or_inline_citations(tmp_path: Path) -> None:
    namespace = runpy.run_path("examples/project_status_engine.py")
    destination = tmp_path / "proof.html"
    render_html(namespace["reading"], destination)
    primary = _primary_flow(destination.read_text(encoding="utf-8"))

    assert "citation" not in primary
    assert "[1]" not in primary
    assert "Source commit" not in primary
    assert "Reading checked" not in primary
    assert "Issues and pull requests checked" not in primary
    assert "Repository languages" not in primary
    assert "Python" not in primary
    assert "SourcePawn" not in primary
    assert "28 July 2026" not in primary
    assert "12:02" not in primary
    assert "d24e979e1747206f0c1ac3c66d3999f479f7ab72" not in primary


def test_evidence_stays_accessible_through_one_disclosure(tmp_path: Path) -> None:
    namespace = runpy.run_path("examples/project_status_engine.py")
    destination = tmp_path / "proof.html"
    render_html(namespace["reading"], destination)
    html = destination.read_text(encoding="utf-8")

    assert '<details class="evidence-disclosure">' in html
    assert "<summary>How do we know?</summary>" in html
    assert "Evidence behind the five answers" in html
    assert "All evidence sources" in html
    assert ".project/progress.json" in html
    assert "d24e979e1747206f0c1ac3c66d3999f479f7ab72" in html
    assert "28 July 2026 at 12:02 BST" in html
    assert html.count("<summary>How do we know?</summary>") == 1


def test_technical_detail_is_collapsed_by_default(tmp_path: Path) -> None:
    namespace = runpy.run_path("examples/project_status_engine.py")
    destination = tmp_path / "proof.html"
    render_html(namespace["reading"], destination)
    html = destination.read_text(encoding="utf-8")

    assert '<details class="technical-detail">' in html
    assert "<summary>Technical details</summary>" in html
    assert "Repository languages" in html
    assert "Python" in html
    assert "74.7% of detected code" in html
    assert "SourcePawn" in html
    assert "C++" in html
    assert "Pawn" in html
    assert "Shell" in html
    assert "PowerShell" in html
    assert "code volume" in html
    assert "They do not prove importance" in html
    assert "Support tools" in html
    assert "GitHub Actions" in html
    assert "Formats and outputs" in html
    assert "HTML, JSON and Markdown" in html
    assert "How Project Reader analysed this" in html
    assert "Project Reader's own implementation is separate" in html
    assert "<details open>" not in html


def test_layout_supports_narrow_width_zoom_and_reduced_motion(tmp_path: Path) -> None:
    namespace = runpy.run_path("examples/project_status_engine.py")
    destination = tmp_path / "proof.html"
    render_html(namespace["reading"], destination)
    html = destination.read_text(encoding="utf-8")

    assert "font-size: 18px;" in html
    assert "max-width: 42rem;" in html
    assert ".reader-flow" in html
    assert "gap: 1.75rem;" in html
    assert "@media (max-width: 700px)" in html
    assert "@media (prefers-reduced-motion: reduce)" in html
    assert "scroll-behavior: auto !important;" in html
    assert ":focus-visible" in html
    assert "outline: 4px solid" in html


def test_disclosure_controls_are_native_and_keyboard_operable(tmp_path: Path) -> None:
    namespace = runpy.run_path("examples/project_status_engine.py")
    destination = tmp_path / "proof.html"
    render_html(namespace["reading"], destination)
    html = destination.read_text(encoding="utf-8")

    assert "<details" in html
    assert "<summary>How do we know?</summary>" in html
    assert "<summary>Technical details</summary>" in html
    assert "details.open = !details.open;" in html
    assert "<button" not in html


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

    assert "We do not know yet" in html
    assert "The collected evidence is not enough for a clear answer." in html
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
