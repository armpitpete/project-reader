from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CURRENT_MAIN = "71685832a9378d2f74ab22294416d67475f368e3"
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


def test_pinned_canonical_validator_accepts_current_record():
    status, _ = load_records()
    MODULE.CANONICAL.validate(status)


def test_current_finish_line_and_pass_evidence_cover_current_product_state():
    status, _ = load_records()
    lifecycle = status["lifecycle_status"]
    stages = {stage["stage"]: stage for stage in lifecycle["stages"]}

    assert CURRENT_MAIN in status["finish_line"]
    assert CURRENT_MAIN in stages["designed"]["required_environment"]
    assert CURRENT_MAIN in stages["implemented"]["required_environment"]
    assert "issue #41 scope" not in stages["designed"]["required_environment"].lower()
    assert "issue #41 scope" not in stages["implemented"]["required_environment"].lower()
    assert lifecycle["verified"] == "insufficient"
    assert stages["independent-review"]["result"] == "INSUFFICIENT"
    assert stages["human-acceptance"]["result"] == "INSUFFICIENT"


def test_percentage_100_is_rejected_when_remaining_work_is_declared():
    status, progress = load_records()
    status = copy.deepcopy(status)
    status["percentage_complete"]["estimate"] = 100
    with pytest.raises(AdoptionError, match="100 percent planning progress"):
        validate_adoption(status, progress)


def test_proxy_substitution_cannot_create_pass():
    status, progress = load_records()
    status = copy.deepcopy(status)
    status["lifecycle_status"]["stages"][5]["relationship"] = "proxy"
    with pytest.raises(AdoptionError, match="canonical Project Status rejection: deployed PASS requires direct evidence"):
        validate_adoption(status, progress)


def test_environment_mismatch_is_rejected():
    status, progress = load_records()
    status = copy.deepcopy(status)
    status["lifecycle_status"]["stages"][6]["observed_environment"] = "fixture"
    with pytest.raises(AdoptionError, match="canonical Project Status rejection: live-behaviour PASS must exercise required environment"):
        validate_adoption(status, progress)


def test_automated_browser_acceptance_is_not_human_acceptance():
    status, progress = load_records()
    status = copy.deepcopy(status)
    human = status["lifecycle_status"]["stages"][7]
    human["result"] = "PASS"
    human["relationship"] = "direct"
    human["observed_environment"] = human["required_environment"]
    human["evidence"] = ["https://github.com/armpitpete/project-reader/actions/runs/31487906093#live-browser-acceptance"]
    with pytest.raises(AdoptionError, match="automated evidence cannot establish human acceptance"):
        validate_adoption(status, progress)


def test_local_path_cannot_accept_record_rejected_by_canonical_validator():
    status, progress = load_records()
    status = copy.deepcopy(status)
    status["lifecycle_status"]["claimed"] = "complete"
    status["lifecycle_status"]["verified"] = "live-behaviour-verified"
    with pytest.raises(AdoptionError, match="canonical Project Status rejection: lifecycle_status.verified must be 'insufficient'"):
        validate_adoption(status, progress)


def test_human_acceptance_alone_cannot_bypass_missing_independent_review():
    status, progress = load_records()
    status = copy.deepcopy(status)
    human = status["lifecycle_status"]["stages"][7]
    human["result"] = "PASS"
    human["relationship"] = "direct"
    human["observed_environment"] = human["required_environment"]
    human["evidence"] = ["human:explicit-current-live-experience-acceptance-fixture"]
    status["lifecycle_status"]["claimed"] = "complete"
    status["lifecycle_status"]["verified"] = "complete"
    with pytest.raises(AdoptionError, match="canonical Project Status rejection: lifecycle_status.verified must be 'insufficient'"):
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
