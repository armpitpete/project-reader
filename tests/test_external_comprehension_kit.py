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
        assert record["participant_statements"] == []
        assert record["facilitator_notes"] == []
        assert record["paid_outcome"]["result"] is None
        assert record["do_not_commit_completed_record"] is True


def test_validator_rejects_fabricated_blank_participant_statement() -> None:
    record = copy.deepcopy(load_record("R01"))
    record["after_use"]["project_purpose"] = "The participant understood everything."

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
    assert "Interpretation" in text
    assert "Decision" in text
    assert "Do not hide individual failures." in text
    assert "not population research" in text
