from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "prototype" / "public-reader.html"
DEFAULT_API_BASE_URL = "https://reader-api.merrinworld.uk"
SHA = re.compile(r"^[0-9a-f]{40}$")


def _public_api_base_url(value: str) -> str:
    candidate = value.strip().rstrip("/")
    parsed = urlparse(candidate)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.params
        or parsed.query
        or parsed.fragment
        or parsed.path
        or any(ord(char) < 32 or char in "\"'<>" for char in candidate)
    ):
        raise ValueError("Public API base URL must be a complete HTTPS origin.")
    return candidate


def build_pages_site(
    *,
    commit: str,
    output: Path,
    source: Path = DEFAULT_SOURCE,
    api_base_url: str = DEFAULT_API_BASE_URL,
) -> tuple[Path, ...]:
    if not SHA.fullmatch(commit):
        raise ValueError("Deployment commit must be a 40-character lowercase Git SHA.")

    api_base = _public_api_base_url(api_base_url)
    html = source.read_text(encoding="utf-8")
    html = html.replace("__PROJECT_READER_API_BASE__", api_base)
    html = html.replace("__PROJECT_READER_API_ORIGIN__", api_base)
    marker = "\n</main>"
    if marker not in html:
        raise ValueError("Source HTML does not contain the expected main landmark.")

    deployment_note = f"""
<details class="technical-detail">
<summary>Technical detail: deployment</summary>
<p><strong>Project Reader deployment commit:</strong> <code>{escape(commit)}</code></p>
<p>This static public proof was produced from the Project Reader repository at that exact commit.</p>
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
                "schema_version": 1,
                "project": "Project Reader public repository reading",
                "repository": "armpitpete/project-reader",
                "deployed_commit": commit,
                "api_base_url": api_base,
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
        description="Build the minimal read-only GitHub Pages proof artifact."
    )
    parser.add_argument("--commit", required=True, help="Project Reader commit SHA")
    parser.add_argument("--output", type=Path, required=True, help="Artifact directory")
    parser.add_argument(
        "--api-base-url",
        default=DEFAULT_API_BASE_URL,
        help="Public Project Reader API HTTPS origin",
    )
    args = parser.parse_args()

    files = build_pages_site(
        commit=args.commit,
        output=args.output,
        api_base_url=args.api_base_url,
    )
    print("Built Pages artifact:")
    for path in files:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
