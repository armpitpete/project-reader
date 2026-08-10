#!/usr/bin/env python3
"""Validate Project Reader's exact Real-Thing Proof adoption record.

This is deliberately project-specific. Canonical lifecycle semantics remain owned by
armpitpete/merrin-project-controls@7bc8b7f5ef921851ad163093f089d28d8128bf6c.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

AUTHORITY = "armpitpete/merrin-project-controls@7bc8b7f5ef921851ad163093f089d28d8128bf6c"
STAGES = (
    "designed",
    "implemented",
    "automated-checks",
    "independent-review",
    "merged",
    "deployed",
    "live-behaviour",
    "human-acceptance",
)
CANONICAL_CLAIMS = {
    "designed",
    "implemented",
    "automated-checks-passed",
    "independently-reviewed",
    "merged",
    "deployed",
    "live-behaviour-verified",
    "human-acceptance-received",
    "complete",
}


class AdoptionError(ValueError):
    pass


def validate_adoption(status: Any, progress: Any) -> None:
    if not isinstance(status, dict) or status.get("project") != "armpitpete/project-reader":
        raise AdoptionError("unexpected Project Reader lifecycle record")

    lifecycle = status.get("lifecycle_status")
    if not isinstance(lifecycle, dict) or lifecycle.get("authority") != AUTHORITY:
        raise AdoptionError("lifecycle authority is not the pinned Project Status v2 control")
    if lifecycle.get("claimed") not in CANONICAL_CLAIMS:
        raise AdoptionError("unsupported lifecycle claim")
    if lifecycle.get("verified") not in CANONICAL_CLAIMS | {"insufficient", "failed"}:
        raise AdoptionError("unsupported verified lifecycle state")

    stages = lifecycle.get("stages")
    if not isinstance(stages, list) or [stage.get("stage") for stage in stages] != list(STAGES):
        raise AdoptionError("all eight lifecycle stages must appear once in canonical order")

    for stage in stages[:7]:
        name = stage["stage"]
        if stage.get("required") is not True:
            raise AdoptionError(f"{name} must remain required")
        if stage.get("result") != "PASS" or stage.get("relationship") != "direct":
            raise AdoptionError(f"{name} PASS requires direct evidence")
        if not stage.get("evidence"):
            raise AdoptionError(f"{name} PASS requires evidence")
        if stage.get("observed_environment") != stage.get("required_environment"):
            raise AdoptionError(f"{name} environment mismatch")

    human = stages[7]
    if human.get("required") is not True:
        raise AdoptionError("human acceptance must remain required")
    human_pass = human.get("result") == "PASS"
    if human_pass:
        evidence = human.get("evidence") or []
        if human.get("relationship") != "direct" or not evidence:
            raise AdoptionError("human acceptance PASS requires direct evidence")
        if human.get("observed_environment") != human.get("required_environment"):
            raise AdoptionError("human acceptance environment mismatch")
        lowered = " ".join(str(item).lower() for item in evidence)
        if "actions/runs" in lowered or "automated" in lowered or "browser-acceptance" in lowered:
            raise AdoptionError("automated evidence cannot establish human acceptance")
    else:
        if human.get("result") != "INSUFFICIENT" or human.get("relationship") not in {"missing", "proxy", "direct"}:
            raise AdoptionError("human acceptance must remain INSUFFICIENT until direct acceptance exists")
        if lifecycle.get("verified") in {"human-acceptance-received", "complete"}:
            raise AdoptionError("human acceptance cannot be verified without direct human evidence")

    if lifecycle.get("verified") == "complete" and not human_pass:
        raise AdoptionError("Project Reader cannot be lifecycle complete without human acceptance")

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
