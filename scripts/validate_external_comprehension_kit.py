from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


KIT_RELATIVE = Path("research/external-comprehension-v0.1")
KIT_VERSION = "external-comprehension-v0.1"
RECORD_IDS = tuple(f"R0{index}" for index in range(1, 6))
LOCKED_OFFER_ID = "owner-ready-report-25-gbp"

REQUIRED_DOC_PHRASES = {
    "FACILITATOR_GUIDE.md": (
        "approximately 10-15 minutes",
        "Project Reader is being tested, not the participant",
        "Do not explain the answers before the participant has tried the site.",
        "Before-Use Questions",
        "Observation Prompts During Use",
        "After-Use Questions",
        "Do not record names, email addresses",
        "Do not ask leading prompts",
    ),
    "PARTICIPANT_SHEET.md": (
        "Project Reader is being tested, not you",
        "You can stop at any time",
        "https://armpitpete.github.io/project-reader/",
        "There are no right or wrong answers",
    ),
    "SCORING_AND_DECISION_METHOD.md": (
        "not a scientifically validated scale",
        "not population research",
        "Comprehension",
        "Usability",
        "Trust",
        "`keep`",
        "`correct`",
        "`expand`",
        "`pause`",
        "`retire`",
    ),
    "PAID_OUTCOME_TEST.md": (
        "Owner-ready Project Reader report - £25 trial price",
        "one supported public GitHub repository",
        "within three working days",
        "one factual correction pass",
        "`paid`",
        "`explicit_commitment`",
        "`refused`",
        "Do not create a payment link.",
    ),
    "SUMMARY_TEMPLATE.md": (
        "R01",
        "R02",
        "R03",
        "R04",
        "R05",
        "Observed Facts",
        "Participant Statements",
        "Interpretation",
        "directional product evidence",
    ),
}

FORBIDDEN_PERSONAL_KEY_PARTS = (
    "name",
    "email",
    "phone",
    "address",
    "diagnosis",
    "medical",
    "medication",
    "school",
    "workplace",
)
ALLOWED_CATEGORY_VALUES = {
    "non_technical",
    "young_person",
    "neurodivergent",
    "overlapping_categories",
}
ALLOWED_NON_EMPTY_STRING_PATHS = {
    ("kit_version",),
    ("participant_id",),
    ("record_status",),
    ("paid_outcome", "locked_offer_id"),
}
ALLOWED_TRUE_PATHS = {("do_not_commit_completed_record",)}
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"\b(?:\+?\d[\s().-]*){8,}\b")
PRIVATE_SECRET_RE = re.compile(
    r"BEGIN (?:OPENSSH|RSA|EC|DSA)? ?PRIVATE KEY|ghp_|github_pat_|sk-[A-Za-z0-9]",
    re.I,
)


