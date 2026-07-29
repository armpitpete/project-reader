import json
from pathlib import Path

from project_reader.interpretation import interpret_evidence_bundle
from project_reader.reading import build_project_reading
from project_reader.render import render_html

HEAD = "a" * 40


def file(path, role, content):
    return {
        "path": path,
        "role": role,
        "collection_method": "gitingest",
        "source_url": f"https://github.com/example/project/blob/{HEAD}/{path}",
        "source_commit": HEAD,
        "sha256": "0" * 64,
        "characters": len(content),
        "content": content,
        "truncated": False,
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
    authority = json.dumps(
        {
            "schema_version": 1,
            "stages": [
                {"label": "Evidence collection", "completed": 1, "total": 1},
                {"label": "Reader page", "completed": 1, "total": 1},
            ],
        }
    )
    interpretation = interpret_evidence_bundle(
        bundle(
            file(
                "README.md",
                "project_overview",
                "# Project\n\nProject Reader helps ordinary people understand public projects.",
            ),
            file(".project/progress.json", "machine_progress", authority),
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
    assert "Nothing currently listed in the recognised owner-authority records." in html


def test_builds_active_reader_when_authority_records_remaining_work() -> None:
    authority = json.dumps(
        {
            "schema_version": 1,
            "stages": [
                {"label": "Evidence collection", "completed": 1, "total": 1},
                {"label": "Release page", "completed": 0, "total": 1},
            ],
        }
    )
    interpretation = interpret_evidence_bundle(
        bundle(
            file(".project/progress.json", "machine_progress", authority),
            progress_records=(progress(),),
        )
    )
    reading = build_project_reading(interpretation)

    assert reading.status == "Active"
    assert reading.completion.percentage == 50
    assert reading.remaining[0].text == "Release page is recorded as unfinished."
    assert "Release page" in reading.next_step.text
