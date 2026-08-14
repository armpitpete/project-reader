#!/usr/bin/env python3
"""Validate project-status records without inflating planning estimates into completion."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

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
STATUS_TO_STAGE = {
    "designed": "designed",
    "implemented": "implemented",
    "automated-checks-passed": "automated-checks",
    "independently-reviewed": "independent-review",
    "merged": "merged",
    "deployed": "deployed",
    "live-behaviour-verified": "live-behaviour",
    "human-acceptance-received": "human-acceptance",
}


class StatusError(ValueError):
    pass


def _expected_verified(claimed: str, stages: dict[str, dict[str, Any]]) -> str:
    required = [name for name in STAGES if stages[name]["required"]]
    if not required:
        raise StatusError("at least one lifecycle stage must be required")
    relevant = required if claimed == "complete" else [
        name for name in required if STAGES.index(name) <= STAGES.index(STATUS_TO_STAGE[claimed])
    ]
    if claimed != "complete" and not stages[STATUS_TO_STAGE[claimed]]["required"]:
        return "insufficient"
    if any(stages[name]["result"] == "FAIL" for name in relevant):
        return "failed"
    if all(
        stages[name]["result"] == "PASS"
        and stages[name]["relationship"] == "direct"
        and stages[name].get("observed_environment") == stages[name].get("required_environment")
        for name in relevant
    ):
        return "complete" if claimed == "complete" else claimed
    return "insufficient"


def validate(record: Any) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise StatusError("project status must be an object")
    for field in ("project", "finish_line", "percentage_complete", "completion_likelihood", "lifecycle_status", "next_bounded_action"):
        if field not in record:
            raise StatusError(f"missing required field: {field}")

    progress = record["percentage_complete"]
    if not isinstance(progress, dict) or not isinstance(progress.get("estimate"), (int, float)):
        raise StatusError("percentage_complete.estimate must be numeric")
    if not 0 <= progress["estimate"] <= 100:
        raise StatusError("percentage_complete.estimate must be between 0 and 100")

    status = record["lifecycle_status"]
    if not isinstance(status, dict):
        raise StatusError("lifecycle_status must be an object")
    claimed = status.get("claimed")
    if claimed not in set(STATUS_TO_STAGE) | {"complete"}:
        raise StatusError("unsupported lifecycle_status.claimed")
    raw_stages = status.get("stages")
    if not isinstance(raw_stages, list) or len(raw_stages) != 8:
        raise StatusError("lifecycle_status.stages must contain exactly eight stages")

    stages: dict[str, dict[str, Any]] = {}
    for item in raw_stages:
        if not isinstance(item, dict) or item.get("stage") not in STAGES:
            raise StatusError("unsupported lifecycle stage")
        name = item["stage"]
        if name in stages:
            raise StatusError(f"duplicate lifecycle stage: {name}")
        required = item.get("required")
        result = item.get("result")
        relationship = item.get("relationship")
        evidence = item.get("evidence", [])
        if not isinstance(required, bool):
            raise StatusError(f"{name}.required must be boolean")
        if required:
            if not item.get("required_environment"):
                raise StatusError(f"{name} requires required_environment")
            if result in {"PASS", "FAIL"}:
                if relationship != "direct":
                    raise StatusError(f"{name} {result} requires direct evidence")
                if item.get("observed_environment") != item.get("required_environment"):
                    raise StatusError(f"{name} {result} must exercise required environment")
                if not evidence:
                    raise StatusError(f"{name} {result} requires evidence")
            elif result == "INSUFFICIENT":
                if relationship not in {"direct", "proxy", "missing"}:
                    raise StatusError(f"{name} INSUFFICIENT has invalid relationship")
            else:
                raise StatusError(f"required stage {name} must be PASS, FAIL or INSUFFICIENT")
        else:
            if not item.get("rationale"):
                raise StatusError(f"not-applicable stage {name} requires rationale")
            if result != "NOT_APPLICABLE" or relationship != "not-applicable":
                raise StatusError(f"not-applicable stage {name} has invalid result")
            if evidence or item.get("required_environment") or item.get("observed_environment"):
                raise StatusError(f"not-applicable stage {name} cannot contain evidence or environments")
        stages[name] = item

    missing = [name for name in STAGES if name not in stages]
    if missing:
        raise StatusError("missing lifecycle stages: " + ", ".join(missing))
    expected = _expected_verified(claimed, stages)
    if status.get("verified") != expected:
        raise StatusError(f"lifecycle_status.verified must be {expected!r}")
    return record


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_project_status.py RECORD.json", file=sys.stderr)
        return 2
    path = Path(argv[1])
    try:
        validate(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, StatusError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"valid project status: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
