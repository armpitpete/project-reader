import json
from pathlib import Path
import importlib.util

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_pages_site", ROOT / "scripts" / "build_pages_site.py"
)
assert SPEC is not None and SPEC.loader is not None
build_pages_site_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_pages_site_module)
build_pages_site = build_pages_site_module.build_pages_site
HEAD = "f" * 40


def test_pages_site_contains_only_public_proof_files(tmp_path: Path) -> None:
    build_pages_site(commit=HEAD, output=tmp_path)

    public_files = sorted(path.name for path in tmp_path.iterdir())
    assert public_files == [".nojekyll", "deployment.json", "index.html"]

    metadata = json.loads((tmp_path / "deployment.json").read_text(encoding="utf-8"))
    assert metadata == {
        "schema_version": 1,
        "project": "Project Reader public proof",
        "repository": "armpitpete/project-reader",
        "deployed_commit": HEAD,
        "source_html": "prototype/project-status-engine.html",
        "public_files": [".nojekyll", "deployment.json", "index.html"],
    }

    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "Project Status Engine" in html
    assert "Technical detail: deployment" in html
    assert "Project Reader deployment commit:" in html
    assert HEAD in html
    assert "I:\\" not in html
    assert "C:\\" not in html
    assert "SECRET" not in html.upper()


def test_pages_site_rejects_non_commit_identifier(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="40-character"):
        build_pages_site(commit="main", output=tmp_path)
