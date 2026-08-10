from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate_real_thing_adoption.py"
SPEC = importlib.util.spec_from_file_location("validate_real_thing_adoption", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
AdoptionError = MODULE.AdoptionError
validate_adoption = MODULE.validate_adoption


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
    with pytest.raises(
        AdoptionError,
        match="human acceptance cannot be verified without direct human evidence|cannot be lifecycle complete without human acceptance",
    ):
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


def test_future_direct_human_acceptance_can_advance_without_validator_change():
    status, progress = load_records()
    status = copy.deepcopy(status)
    human = status["lifecycle_status"]["stages"][7]
    human["result"] = "PASS"
    human["relationship"] = "direct"
    human["observed_environment"] = human["required_environment"]
    human["evidence"] = ["human:explicit-live-experience-acceptance-fixture"]
    status["lifecycle_status"]["claimed"] = "complete"
    status["lifecycle_status"]["verified"] = "complete"
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
