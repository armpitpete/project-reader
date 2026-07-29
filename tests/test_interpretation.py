import json

import pytest

from project_reader.interpretation import InterpretationError, interpret_evidence_bundle

HEAD = "a" * 40
OTHER = "b" * 40


def file(
    path,
    role,
    content,
    *,
    commit=HEAD,
    truncated=False,
    source_url=None,
):
    return {
        "path": path,
        "role": role,
        "collection_method": "gitingest",
        "source_url": source_url
        or f"https://github.com/example/project/blob/{commit}/{path}",
        "source_commit": commit,
        "sha256": "0" * 64,
        "characters": len(content),
        "content": content,
        "truncated": truncated,
    }


def issue(number=4):
    return {
        "number": number,
        "title": "Open issue",
        "url": f"https://github.com/example/project/issues/{number}",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-02T00:00:00Z",
        "labels": [],
        "draft": None,
    }


def pull(number=5):
    return {
        "number": number,
        "title": "Open pull request",
        "url": f"https://github.com/example/project/pull/{number}",
        "created_at": "2026-01-03T00:00:00Z",
        "updated_at": "2026-01-04T00:00:00Z",
        "labels": [],
        "draft": True,
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
    assert "selected owner-authority" in result.remaining[0].text
    assert result.remaining[0].owner_authority is True


def test_open_queues_are_inspectable_but_not_remaining_authority():
    result = interpret_evidence_bundle(
        bundle(
            file(
                "README.md",
                "project_overview",
                "# Example\n\nA tool that explains a public example project.",
            ),
            issues=(issue(),),
            pulls=(pull(),),
        )
    )
    assert result.remaining == ()
    queue = next(
        item for item in result.uncertainties if item.key == "uncertainty:open-queues"
    )
    assert queue.evidence_keys == ("issue:4", "pull_request:5")
    references = {item.key: item for item in result.evidence}
    assert references["issue:4"].source_url.endswith("/issues/4")
    assert references["issue:4"].role == "open_issue"
    assert references["pull_request:5"].source_url.endswith("/pull/5")
    assert references["pull_request:5"].role == "open_pull_request"
    assert any(
        item.key == "uncertainty:remaining-authority"
        for item in result.uncertainties
    )


def test_invalid_queue_url_is_rejected():
    bad = issue()
    bad["url"] = "https://github.com/other/project/issues/4"
    with pytest.raises(InterpretationError, match="uninspectable open_issues URL"):
        interpret_evidence_bundle(bundle(issues=(bad,)))


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
                "# Old\n\nThis tool should not be trusted as current.",
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


@pytest.mark.parametrize(
    "source_url",
    [
        f"https://github.com/other/project/blob/{HEAD}/README.md",
        f"https://github.com/example/project/blob/{HEAD}/OTHER.md",
        f"https://github.com/example/project/blob/{HEAD}/README.md?ref={HEAD}",
    ],
)
def test_file_url_must_match_repository_commit_and_path(source_url):
    result = interpret_evidence_bundle(
        bundle(
            file(
                "README.md",
                "project_overview",
                "# Example\n\nA tool that explains public projects.",
                source_url=source_url,
            )
        )
    )
    assert result.purpose.kind == "unknown"
    assert result.conflicts[0].topic == "stale_evidence"
    assert "repository, commit, and path" in result.evidence[0].exclusion_reason


def test_exact_raw_github_file_url_is_accepted():
    result = interpret_evidence_bundle(
        bundle(
            file(
                "README.md",
                "project_overview",
                "# Example\n\nA tool that explains public projects.",
                source_url=(
                    f"https://raw.githubusercontent.com/example/project/{HEAD}/README.md"
                ),
            )
        )
    )
    assert result.purpose.kind == "fact"
    assert result.evidence[0].usable is True


def test_purpose_selection_skips_non_purpose_preamble():
    result = interpret_evidence_bundle(
        bundle(
            file(
                "README.md",
                "project_overview",
                (
                    "# Example\n\n"
                    "Support this project through Ko-fi and sponsorship.\n\n"
                    "Project Reader helps non-technical people understand public repositories.\n\n"
                    "## Internal data\n\n"
                    "The repository system provides a workflow that manages every internal dataset and service."
                ),
            )
        )
    )
    assert result.purpose.text.startswith("Project Reader helps")


def test_truncated_purpose_file_returns_unknown():
    result = interpret_evidence_bundle(
        bundle(
            file(
                "README.md",
                "project_overview",
                "# Example\n\nA tool that explains public projects clearly.",
                truncated=True,
            )
        )
    )
    assert result.purpose.kind == "unknown"
    assert result.purpose.evidence_keys == ()
    assert any(item.topic == "evidence" for item in result.uncertainties)


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
    assert result.technologies[0].evidence_keys == ("file:pyproject.toml",)
    assert not any(
        item.topic == "technology" for item in result.uncertainties
    )


def test_missing_manifest_returns_unknown_technology():
    result = interpret_evidence_bundle(
        bundle(
            file(
                "README.md",
                "project_overview",
                "# Example\n\nA tool made with futuristic magic and Python maybe.",
            )
        )
    )
    assert result.technologies == ()
    assert any(
        item.key == "uncertainty:technology" for item in result.uncertainties
    )


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
