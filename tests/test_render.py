from pathlib import Path
import runpy

from project_reader.render import render_html


def test_public_proof_renders_citations_and_complete_state(tmp_path: Path) -> None:
    namespace = runpy.run_path("examples/project_status_engine.py")
    destination = tmp_path / "proof.html"
    render_html(namespace["reading"], destination)
    html = destination.read_text(encoding="utf-8")

    assert "Project Status Engine" in html
    assert "100% complete" in html
    assert "Already complete" in html
    assert "Contact the project owner" in html
    assert 'href="#evidence-completion"' in html
    assert "How was this made?" in html
