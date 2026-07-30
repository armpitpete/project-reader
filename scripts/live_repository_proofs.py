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
    "armpitpete/project-status-engine",
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
                "What is this project?",
                "What has been finished?",
                "What is still to do?",
                "Will the current plan be finished?",
                "What happens next?",
            )
        ),
    }


def _assert_contract(proofs: list[dict[str, Any]]) -> None:
    by_repo = {item["repository"]: item for item in proofs}
    mixed = by_repo["armpitpete/project-status-engine"]
    if len(mixed["language_names"]) < 3:
        raise AssertionError("project-status-engine did not prove mixed-language reading")
    if mixed["authority_record_count"] < 1 or mixed["completion_percentage"] is None:
        raise AssertionError("project-status-engine did not prove authority-backed completion")

    missing = by_repo["armpitpete/over-my-home"]
    if (
        missing["authority_record_count"] != 0
        or missing["completion_percentage"] is not None
        or missing["status"] != "Unknown"
        or not missing["authority_unknown"]
    ):
        raise AssertionError("over-my-home did not prove missing-authority unknown state")

    for proof in proofs:
        if len(proof["source_commit"]) != 40:
            raise AssertionError(f"{proof['repository']} has no exact source commit")
        if not proof["html_contains_reader_questions"]:
            raise AssertionError(f"{proof['repository']} did not render the reader result")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the v0.7 live public repository reading proofs."
    )
    parser.add_argument(
        "--repository",
        action="append",
        dest="repositories",
        help="owner/name public repository to read. Defaults to the v0.7 proof set.",
    )
    parser.add_argument("--output", type=Path, required=True, help="JSON proof file to write")
    parser.add_argument(
        "--max-repository-size-kb",
        type=int,
        default=50_000,
        help="Maximum GitHub repository size accepted by the public reader.",
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
                "schema_version": 1,
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
