from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.validate_real_thing_adoption import AdoptionError, validate_adoption

ROOT = Path(__file__).resolve().parents[1]


def load_records():
    status = json.loads((ROOT / "project-status.json").read_text(encoding="utf-8"))
    progress = json.loads((ROOT / ".project" / "progress.json").read_text(encoding="utf-8"))
    return status, progress


def test_current_adoption_record_is_valid():
    status, progress = load_records()
    validate_adoption(status, progress)


def test_percentage_100_does_not_create_lifecycle_completion():
    status, progress = load_records()
    status = copy.deepcopy(status)
    status["lifecycle_status"]["verified"] = "complete"
    with pytest.raises(AdoptionError, match="must stop at live-behaviour-verified|planning percentage|cannot be lifecycle complete"):
        validate_adoption(status, progress)


def test_proxy_substitution_cannot_create_pass():
    status, progress = load_records()
    status = copy.deepcopy(status)
    status["lifecycle_status"]["stages"][5]["relationship"] = "proxy"
    with pytest.raises(AdoptionError, match="PASS requires direct evidence"):
        validate_adoption(status, progress)


def test_environment_mismatch_is_rejected():
    status, progress = load_records()
    status = copy.deepcopy(status)
    status["lifecycle_status"]["stages"][6]["observed_environment"] = "fixture"
    with pytest.raises(AdoptionError, match="environment mismatch"):
        validate_adoption(status, progress)


def test_automated_browser_acceptance_is_not_human_acceptance():
    status, progress = load_records()
    status = copy.deepcopy(status)
    human = status["lifecycle_status"]["stages"][7]
    human["result"] = "PASS"
    human["relationship"] = "direct"
    human["observed_environment"] = human["required_environment"]
    human["evidence"] = ["https://github.com/armpitpete/project-reader/actions/runs/30934402526#live-browser-acceptance"]
    with pytest.raises(AdoptionError, match="automated evidence cannot establish human acceptance"):
        validate_adoption(status, progress)


def test_legacy_unqualified_complete_is_rejected():
    status, progress = load_records()
    progress = copy.deepcopy(progress)
    progress["release"]["complete"] = True
    with pytest.raises(AdoptionError, match="unqualified complete"):
        validate_adoption(status, progress)


def test_legacy_release_completion_must_stay_bounded():
    status, progress = load_records()
    progress = copy.deepcopy(progress)
    progress["release"]["completion_scope"] = "complete"
    with pytest.raises(AdoptionError, match="exclude whole-project lifecycle completion"):
        validate_adoption(status, progress)
