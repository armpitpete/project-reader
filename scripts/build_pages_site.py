from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "prototype" / "public-reader.html"
SHA = re.compile(r"^[0-9a-f]{40}$")


def build_pages_site(
    *,
    commit: str,
    output: Path,
    source: Path = DEFAULT_SOURCE,
) -> tuple[Path, ...]:
    if not SHA.fullmatch(commit):
        raise ValueError("Deployment commit must be a 40-character lowercase Git SHA.")

    html = source.read_text(encoding="utf-8")
    marker = "\n</main>"
    if marker not in html:
        raise ValueError("Source HTML does not contain the expected main landmark.")

    deployment_note = f"""
<details class="technical-detail">
<summary>Technical detail: deployment</summary>
<p><strong>Project Reader deployment commit:</strong> <code>{escape(commit)}</code></p>
<p>This self-contained public reader was produced from the Project Reader repository at that exact commit.</p>
</details>
"""
    html = html.replace(marker, deployment_note + marker, 1)

    output.mkdir(parents=True, exist_ok=True)
    index = output / "index.html"
    metadata = output / "deployment.json"
    nojekyll = output / ".nojekyll"

    index.write_text(html, encoding="utf-8")
    metadata.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "project": "Project Reader self-contained public repository reading",
                "repository": "armpitpete/project-reader",
                "deployed_commit": commit,
                "runtime": "browser-only",
                "public_data_origin": "https://api.github.com",
                "source_html": "prototype/public-reader.html",
                "public_files": [".nojekyll", "deployment.json", "index.html"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    nojekyll.write_text("", encoding="utf-8")
    return (nojekyll, metadata, index)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the minimal self-contained GitHub Pages reader artifact."
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
