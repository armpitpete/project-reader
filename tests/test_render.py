from pathlib import Path
import runpy

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
