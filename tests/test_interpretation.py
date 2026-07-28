import json

import pytest

from project_reader.interpretation import InterpretationError, interpret_evidence_bundle

HEAD = "a" * 40
OTHER = "b" * 40


def file(path, role, content, *, commit=HEAD, truncated=False):
    return {
        "path": path,
        "role": role,
        "collection_method": "gitingest",
        "source_url": f"https://github.com/example/project/blob/{commit}/{path}",
        "source_commit": commit,
        "sha256": "0" * 64,
        "characters": len(content),
        "content": content,
        "truncated": truncated,
    }


def bundle(*files, progress=(), issues=(), pulls=()):
    return {
        "schema_version": 1,
        "checked_at": "2026-07-28T12:00:00Z",
        "repository": "example/project",
        "repository_url": "https://github.com/example/project",
        "default_branch": "main",
        "source_commit": HEAD,
        "source_url": f"https://github.com/example/project/tree/{HEAD}",
        "gitingest_summary": "summary",
        "important_files": list(files),
        "progress_records": list(progress),
        "open_issues": list(issues),
        "open_pull_requests": list(pulls),
    }


def progress(path=".project/progress.json", rank=1, kind="machine_progress"):
    return {
        "path": path,
        "kind": kind,
        "authority_rank": rank,
        "sha256": "0" * 64,
        "valid_json": True if path.endswith(".json") else None,
        "schema_version": 1 if path.endswith(".json") else None,
        "stage_count": 2 if path.endswith(".json") else None,
        "overall_enabled": False if path.endswith(".json") else None,
    }


PROGRESS = json.dumps(
    {
        "schema_version": 1,
        "authority": "README.md",
        "stages": [
            {
                "id": "one",
                "label": "First stage",
                "completed": 1,
                "total": 1,
            },
            {
                "id": "two",
                "label": "Second stage",
                "completed": 1,
                "total": 3,
            },
        ],
        "overall": {"enabled": False},
    }
)


def test_reads_purpose_and_owner_authority_work():
    result = interpret_evidence_bundle(
        bundle(
            file(
                "README.md",
                "project_overview",
                "# Example\n\nA small tool that explains public projects clearly.",
            ),
            file(".project/progress.json", "machine_progress", PROGRESS),
            progress=(progress(),),
        )
    )
    assert result.purpose.kind == "fact"
    assert result.purpose.text == "A small tool that explains public projects clearly."
    assert result.owner_authority_records[0].primary is True
    assert result.owner_authority_records[0].declared_authority == "README.md"
    assert [item.text for item in result.done] == [
        "First stage is recorded as complete."
    ]
    assert [item.text for item in result.remaining] == [
        "Second stage is recorded as unfinished."
    ]


def test_no_remaining_authority_items_is_not_overstated():
    complete = json.dumps(
        {
            "schema_version": 1,
            "stages": [
                {"label": "Only stage", "completed": 1, "total": 1}
            ],
        }
    )
    result = interpret_evidence_bundle(
        bundle(
            file(".project/progress.json", "machine_progress", complete),
            progress=(progress(),),
        )
    )
    assert result.remaining[0].text.startswith("No unfinished work item")
    assert result.remaining[0].owner_authority is True


def test_open_queues_are_not_treated_as_remaining_authority():
    result = interpret_evidence_bundle(
        bundle(
            file(
                "README.md",
                "project_overview",
                "# Example\n\nA public example project with a clear purpose.",
            ),
            issues=({"number": 4, "title": "Maybe later"},),
        )
    )
    assert result.remaining == ()
    assert any(
        item.key == "uncertainty:open-queues" for item in result.uncertainties
    )
    assert any(
        item.key == "uncertainty:remaining-authority"
        for item in result.uncertainties
    )


def test_lower_rank_conflict_is_visible_but_primary_authority_wins():
    result = interpret_evidence_bundle(
        bundle(
            file(".project/progress.json", "machine_progress", PROGRESS),
            file("ROADMAP.md", "roadmap", "# Roadmap\n\n- [ ] First stage\n"),
            progress=(progress(), progress("ROADMAP.md", 3, "roadmap")),
        )
    )
    assert result.done[0].text == "First stage is recorded as complete."
    assert result.conflicts[0].topic == "work_state"
    assert "rank-1" in result.conflicts[0].resolution


def test_equal_rank_conflict_returns_unknown():
    result = interpret_evidence_bundle(
        bundle(
            file("STATUS.md", "project_status", "# Status\n\n- [x] Shared item\n"),
            file(
                "PROJECT_STATUS.md",
                "project_status",
                "# Project status\n\n- [ ] Shared item\n",
            ),
            progress=(
                progress("STATUS.md", 2, "project_status"),
                progress("PROJECT_STATUS.md", 2, "project_status"),
            ),
        )
    )
    assert result.done == ()
    assert result.remaining == ()
    assert any(
        "equal-ranked" in item.basis.casefold() for item in result.uncertainties
    )


def test_stale_file_is_excluded_and_reported():
    result = interpret_evidence_bundle(
        bundle(
            file(
                "README.md",
                "project_overview",
                "# Old\n\nThis should not be trusted as current.",
                commit=OTHER,
            )
        )
    )
    assert result.purpose.kind == "unknown"
    assert result.conflicts[0].topic == "stale_evidence"
    assert result.evidence[0].usable is False
    assert (
        result.evidence[0].exclusion_reason
        == "source commit does not match the bundle"
    )


def test_technologies_require_manifest_evidence():
    result = interpret_evidence_bundle(
        bundle(
            file(
                "pyproject.toml",
                "technology_manifest",
                '[project]\nname = "example"\nrequires-python = ">=3.12"\n',
            )
        )
    )
    assert result.technologies[0].text == "This repository uses Python."
    assert not any(
        item.topic == "technology" for item in result.uncertainties
    )


def test_missing_manifest_returns_unknown_technology():
    result = interpret_evidence_bundle(
        bundle(
            file(
                "README.md",
                "project_overview",
                "# Example\n\nMade with futuristic magic and Python maybe.",
            )
        )
    )
    assert result.technologies == ()
    assert any(
        item.key == "uncertainty:technology" for item in result.uncertainties
    )


def test_truncated_file_is_flagged():
    result = interpret_evidence_bundle(
        bundle(
            file(
                "README.md",
                "project_overview",
                "# Example\n\nA clear project purpose is still visible here.",
                truncated=True,
            )
        )
    )
    assert any(item.topic == "evidence" for item in result.uncertainties)


def test_output_refuses_scoring_and_final_judgement():
    payload = interpret_evidence_bundle(bundle()).to_dict()
    assert "completion_percentage" not in payload
    assert "likelihood" not in payload
    assert "status" not in payload
    assert {item["topic"] for item in payload["refusals"]} == {
        "completion_percentage",
        "likelihood_assessment",
        "final_status",
    }


def test_wrong_schema_is_rejected():
    data = bundle()
    data["schema_version"] = 2
    with pytest.raises(InterpretationError, match="schema version 1"):
        interpret_evidence_bundle(data)
