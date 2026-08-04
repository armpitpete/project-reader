from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "prototype" / "public-reader.html"
DEFAULT_APP = ROOT / "prototype" / "app.js"
DEFAULT_COMPREHENSION = ROOT / "prototype" / "comprehension.js"
DEFAULT_NETWORK_CORRECTIONS = ROOT / "prototype" / "network-corrections.js"
DEFAULT_POLISH = ROOT / "prototype" / "polish.js"
DEFAULT_RESILIENCE = ROOT / "prototype" / "resilience.js"
SHA = re.compile(r"^[0-9a-f]{40}$")
PUBLIC_ORIGIN = "https://armpitpete.github.io/project-reader/"
SITEMAP_NAMESPACE = "http://www.sitemaps.org/schemas/sitemap/0.9"


def build_pages_site(
    *,
    commit: str,
    output: Path,
    source: Path = DEFAULT_SOURCE,
    app_source: Path = DEFAULT_APP,
    comprehension_source: Path = DEFAULT_COMPREHENSION,
    network_corrections_source: Path = DEFAULT_NETWORK_CORRECTIONS,
    polish_source: Path = DEFAULT_POLISH,
    resilience_source: Path = DEFAULT_RESILIENCE,
) -> tuple[Path, ...]:
    if not SHA.fullmatch(commit):
        raise ValueError("Deployment commit must be a 40-character lowercase Git SHA.")

    html = source.read_text(encoding="utf-8")
    marker = "<!-- DEPLOYMENT_DETAIL -->"
    if marker not in html:
        raise ValueError("Source HTML does not contain the deployment marker.")

    deployment_note = f"""
<details class="technical-detail">
<summary>Technical detail: deployment</summary>
<p><strong>Project Reader deployment commit:</strong> <code>{escape(commit)}</code></p>
<p>This public reader was produced from the Project Reader repository at that exact commit.</p>
</details>
"""
    html = html.replace(marker, deployment_note, 1)

    output.mkdir(parents=True, exist_ok=True)
    index = output / "index.html"
    app = output / "app.js"
    comprehension = output / "comprehension.js"
    network_corrections = output / "network-corrections.js"
    polish = output / "polish.js"
    resilience = output / "resilience.js"
    metadata = output / "deployment.json"
    sitemap = output / "sitemap.xml"
    nojekyll = output / ".nojekyll"

    index.write_text(html, encoding="utf-8")
    shutil.copyfile(app_source, app)
    shutil.copyfile(comprehension_source, comprehension)
    shutil.copyfile(network_corrections_source, network_corrections)
    shutil.copyfile(polish_source, polish)
    shutil.copyfile(resilience_source, resilience)
    sitemap.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="{SITEMAP_NAMESPACE}">\n'
        f"  <url><loc>{PUBLIC_ORIGIN}</loc></url>\n"
        "</urlset>\n",
        encoding="utf-8",
    )
    public_files = [
        ".nojekyll",
        "app.js",
        "comprehension.js",
        "deployment.json",
        "index.html",
        "network-corrections.js",
        "polish.js",
        "resilience.js",
        "sitemap.xml",
    ]
    metadata.write_text(
        json.dumps(
            {
                "schema_version": 4,
                "project": "Project Reader resilient evidence-backed repository comprehension",
                "repository": "armpitpete/project-reader",
                "deployed_commit": commit,
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
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    nojekyll.write_text("", encoding="utf-8")
    return (
        nojekyll,
        app,
        comprehension,
        metadata,
        index,
        network_corrections,
        polish,
        resilience,
        sitemap,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the self-contained GitHub Pages reader artifact."
    )
    parser.add_argument("--commit", required=True, help="Project Reader commit SHA")
    parser.add_argument("--output", type=Path, required=True, help="Artifact directory")
    args = parser.parse_args()

    files = build_pages_site(commit=args.commit, output=args.output)
    print("Built Pages artifact:")
    for path in files:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
