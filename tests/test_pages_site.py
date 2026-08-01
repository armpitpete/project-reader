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


def test_pages_site_contains_only_public_reader_files(tmp_path: Path) -> None:
    build_pages_site(commit=HEAD, output=tmp_path)

    public_files = sorted(path.name for path in tmp_path.iterdir())
    assert public_files == [
        ".nojekyll",
        "app.js",
        "comprehension.js",
        "deployment.json",
        "index.html",
    ]

    metadata = json.loads((tmp_path / "deployment.json").read_text(encoding="utf-8"))
    assert metadata == {
        "schema_version": 3,
        "project": "Project Reader evidence-backed public repository comprehension",
        "repository": "armpitpete/project-reader",
        "deployed_commit": HEAD,
        "runtime": "browser-only",
        "public_data_origin": "https://api.github.com",
        "source_html": "prototype/public-reader.html",
        "source_scripts": ["prototype/app.js", "prototype/comprehension.js"],
        "public_files": public_files,
    }

    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    app = (tmp_path / "app.js").read_text(encoding="utf-8")
    comprehension = (tmp_path / "comprehension.js").read_text(encoding="utf-8")

    assert "Project Reader" in html
    assert "Understand what a public GitHub project is" in html
    assert "Public GitHub repository" in html
    assert "Read this project" in html
    assert 'role="status" aria-live="polite"' in html
    assert 'aria-label="Project Reader result"' in html
    assert '<script type="module" src="./app.js"></script>' in html
    assert "Project Reader deployment commit:" in html
    assert HEAD in html
    assert "reader-api.merrinworld.uk" not in html + app + comprehension
    assert "GITHUB_TOKEN" not in html + app + comprehension
    assert "PRIVATE KEY" not in (html + app + comprehension).upper()
    assert "innerHTML" not in app + comprehension
    assert 'method: "GET"' in app
    assert 'method: "POST"' not in app
    assert "buildComprehension" in comprehension
    assert "Learning course or curriculum" in comprehension
    assert "Application and open-source codebase" in comprehension
    assert "coding or markup language" not in comprehension
    assert "percentage >= 0.1" in comprehension
    assert "What is this?" in app
    assert "Who is it for?" in app
    assert "What can I do with it?" in app
    assert "What already exists?" in app
    assert "What is unfinished or uncertain?" in app
    assert "Where should I start?" in app
    assert "Evidence behind the plain reading" in app
    assert "write anything" in app
    assert "I:\\" not in html + app + comprehension
    assert "C:\\" not in html + app + comprehension
    assert "SECRET" not in (html + app + comprehension).upper()


def test_pages_site_rejects_non_commit_identifier(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="40-character"):
        build_pages_site(commit="main", output=tmp_path)
