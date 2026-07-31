from pathlib import Path
import runpy

import pytest

from project_reader.models import (
    Claim,
    CompletionResult,
    Evidence,
    EvidenceStrength,
    LikelihoodResult,
    ProjectReading,
    RepositoryLanguage,
)
from project_reader.render import render_html, render_html_fragment, render_html_string


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
    assert "Readable evidence and exact sources" in html
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
    assert "<script" not in html
    assert "<button" not in html


def test_rendered_fragment_has_no_document_shell_or_script() -> None:
    namespace = runpy.run_path("examples/project_status_engine.py")
    fragment = render_html_fragment(namespace["reading"])

    assert fragment.startswith("<style data-project-reader-result-style>")
    assert "<article class=\"project-reader-result\">" in fragment
    assert "<!doctype html>" not in fragment
    assert "<iframe" not in fragment
    assert "<script" not in fragment


def test_markdown_evidence_renders_readably_and_inert() -> None:
    malicious_markdown = """# Readable README

This evidence has a [safe source link](https://github.com/example/project) and `inline code`.

- a useful list item
- another useful list item

| Name | Meaning |
| --- | --- |
| R01 | A row |

```html
<script>alert("x")</script>
<form action="https://example.com"><button>Pay</button></form>
```

<img src=x onerror=alert(1)>
"""
    reading = ProjectReading(
        name="Project",
        explanation=Claim("The README says this project helps people.", ("file:README.md",)),
        status="Unknown",
        status_evidence_keys=("file:README.md",),
        completion=CompletionResult(
            None,
            EvidenceStrength.UNKNOWN,
            "Completion cannot be measured.",
            evidence_keys=("file:README.md",),
        ),
        likelihood=LikelihoodResult(
            0,
            "Unknown",
            0,
            0,
            "Low",
            "Insufficient evidence for an evidence-backed likelihood forecast.",
            evidence_keys=("file:README.md",),
        ),
        done=(),
        remaining=(),
        next_step=Claim("Review the README evidence.", ("file:README.md",)),
        evidence=(
            Evidence(
                "file:README.md",
                "README.md (project overview)",
                "https://github.com/example/project/blob/" + "a" * 40 + "/README.md",
                content=malicious_markdown,
                content_format="markdown",
            ),
        ),
        project_url="https://github.com/example/project",
        contact_url="mailto:owner@example.com",
    )

    html = render_html_string(reading)

    assert "<h4>Readable README</h4>" in html
    assert "<li>a useful list item</li>" in html
    assert "<table>" in html
    assert '<a href="https://github.com/example/project" target="_blank" rel="noopener noreferrer">safe source link</a>' in html
    assert "<code>inline code</code>" in html
    assert "<script>alert" not in html
    assert "&lt;script&gt;alert" in html
    assert "<form" not in html
    assert "onerror=alert" in html
    assert 'Open original source</a>' in html


def test_repository_languages_teach_catalogue_and_generic_fallback() -> None:
    evidence = (
        Evidence("language:typescript", "Repository languages: TypeScript (40%)", "https://api.github.com/repos/example/project/languages"),
        Evidence("language:css", "Repository languages: CSS (30%)", "https://api.github.com/repos/example/project/languages"),
        Evidence("language:html", "Repository languages: HTML (20%)", "https://api.github.com/repos/example/project/languages"),
        Evidence("language:mystery", "Repository languages: MysteryLang (10%)", "https://api.github.com/repos/example/project/languages"),
    )
    reading = ProjectReading(
        name="Project",
        explanation=Claim("The collected evidence does not state a clear purpose."),
        status="Unknown",
        status_evidence_keys=(),
        completion=CompletionResult(None, EvidenceStrength.UNKNOWN, "Completion cannot be measured."),
        likelihood=LikelihoodResult(0, "Unknown", 0, 0, "Low", "Insufficient evidence."),
        done=(),
        remaining=(),
        next_step=Claim("Review evidence."),
        repository_languages=(
            RepositoryLanguage("TypeScript", 40.0, 400, ("language:typescript",)),
            RepositoryLanguage("CSS", 30.0, 300, ("language:css",)),
            RepositoryLanguage("HTML", 20.0, 200, ("language:html",)),
            RepositoryLanguage("MysteryLang", 10.0, 100, ("language:mystery",)),
        ),
        evidence=evidence,
        project_url="https://github.com/example/project",
        contact_url="https://github.com/example",
    )

    html = render_html_string(reading)

    assert "TypeScript is JavaScript with extra checks" in html
    assert "CSS controls how a web page looks" in html
    assert "HTML gives a web page its structure" in html
    assert "MysteryLang is a repository language detected by GitHub Linguist." in html
    assert "The percentage alone is not enough to infer that." in html
    assert "They do not prove importance" in html


def test_project_contact_and_evidence_links_open_outside_result() -> None:
    reading = ProjectReading(
        name="Project",
        explanation=Claim("The README says this project helps people.", ("file:README.md",)),
        status="Unknown",
        status_evidence_keys=("file:README.md",),
        completion=CompletionResult(None, EvidenceStrength.UNKNOWN, "Completion cannot be measured."),
        likelihood=LikelihoodResult(0, "Unknown", 0, 0, "Low", "Insufficient evidence."),
        done=(),
        remaining=(),
        next_step=Claim("Review evidence.", ("file:README.md",)),
        evidence=(
            Evidence(
                "file:README.md",
                "README.md (project overview)",
                "https://github.com/example/project/blob/" + "a" * 40 + "/README.md",
                content="# Evidence",
                content_format="markdown",
            ),
        ),
        project_url="https://github.com/example/project",
        contact_url="https://github.com/example",
    )

    html = render_html_string(reading)

    assert '<a class="button" href="https://github.com/example/project" target="_blank" rel="noopener noreferrer">View the project</a>' in html
    assert '<a class="button" href="https://github.com/example" target="_blank" rel="noopener noreferrer">Contact the project owner</a>' in html
    assert '<a class="source-action" href="https://github.com/example/project/blob/' in html
    assert 'target="_blank" rel="noopener noreferrer">Open original source</a>' in html


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
