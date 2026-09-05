import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "research" / "unseen-generalisation-v1.3"
BASELINE = "1332e0a6baab8b3dd03dff30473ac52edda2b52e"
KNOWN_TUNED = {
    "audiokit/audiokitsynthone",
    "microsoft/ai-for-beginners",
    "cloudflare/cloudflared",
    "armpitpete/project-status-engine",
    "armpitpete/over-my-home",
    "armpitpete/sample-hold-lab",
}
FROZEN_BLOBS = {
    "prototype/comprehension.js": "2d59801ca8ad30875da7ef51415a1b1844c3a92d",
    "prototype/network-corrections.js": "9f1a8788c14732f820c02e9098a5e10e46a014d5",
    "prototype/polish.js": "c329de3b0a92ddc8705504e01f6065c66b7440d3",
}
REQUIRED_STRATA = {
    "application_product",
    "command_line_tool",
    "network_background_service",
    "library_framework",
    "game",
    "hardware_embedded",
    "documentation_reference",
    "course_curriculum",
    "research",
    "dataset",
    "plugin_extension",
    "mixed_reference_collection",
}


def load(name):
    return json.loads((BENCHMARK / name).read_text(encoding="utf-8"))


def git_blob_sha(relative_path):
    return subprocess.check_output(
        ["git", "hash-object", relative_path], cwd=ROOT, text=True
    ).strip()


def test_frozen_production_interpretation_blobs_are_unchanged():
    for relative_path, expected in FROZEN_BLOBS.items():
        assert git_blob_sha(relative_path) == expected


def test_manifest_is_frozen_to_v12_baseline_and_excludes_known_tuned_repositories():
    manifest = load("manifest.json")
    assert manifest["baseline_project_reader_main"] == BASELINE
    assert manifest["production_feature_freeze"] is True
    assert len(manifest["repositories"]) == 30
    assert len({item["id"] for item in manifest["repositories"]}) == 30
    assert len({item["repository"].lower() for item in manifest["repositories"]}) == 30
    assert not ({item["repository"].lower() for item in manifest["repositories"]} & KNOWN_TUNED)


def test_active_expected_corpus_has_30_unique_records_and_all_required_strata():
    expected = load("expected-readings.json")
    assert expected["baseline_project_reader_main"] == BASELINE
    assert len(expected["records"]) == 30

    ids = [item["id"] for item in expected["records"]]
    repos = [item["repository"].lower() for item in expected["records"]]
    assert len(ids) == len(set(ids)) == 30
    assert len(repos) == len(set(repos)) == 30
    assert not (set(repos) & KNOWN_TUNED)
    assert REQUIRED_STRATA <= {item["stratum"] for item in expected["records"]}

    # Frozen U03 no longer resolves and must remain historical rather than being
    # silently rewritten; U03R1 is the separately frozen pre-evaluation replacement.
    assert "U03" not in ids
    assert "U03R1" in ids
    replacement = next(item for item in expected["records"] if item["id"] == "U03R1")
    assert replacement["repository"].lower() == "audacity/audacity"


def test_expected_records_are_broad_and_have_explicit_wrong_claim_guardrails():
    expected = load("expected-readings.json")
    for item in expected["records"]:
        assert item["acceptable_types"]
        assert len(item["core_purpose"].strip()) >= 10
        assert isinstance(item["useful_actions"], list)
        assert isinstance(item["central_capabilities"], list)
        assert isinstance(item["explicit_limits_or_unfinished"], list)
        assert item["materially_wrong_claims"]
        assert item["source"].startswith("https://github.com/")


def test_benchmark_runner_is_validation_safe_and_targets_exactly_the_expected_records():
    runner = (ROOT / "scripts" / "run_unseen_generalisation_benchmark.mjs").read_text(encoding="utf-8")
    assert BASELINE in runner
    assert "--validate-only" in runner
    assert "expected-readings.json" in runner
    assert "buildComprehension" in runner
    assert "polishReading" in runner
    assert "correctNetworkServiceReading" in runner
    assert 'method: "POST"' not in runner
    assert "writeFile" in runner
    assert "PROJECT_READER_GITHUB_TOKEN" in runner
