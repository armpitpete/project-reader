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
        "network-corrections.js",
        "polish.js",
        "resilience.js",
    ]

    metadata = json.loads((tmp_path / "deployment.json").read_text(encoding="utf-8"))
    assert metadata == {
        "schema_version": 4,
        "project": "Project Reader resilient evidence-backed repository comprehension",
        "repository": "armpitpete/project-reader",
        "deployed_commit": HEAD,
        "runtime": "browser-only",
        "public_data_origins": [
            "https://api.github.com",
            "https://raw.githubusercontent.com",
        ],
        "rate_limit_fallback": "public README without account or token",
        "source_html": "prototype/public-reader.html",
        "source_scripts": [
            "prototype/app.js",
            "prototype/comprehension.js",
            "prototype/network-corrections.js",
            "prototype/polish.js",
            "prototype/resilience.js",
        ],
        "public_files": public_files,
    }

    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    app = (tmp_path / "app.js").read_text(encoding="utf-8")
    comprehension = (tmp_path / "comprehension.js").read_text(encoding="utf-8")
    network = (tmp_path / "network-corrections.js").read_text(encoding="utf-8")
    polish = (tmp_path / "polish.js").read_text(encoding="utf-8")
    resilience = (tmp_path / "resilience.js").read_text(encoding="utf-8")
    public = html + app + comprehension + network + polish + resilience

    assert "Project Reader" in html
    assert "Understand what a public GitHub project is" in html
    assert "Public GitHub repository" in html
    assert "Read this project" in html
    assert 'role="status" aria-live="polite"' in html
    assert 'aria-label="Project Reader result"' in html
    assert '<script type="module" src="./app.js"></script>' in html
    assert "Project Reader deployment commit:" in html
    assert HEAD in html
    assert "https://raw.githubusercontent.com" in html
    assert "falls back to the public README" in html
    assert "reader-api.merrinworld.uk" not in public
    assert "GITHUB_TOKEN" not in public
    assert "PRIVATE KEY" not in public.upper()
    assert "innerHTML" not in app + comprehension + network + polish + resilience
    assert 'method: "GET"' in app
    assert 'method: "POST"' not in app
    assert "buildComprehension" in comprehension
    assert "polishReading" in app
    assert "correctNetworkServiceReading" in app
    assert "fetchRawReadme" in app
    assert "polishReading" in polish
    assert "Command-line network client or service" in network
    assert "Install or download the command-line client" in network
    assert "Deprecated versions" not in network
    assert "raw-content service" in resilience
    assert "without account or token" in json.dumps(metadata)
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
    assert "Study or change the source code" in polish
    assert "Browse the course lessons" in polish
    assert "deeper mathematics of deep learning" in polish
    assert "overflow-x:hidden" in html
    assert "overflow-wrap:anywhere" in html
    assert "write anything" in app
    assert "I:\\" not in public
    assert "C:\\" not in public
    assert "SECRET" not in public.upper()


def test_pages_site_rejects_non_commit_identifier(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="40-character"):
        build_pages_site(commit="main", output=tmp_path)
