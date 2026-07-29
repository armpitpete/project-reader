import json
from pathlib import Path

import pytest

from project_reader.models import EvidenceStrength
from project_reader.interpretation import interpret_evidence_bundle
from project_reader.reading import build_project_reading
from project_reader.render import render_html

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


def authority(stages):
    return json.dumps({"schema_version": 1, "stages": stages})


def bundle(*files, progress_records=()):
    return {
        "schema_version": 1,
        "checked_at": "2026-07-29T10:00:00Z",
        "repository": "example/project",
        "repository_url": "https://github.com/example/project",
        "default_branch": "main",
        "source_commit": HEAD,
        "source_url": f"https://github.com/example/project/tree/{HEAD}",
        "gitingest_summary": "summary",
        "important_files": list(files),
        "progress_records": list(progress_records),
        "open_issues": [],
        "open_pull_requests": [],
    }


def test_builds_complete_ordinary_reader_from_authority_records(tmp_path: Path) -> None:
    authority_json = authority(
        [
            {"label": "Evidence collection", "completed": 1, "total": 1},
            {"label": "Reader page", "completed": 1, "total": 1},
        ]
    )
    interpretation = interpret_evidence_bundle(
        bundle(
            file(
                "README.md",
                "project_overview",
                "# Project\n\nProject Reader helps ordinary people understand public projects.",
            ),
            file(".project/progress.json", "machine_progress", authority_json),
            file("pyproject.toml", "technology_manifest", "[project]\nname='project'\n"),
            progress_records=(progress(),),
        )
    )
    reading = build_project_reading(interpretation)

    assert reading.name == "Project"
    assert reading.status == "Complete"
    assert reading.completion.percentage == 100
    assert reading.likelihood.label == "Already complete"
    assert reading.remaining_empty is not None
    assert reading.contact_url == "https://github.com/example"
    assert reading.technologies[0].name == "Python"

    destination = tmp_path / "reader.html"
    render_html(reading, destination)
    html = destination.read_text(encoding="utf-8")
    assert "What is this project?" not in html
    assert "Why should this assessment be trusted?" in html
    assert "How was this made?" in html
    assert "Contact the project owner" in html
    assert "No unfinished work item is listed in the selected owner-authority records." in html


def test_builds_active_reader_when_authority_records_remaining_work() -> None:
    authority_json = authority(
        [
            {"label": "Evidence collection", "completed": 1, "total": 1},
            {"label": "Release page", "completed": 0, "total": 1},
        ]
    )
    interpretation = interpret_evidence_bundle(
        bundle(
            file(".project/progress.json", "machine_progress", authority_json),
            progress_records=(progress(),),
        )
    )
    reading = build_project_reading(interpretation)

    assert reading.status == "Active"
    assert reading.completion.percentage == 50
    assert reading.likelihood.label == "Unknown"
    assert reading.remaining[0].text == "Release page is recorded as unfinished."
    assert "Release page" in reading.next_step.text


def test_partial_authority_units_are_used_for_completion_percentage() -> None:
    interpretation = interpret_evidence_bundle(
        bundle(
            file(
                ".project/progress.json",
                "machine_progress",
                authority(
                    [
                        {"label": "Reader page", "completed": 9, "total": 10},
                        {"label": "Release sign-off", "completed": 0, "total": 1},
                    ]
                ),
            ),
            progress_records=(progress(),),
        )
    )
    reading = build_project_reading(interpretation)

    assert reading.status == "Active"
    assert reading.completion.percentage == 82
    assert reading.completion.explanation == "9 of 11 defined work units are accepted as done."


def test_equal_rank_authority_conflict_suppresses_completion_and_status() -> None:
    interpretation = interpret_evidence_bundle(
        bundle(
            file("STATUS.md", "project_status", "# Status\n\n- [x] Shared item\n"),
            file("PROJECT_STATUS.md", "project_status", "# Status\n\n- [ ] Shared item\n"),
            progress_records=(
                progress("STATUS.md", 2, "project_status"),
                progress("PROJECT_STATUS.md", 2, "project_status"),
            ),
        )
    )
    reading = build_project_reading(interpretation)

    assert reading.status == "Unknown"
    assert reading.completion.percentage is None
    assert reading.completion.evidence_strength is EvidenceStrength.UNKNOWN