class KitValidationError(ValueError):
    """Raised when the external comprehension kit is unsafe or incomplete."""


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _walk(value: Any, path: tuple[str, ...] = ()) -> list[tuple[tuple[str, ...], Any]]:
    items = [(path, value)]
    if isinstance(value, dict):
        for key, child in value.items():
            items.extend(_walk(child, path + (str(key),)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            items.extend(_walk(child, path + (str(index),)))
    return items


def _path_text(path: tuple[str, ...]) -> str:
    return ".".join(path)


def _require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def validate_documents(kit_dir: Path) -> list[str]:
    errors: list[str] = []

    for filename, phrases in REQUIRED_DOC_PHRASES.items():
        path = kit_dir / filename
        if not path.is_file():
            errors.append(f"missing required document: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in text:
                errors.append(f"{filename} is missing required phrase: {phrase}")

    paid_text = (kit_dir / "PAID_OUTCOME_TEST.md").read_text(encoding="utf-8")
    _require(
        paid_text.count("Owner-ready Project Reader report - £25 trial price") == 1,
        errors,
        "paid test must describe exactly one locked offer title",
    )
    _require("£25" in paid_text, errors, "paid test must preserve the locked £25 trial price")
    for forbidden in ("Stripe", "PayPal", "checkout", "subscription", "retainer"):
        _require(forbidden.lower() not in paid_text.lower(), errors, f"paid test must not introduce {forbidden}")

    return errors


def validate_record_shape(record: dict[str, Any], expected_id: str | None = None) -> list[str]:
    errors: list[str] = []

    required_top_level = {
        "schema_version",
        "kit_version",
        "participant_id",
        "record_status",
        "participant_context",
        "consent",
        "before_use",
        "observation",
        "after_use",
        "paid_outcome",
        "facilitator_notes",
        "participant_statements",
        "interpretation_after_session",
        "do_not_commit_completed_record",
    }
    _require(set(record) == required_top_level, errors, "record top-level keys do not match the schema")
    if errors:
        return errors

    _require(record["schema_version"] == 1, errors, "record schema_version must be 1")
    _require(record["kit_version"] == KIT_VERSION, errors, "record kit_version is wrong")
    _require(record["participant_id"] in RECORD_IDS, errors, "participant_id must be R01-R05")
    if expected_id is not None:
        _require(record["participant_id"] == expected_id, errors, f"record ID must be {expected_id}")
    _require(record["record_status"] == "blank_template", errors, "checked-in records must be blank_template")
    _require(record["do_not_commit_completed_record"] is True, errors, "records must warn against committing completed data")

    categories = record["participant_context"].get("self_described_categories")
    _require(categories == [], errors, "blank records must not prefill participant categories")
    if isinstance(categories, list):
        unexpected = set(categories) - ALLOWED_CATEGORY_VALUES
        _require(not unexpected, errors, f"unexpected participant category values: {sorted(unexpected)}")

    paid = record["paid_outcome"]
    _require(paid.get("locked_offer_id") == LOCKED_OFFER_ID, errors, "paid_outcome locked offer id is wrong")
    _require(paid.get("result") is None, errors, "blank records must not prefill paid-outcome results")

    for collection_path in (
        ("observation", "disclosure_controls_opened"),
        ("observation", "hesitation_or_confusion_events"),
        ("observation", "misunderstandings"),
        ("facilitator_notes",),
        ("participant_statements",),
    ):
        value: Any = record
        for part in collection_path:
            value = value[part]
        _require(value == [], errors, f"blank records must leave {_path_text(collection_path)} empty")

    for path, value in _walk(record):
        if path and any(part.lower() in FORBIDDEN_PERSONAL_KEY_PARTS for part in path):
            errors.append(f"record contains forbidden personal-data field: {_path_text(path)}")
        if isinstance(value, str):
            if value and path not in ALLOWED_NON_EMPTY_STRING_PATHS:
                errors.append(f"blank record contains participant evidence at {_path_text(path)}")
            if EMAIL_RE.search(value):
                errors.append(f"record contains an email-like value at {_path_text(path)}")
            if PHONE_RE.search(value):
                errors.append(f"record contains a phone-like value at {_path_text(path)}")
            if PRIVATE_SECRET_RE.search(value):
                errors.append(f"record contains secret-like material at {_path_text(path)}")
        elif isinstance(value, bool):
            if value is True and path not in ALLOWED_TRUE_PATHS:
                errors.append(f"blank record contains a prefilled boolean at {_path_text(path)}")
            if value is False:
                errors.append(f"blank record contains a prefilled false boolean at {_path_text(path)}")
        elif isinstance(value, int) and path not in {("schema_version",)}:
            errors.append(f"blank record contains a prefilled number at {_path_text(path)}")

    return errors


def validate_schema(kit_dir: Path) -> list[str]:
    errors: list[str] = []
    schema = _load_json(kit_dir / "RECORD_SCHEMA.json")

    _require(schema.get("title") == "Project Reader External Comprehension Session Record", errors, "schema title is wrong")
    participant_enum = schema["properties"]["participant_id"]["enum"]
    _require(tuple(participant_enum) == RECORD_IDS, errors, "schema participant IDs must be R01-R05")
    paid_enum = set(schema["properties"]["paid_outcome"]["properties"]["result"]["enum"])
    _require({"paid", "explicit_commitment", "refused", "not_offered", None} == paid_enum, errors, "schema paid result enum is wrong")
    _require(
        schema["properties"]["paid_outcome"]["properties"]["locked_offer_id"]["const"] == LOCKED_OFFER_ID,
        errors,
        "schema locked offer id is wrong",
    )

    return errors


def validate_records(kit_dir: Path) -> list[str]:
    errors: list[str] = []
    records_dir = kit_dir / "records"
    record_paths = sorted(records_dir.glob("R??.json"))

    _require([path.stem for path in record_paths] == list(RECORD_IDS), errors, "records must be exactly R01.json through R05.json")
    for path in record_paths:
        loaded = _load_json(path)
        if not isinstance(loaded, dict):
            errors.append(f"{path} must contain a JSON object")
            continue
        errors.extend(f"{path.name}: {error}" for error in validate_record_shape(loaded, expected_id=path.stem))

    return errors


def validate_kit(root: Path) -> list[str]:
    kit_dir = root / KIT_RELATIVE
    errors: list[str] = []

    if not kit_dir.is_dir():
        return [f"missing kit directory: {kit_dir}"]

    errors.extend(validate_documents(kit_dir))
    errors.extend(validate_schema(kit_dir))
    errors.extend(validate_records(kit_dir))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the external comprehension field-test kit.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    errors = validate_kit(args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("External comprehension field-test kit validates: 5 blank records, locked offer, and required materials.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
