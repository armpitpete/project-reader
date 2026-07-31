import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_external_comprehension_kit",
    ROOT / "scripts" / "validate_external_comprehension_kit.py",
)
assert SPEC is not None and SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def load_record(record_id: str) -> dict:
    return json.loads(
        (ROOT / "research" / "external-comprehension-v0.1" / "records" / f"{record_id}.json").read_text(
            encoding="utf-8"
        )
    )


def test_external_comprehension_kit_validates() -> None:
    assert validator.validate_kit(ROOT) == []


def test_blank_records_are_anonymous_empty_templates() -> None:
    for record_id in validator.RECORD_IDS:
        record = load_record(record_id)
        assert record["participant_id"] == record_id
        assert record["record_status"] == "blank_template"
        assert record["participant_context"]["self_described_categories"] == []
        assert record["context_questions"] == {
            "github_comfort": None,
            "general_tool_trust_or_distrust_factors": None,
        }
        assert record["participant_statements"] == []
        assert record["facilitator_notes"] == []
        assert record["paid_outcome"]["result"] is None
        assert record["matched_comparison_after_session"]["understanding_change"] is None
        assert record["do_not_commit_completed_record"] is True


def test_records_lock_same_comprehension_repository_for_r01_to_r05() -> None:
    for record_id in validator.RECORD_IDS:
        record = load_record(record_id)
        assert record["comprehension_repository"] == {
            "owner_repo": "armpitpete/sample-hold-lab",
            "github_url": "https://github.com/armpitpete/sample-hold-lab",
            "project_reader_input": "armpitpete/sample-hold-lab",
            "locked_for_sessions": True,
        }
        assert record["baseline_github_inspection"]["repository_page_url"] == (
            "https://github.com/armpitpete/sample-hold-lab"
        )
        assert record["project_reader_use"]["repository_used"] == "armpitpete/sample-hold-lab"


def test_records_have_same_six_matched_fields_before_and_after_project_reader() -> None:
    expected = set(validator.MATCHED_ANSWER_FIELDS)

    for record_id in validator.RECORD_IDS:
        record = load_record(record_id)
        assert set(record["before_project_reader"]) == expected
        assert set(record["after_project_reader"]) == expected
        assert record["before_project_reader"] == record["after_project_reader"]


def test_schema_requires_matched_before_and_after_fields() -> None:
    schema = json.loads(
        (ROOT / "research" / "external-comprehension-v0.1" / "RECORD_SCHEMA.json").read_text(encoding="utf-8")
    )

    assert schema["properties"]["before_project_reader"]["$ref"] == "#/$defs/matched_answers"
    assert schema["properties"]["after_project_reader"]["$ref"] == "#/$defs/matched_answers"
    assert tuple(schema["$defs"]["matched_answers"]["required"]) == validator.MATCHED_ANSWER_FIELDS


def test_facilitator_guide_asks_six_questions_before_and_after() -> None:
    text = (
        ROOT / "research" / "external-comprehension-v0.1" / "FACILITATOR_GUIDE.md"
    ).read_text(encoding="utf-8")

    for question in validator.MATCHED_QUESTION_TEXT:
        assert text.count(question) >= 2
    assert "Do not ask the participant to guess what \"Project Reader\" might do." in text


def test_baseline_inspection_is_capped_at_three_minutes() -> None:
    record = load_record("R01")

    assert record["baseline_github_inspection"]["maximum_inspection_seconds"] == 180

    changed = copy.deepcopy(record)
    changed["baseline_github_inspection"]["maximum_inspection_seconds"] = 181
    errors = validator.validate_record_shape(changed, expected_id="R01")

    assert any("three minutes" in error for error in errors)


def test_validator_rejects_missing_matched_baseline_field() -> None:
    record = copy.deepcopy(load_record("R01"))
    del record["before_project_reader"]["perceived_likelihood_of_finishing"]

    errors = validator.validate_record_shape(record, expected_id="R01")

    assert any("six matched fields" in error for error in errors)


def test_validator_rejects_repository_drift_between_sessions() -> None:
    record = copy.deepcopy(load_record("R01"))
    record["comprehension_repository"]["owner_repo"] = "armpitpete/other-project"

    errors = validator.validate_record_shape(record, expected_id="R01")

    assert any("common comprehension repository" in error for error in errors)


def test_validator_rejects_fabricated_blank_participant_statement() -> None:
    record = copy.deepcopy(load_record("R01"))
    record["after_project_reader"]["project_purpose"] = "The participant understood everything."

    errors = validator.validate_record_shape(record, expected_id="R01")

    assert any("participant evidence" in error for error in errors)


def test_validator_rejects_personal_identifier_fields() -> None:
    record = copy.deepcopy(load_record("R01"))
    record["participant_name"] = "Example Person"

    errors = validator.validate_record_shape(record, expected_id="R01")

    assert any("top-level keys" in error for error in errors)


def test_validator_rejects_prefilled_commercial_outcome() -> None:
    record = copy.deepcopy(load_record("R01"))
    record["paid_outcome"]["result"] = "paid"

    errors = validator.validate_record_shape(record, expected_id="R01")

    assert any("paid-outcome results" in error for error in errors)


def test_scoring_distinguishes_comprehension_usability_and_trust() -> None:
    text = (
        ROOT / "research" / "external-comprehension-v0.1" / "SCORING_AND_DECISION_METHOD.md"
    ).read_text(encoding="utf-8")

    assert "### Comprehension" in text
    assert "### Usability" in text
    assert "### Trust" in text
    assert "### Paid Outcome" in text
    assert "`clearer`" in text
    assert "new unsupported certainty" in text


def test_paid_outcome_card_uses_locked_single_offer_without_payment_infrastructure() -> None:
    text = (
        ROOT / "research" / "external-comprehension-v0.1" / "PAID_OUTCOME_TEST.md"
    ).read_text(encoding="utf-8")

    assert "Owner-ready Project Reader report - £25 trial price" in text
    assert "one supported public GitHub repository" in text
    assert "`paid`" in text
    assert "`explicit_commitment`" in text
    assert "`refused`" in text
    assert "Stripe" not in text
    assert "PayPal" not in text
    assert "checkout" not in text.lower()


def test_summary_template_keeps_facts_quotes_interpretation_and_decisions_separate() -> None:
    text = (
        ROOT / "research" / "external-comprehension-v0.1" / "SUMMARY_TEMPLATE.md"
    ).read_text(encoding="utf-8")

    assert "Observed Facts" in text
    assert "Participant Statements" in text
    assert "Facilitator Interpretation" in text
    assert "Decision" in text
    assert "Do not hide individual failures." in text
    assert "not population research" in text
