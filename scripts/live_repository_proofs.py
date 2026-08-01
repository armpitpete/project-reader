from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from project_reader.evidence import EvidenceCollectionError, collect_public_evidence
from project_reader.interpretation import InterpretationError, interpret_evidence_bundle
from project_reader.reading import build_project_reading
from project_reader.render import render_html_string

DEFAULT_REPOSITORIES = (
    "armpitpete/over-my-home",
    "armpitpete/sample-hold-lab",
)


def _authority_unknown(interpretation) -> bool:
    return any(
        item.owner_authority
        or item.topic in {"owner_authority", "work_state"}
        or item.key in {"uncertainty:done-authority", "uncertainty:remaining-authority"}
        for item in interpretation.uncertainties
    )


def _read(repository: str, *, max_repository_size_kb: int) -> dict[str, Any]:
    evidence = collect_public_evidence(
        repository,
        token=os.getenv("PROJECT_READER_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN"),
        max_repository_size_kb=max_repository_size_kb,
    )
    interpretation = interpret_evidence_bundle(evidence)
    reading = build_project_reading(interpretation)
    result_html = render_html_string(reading)
    return {
        "repository": evidence.repository,
        "repository_url": evidence.repository_url,
        "source_commit": evidence.source_commit,
        "checked_at": evidence.checked_at,
        "status": reading.status,
        "completion_percentage": reading.completion.percentage,
        "completion_evidence_strength": reading.completion.evidence_strength.value,
        "likelihood": reading.likelihood.label,
        "language_names": [item.name for item in reading.repository_languages],
        "important_files": [item.path for item in evidence.important_files],
        "progress_records": [item.path for item in evidence.progress_records],
        "authority_record_count": len(interpretation.owner_authority_records),
        "authority_unknown": _authority_unknown(interpretation),
        "open_issue_count": len(evidence.open_issues),
        "open_pull_request_count": len(evidence.open_pull_requests),
        "html_contains_reader_questions": all(
            phrase in result_html
            for phrase in (
                "Simple reading",
                "What is this project?",
                "What can someone do with it?",
                "What appears to work or be finished?",
                "What is unfinished or unclear?",
                "What was it made with?",
                "Project status and reasons",
                "Technical sources and repository details",
            )
        ),
    }


def _assert_contract(proofs: list[dict[str, Any]]) -> None:
    by_repo = {item["repository"]: item for item in proofs}
    if set(by_repo) != set(DEFAULT_REPOSITORIES):
        raise AssertionError("live proof set does not match the public repository fixtures")

    missing = by_repo["armpitpete/over-my-home"]
    if missing["completion_percentage"] is not None or missing["status"] != "Unknown":
        raise AssertionError("over-my-home did not preserve the unsupported-completion unknown state")

    for proof in proofs:
        if len(proof["source_commit"]) != 40:
            raise AssertionError(f"{proof['repository']} has no exact source commit")
        if not proof["repository_url"].startswith("https://github.com/"):
            raise AssertionError(f"{proof['repository']} has no public GitHub source URL")
        if not proof["html_contains_reader_questions"]:
            raise AssertionError(f"{proof['repository']} did not render the reader result")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run live public-repository proofs for the retained Python reference toolkit."
    )
    parser.add_argument(
        "--repository",
        action="append",
        dest="repositories",
        help="owner/name public repository to read. Defaults to the public proof set.",
    )
    parser.add_argument("--output", type=Path, required=True, help="JSON proof file to write")
    parser.add_argument(
        "--max-repository-size-kb",
        type=int,
        default=50_000,
        help="Maximum GitHub repository size accepted by the reference reader.",
    )
    args = parser.parse_args()

    repositories = tuple(args.repositories or DEFAULT_REPOSITORIES)
    try:
        proofs = [
            _read(repository, max_repository_size_kb=args.max_repository_size_kb)
            for repository in repositories
        ]
        if repositories == DEFAULT_REPOSITORIES:
            _assert_contract(proofs)
    except (ValueError, EvidenceCollectionError, InterpretationError, AssertionError) as error:
        parser.exit(2, f"Project Reader live proof failed: {error}\n")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "proof_repositories": proofs,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {args.output} with {len(proofs)} live repository proof(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
