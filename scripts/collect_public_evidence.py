from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from project_reader.evidence import (
    EvidenceCollectionError,
    collect_public_evidence,
    write_evidence_bundle,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect a factual evidence bundle for one public GitHub repository."
    )
    parser.add_argument("repository", help="owner/name or https://github.com/owner/name")
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="JSON file to write",
    )
    parser.add_argument(
        "--max-repository-size-kb",
        type=int,
        help="Optional public repository size limit before repository content is read",
    )
    args = parser.parse_args()

    try:
        bundle = collect_public_evidence(
            args.repository,
            token=os.getenv("PROJECT_READER_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN"),
            max_repository_size_kb=args.max_repository_size_kb,
        )
        write_evidence_bundle(bundle, args.output)
    except (ValueError, EvidenceCollectionError) as error:
        parser.exit(2, f"Project Reader: {error}\n")

    print(
        f"Wrote {args.output} for {bundle.repository} at {bundle.source_commit} "
        f"with {len(bundle.repository_languages)} repository language(s), "
        f"{len(bundle.progress_records)} progress record(s), "
        f"{len(bundle.open_issues)} open issue(s), and "
        f"{len(bundle.open_pull_requests)} open pull request(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
