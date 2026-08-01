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
SHA = re.compile(r"^[0-9a-f]{40}$")


def build_pages_site(
    *,
    commit: str,
    output: Path,
    source: Path = DEFAULT_SOURCE,
    app_source: Path = DEFAULT_APP,
    comprehension_source: Path = DEFAULT_COMPREHENSION,
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
    metadata = output / "deployment.json"
    nojekyll = output / ".nojekyll"

    index.write_text(html, encoding="utf-8")
    shutil.copyfile(app_source, app)
    shutil.copyfile(comprehension_source, comprehension)
    public_files = [".nojekyll", "app.js", "comprehension.js", "deployment.json", "index.html"]
    metadata.write_text(
        json.dumps(
            {
                "schema_version": 3,
                "project": "Project Reader evidence-backed public repository comprehension",
                "repository": "armpitpete/project-reader",
                "deployed_commit": commit,
                "runtime": "browser-only",
                "public_data_origin": "https://api.github.com",
                "source_html": "prototype/public-reader.html",
                "source_scripts": ["prototype/app.js", "prototype/comprehension.js"],
                "public_files": public_files,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    nojekyll.write_text("", encoding="utf-8")
    return (nojekyll, app, comprehension, metadata, index)


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