def test_lower_rank_conflict_does_not_block_primary_completion() -> None:
    interpretation = interpret_evidence_bundle(
        bundle(
            file(
                ".project/progress.json",
                "machine_progress",
                authority([{"label": "Shared item", "completed": 1, "total": 1}]),
            ),
            file("ROADMAP.md", "roadmap", "# Roadmap\n\n- [ ] Shared item\n"),
            progress_records=(
                progress(),
                progress("ROADMAP.md", 3, "roadmap"),
            ),
        )
    )
    reading = build_project_reading(interpretation)

    assert interpretation.conflicts
    assert reading.remaining_empty is not None
    assert reading.remaining_empty.evidence_keys == ("file:.project/progress.json",)
    assert reading.status == "Complete"
    assert reading.completion.percentage == 100


def test_missing_authority_suppresses_completion_and_status() -> None:
    interpretation = interpret_evidence_bundle(
        bundle(
            file(
                "README.md",
                "project_overview",
                "# Project\n\nProject Reader helps ordinary people understand public projects.",
            )
        )
    )
    reading = build_project_reading(interpretation)

    assert reading.status == "Unknown"
    assert reading.completion.percentage is None
    assert reading.likelihood.label == "Unknown"


def test_invalid_authority_suppresses_completion_and_status() -> None:
    interpretation = interpret_evidence_bundle(
        bundle(
            file(".project/progress.json", "machine_progress", "{not valid json"),
            progress_records=(progress(),),
        )
    )
    reading = build_project_reading(interpretation)

    assert reading.status == "Unknown"
    assert reading.completion.percentage is None


def test_truncated_authority_suppresses_completion_and_status() -> None:
    interpretation = interpret_evidence_bundle(
        bundle(
            file(
                ".project/progress.json",
                "machine_progress",
                authority([{"label": "Shared item", "completed": 1, "total": 1}]),
                truncated=True,
            ),
            progress_records=(progress(),),
        )
    )
    reading = build_project_reading(interpretation)

    assert reading.status == "Unknown"
    assert reading.completion.percentage is None


def test_stale_non_authority_evidence_does_not_block_completion() -> None:
    interpretation = interpret_evidence_bundle(
        bundle(
            file(
                "README.md",
                "project_overview",
                "# Old\n\nThis old file is stale and should not define status.",
                commit=OTHER,
            ),
            file(
                ".project/progress.json",
                "machine_progress",
                authority([{"label": "Shared item", "completed": 1, "total": 1}]),
            ),
            progress_records=(progress(),),
        )
    )
    reading = build_project_reading(interpretation)

    assert any(conflict.topic == "stale_evidence" for conflict in interpretation.conflicts)
    assert reading.status == "Complete"
    assert reading.completion.percentage == 100


def test_manifest_does_not_prove_project_specific_technology_claims() -> None:
    interpretation = interpret_evidence_bundle(
        bundle(
            file("pyproject.toml", "technology_manifest", "[project]\nname='project'\n"),
        )
    )
    reading = build_project_reading(interpretation)
    technology = reading.technologies[0]

    assert "unknown" in technology.use_here
    assert technology.reason_strength is EvidenceStrength.UNKNOWN
    assert technology.evidence_keys == ("file:pyproject.toml",)


@pytest.mark.parametrize("contact_url", ["javascript:alert(1)", "data:text/html,<p>x</p>"])
def test_unsafe_contact_url_is_rejected(contact_url: str) -> None:
    interpretation = interpret_evidence_bundle(bundle())

    with pytest.raises(ValueError, match="Contact URL"):
        build_project_reading(interpretation, contact_url=contact_url)
