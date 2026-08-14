#!/usr/bin/env python3
"""Validate Project Reader's exact Real-Thing Proof adoption record.

Canonical lifecycle semantics are executed first from the immutable vendored snapshot
of armpitpete/merrin-project-controls@7bc8b7f5ef921851ad163093f089d28d8128bf6c.
The checks below are Project Reader-specific additions only.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

AUTHORITY = "armpitpete/merrin-project-controls@7bc8b7f5ef921851ad163093f089d28d8128bf6c"
ROOT = Path(__file__).resolve().parents[1]
CANONICAL_PATH = (
    ROOT
    / "vendor"
    / "merrin-project-controls"
    / "7bc8b7f5ef921851ad163093f089d28d8128bf6c"
    / "validate_project_status.py"
)
CANONICAL_BLOB_SHA = "d0e704ab42d72da6b66fb1d9f31d739ed6220abd"
CANONICAL_BYTES = CANONICAL_PATH.read_bytes()
actual_blob_sha = hashlib.sha1(
    f"blob {len(CANONICAL_BYTES)}\0".encode("ascii") + CANONICAL_BYTES
).hexdigest()
if actual_blob_sha != CANONICAL_BLOB_SHA:
    raise RuntimeError(
        "vendored canonical Project Status validator does not match the pinned authority"
    )
SPEC = importlib.util.spec_from_file_location("pinned_project_status_validator", CANONICAL_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("pinned canonical Project Status validator cannot be loaded")
CANONICAL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CANONICAL)


class AdoptionError(ValueError):
    pass


def validate_adoption(status: Any, progress: Any) -> None:
    try:
        CANONICAL.validate(status)
    except CANONICAL.StatusError as exc:
        raise AdoptionError(f"canonical Project Status rejection: {exc}") from exc

    if status.get("project") != "armpitpete/project-reader":
        raise AdoptionError("unexpected Project Reader lifecycle record")

    lifecycle = status.get("lifecycle_status", {})
    if lifecycle.get("authority") != AUTHORITY:
        raise AdoptionError("lifecycle authority is not the pinned Project Status v2 control")

    planning = status.get("percentage_complete", {})
    remaining = planning.get("remaining_work") or []
    if planning.get("estimate") == 100 and remaining:
        raise AdoptionError("100 percent planning progress is incompatible with declared remaining work")

    stages = lifecycle.get("stages", [])
    human = next((stage for stage in stages if stage.get("stage") == "human-acceptance"), None)
    if not isinstance(human, dict):
        raise AdoptionError("human acceptance stage is missing")
    if human.get("result") == "PASS":
        evidence = human.get("evidence") or []
        lowered = " ".join(str(item).lower() for item in evidence)
        if "actions/runs" in lowered or "automated" in lowered or "browser-acceptance" in lowered:
            raise AdoptionError("automated evidence cannot establish human acceptance")

    if not isinstance(progress, dict):
        raise AdoptionError("legacy progress record must be an object")
    release = progress.get("release")
    if not isinstance(release, dict):
        raise AdoptionError("legacy release record is missing")
    if "complete" in release:
        raise AdoptionError("legacy release must not expose an unqualified complete field")
    if release.get("bounded_release_stages_complete") is not True:
        raise AdoptionError("legacy release-stage completion must be explicitly bounded")
    scope = str(release.get("completion_scope", "")).lower()
    if "not whole-project lifecycle completion" not in scope:
        raise AdoptionError("legacy completion scope must exclude whole-project lifecycle completion")
    if progress.get("lifecycle_authority") != "../project-status.json":
        raise AdoptionError("legacy progress record must point to canonical lifecycle status")


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: validate_real_thing_adoption.py project-status.json .project/progress.json", file=sys.stderr)
        return 2
    try:
        status = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
        progress = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
        validate_adoption(status, progress)
    except (OSError, json.JSONDecodeError, AdoptionError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("valid Project Reader Real-Thing Proof adoption")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
