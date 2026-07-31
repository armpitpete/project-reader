from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


KIT_RELATIVE = Path("research/external-comprehension-v0.1")
KIT_VERSION = "external-comprehension-v0.1"
SCHEMA_VERSION = 2
RECORD_IDS = tuple(f"R0{index}" for index in range(1, 6))
LOCKED_REPOSITORY = "armpitpete/sample-hold-lab"
LOCKED_REPOSITORY_URL = "https://github.com/armpitpete/sample-hold-lab"
PROJECT_READER_URL = "https://armpitpete.github.io/project-reader/"
BASELINE_MAX_SECONDS = 180
LOCKED_OFFER_ID = "owner-ready-report-25-gbp"

MATCHED_ANSWER_FIELDS = (
    "project_purpose",
    "completed_work",
    "remaining_or_uncertain_work",
    "perceived_completion_state",
    "perceived_likelihood_of_finishing",
    "evidence_trust_basis",
    "ability_to_answer",
    "confidence_if_expressed",
)
MATCHED_QUESTION_TEXT = (
    "In your own words, what is this project?",
    "What, if anything, appears finished?",
    "What, if anything, appears unfinished or uncertain?",
    "How complete do you think it is? Use your own words; a percentage is not required.",
    "How likely do you think the current plan is to be finished?",
    "What evidence makes you trust or distrust those answers?",
)
MATCHED_COMPARISON_FIELDS = (
    "understanding_change",
    "corrected_misunderstanding",
    "new_unsupported_certainty",
    "trust_change",
    "project_reader_enabled_answer",
    "facilitator_interpretation_basis",
)

REQUIRED_DOC_PHRASES = {
    "FACILITATOR_GUIDE.md": (
        "approximately 15-20 minutes",
        "Project Reader is being tested, not the participant",
        "Do not explain the repository, GitHub, or Project Reader answers before the participant has tried each step.",
        LOCKED_REPOSITORY,
        LOCKED_REPOSITORY_URL,
        "Allow up to three minutes of natural inspection",
        "Context Questions",
        "Before Project Reader: Ordinary GitHub Baseline",
        "After Project Reader: Matched Questions",
        "Record confidence only if the participant naturally expresses it",
        "Do not ask leading prompts",
    ),
    "PARTICIPANT_SHEET.md": (
        "Project Reader is being tested, not you",
        "You can stop at any time",
        PROJECT_READER_URL,
        LOCKED_REPOSITORY_URL,
        "up to three minutes",
        "Answer the same six questions again",
        "There are no right or wrong answers",
    ),
    "SCORING_AND_DECISION_METHOD.md": (
        "not a scientifically validated scale",
        "not population research",
        LOCKED_REPOSITORY,
        "`clearer`",
        "`unchanged`",
        "`less_clear`",
        "`incomparable`",
        "new unsupported certainty",
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
        LOCKED_REPOSITORY,
        "Matched Question Comparison",
        "Observed Facts",
        "Participant Statements",
        "Facilitator Interpretation",
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
    ("comprehension_repository", "owner_repo"),
    ("comprehension_repository", "github_url"),
    ("comprehension_repository", "project_reader_input"),
    ("baseline_github_inspection", "repository_page_url"),
    ("project_reader_use", "project_reader_url"),
    ("project_reader_use", "repository_used"),
    ("paid_outcome", "locked_offer_id"),
}
ALLOWED_TRUE_PATHS = {
    ("comprehension_repository", "locked_for_sessions"),
    ("do_not_commit_completed_record",),
}
ALLOWED_NUMBER_PATHS = {
    ("schema_version",),
    ("baseline_github_inspection", "maximum_inspection_seconds"),
}
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

    guide_text = (kit_dir / "FACILITATOR_GUIDE.md").read_text(encoding="utf-8")
    for question in MATCHED_QUESTION_TEXT:
        _require(
            guide_text.count(question) >= 2,
            errors,
            f"FACILITATOR_GUIDE.md must ask matched question before and after Project Reader: {question}",
        )

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


def validate_matched_answers(record: dict[str, Any], section: str) -> list[str]:
    errors: list[str] = []
    answers = record.get(section)
    if not isinstance(answers, dict):
        return [f"{section} must be an object"]

    _require(
        tuple(answers.keys()) == MATCHED_ANSWER_FIELDS,
        errors,
        f"{section} must contain the six matched fields plus ability and natural confidence",
    )
    for field in MATCHED_ANSWER_FIELDS:
        _require(answers.get(field) is None, errors, f"blank records must leave {section}.{field} empty")

    return errors


def validate_record_shape(record: dict[str, Any], expected_id: str | None = None) -> list[str]:
    errors: list[str] = []

    required_top_level = {
        "schema_version",
        "kit_version",
        "participant_id",
        "record_status",
        "comprehension_repository",
        "participant_context",
        "context_questions",
        "consent",
        "baseline_github_inspection",
        "before_project_reader",
        "project_reader_use",
        "after_project_reader",
        "usability_follow_up",
        "paid_outcome",
        "facilitator_notes",
        "participant_statements",
        "matched_comparison_after_session",
        "interpretation_after_session",
        "do_not_commit_completed_record",
    }
    _require(set(record) == required_top_level, errors, "record top-level keys do not match the schema")
    if errors:
        return errors

    _require(record["schema_version"] == SCHEMA_VERSION, errors, f"record schema_version must be {SCHEMA_VERSION}")
    _require(record["kit_version"] == KIT_VERSION, errors, "record kit_version is wrong")
    _require(record["participant_id"] in RECORD_IDS, errors, "participant_id must be R01-R05")
    if expected_id is not None:
        _require(record["participant_id"] == expected_id, errors, f"record ID must be {expected_id}")
    _require(record["record_status"] == "blank_template", errors, "checked-in records must be blank_template")
    _require(record["do_not_commit_completed_record"] is True, errors, "records must warn against committing completed data")

    repository = record["comprehension_repository"]
    _require(
        repository == {
            "owner_repo": LOCKED_REPOSITORY,
            "github_url": LOCKED_REPOSITORY_URL,
            "project_reader_input": LOCKED_REPOSITORY,
            "locked_for_sessions": True,
        },
        errors,
        f"records must lock the common comprehension repository to {LOCKED_REPOSITORY}",
    )

    categories = record["participant_context"].get("self_described_categories")
    _require(categories == [], errors, "blank records must not prefill participant categories")
    if isinstance(categories, list):
        unexpected = set(categories) - ALLOWED_CATEGORY_VALUES
        _require(not unexpected, errors, f"unexpected participant category values: {sorted(unexpected)}")

    _require(
        tuple(record["context_questions"].keys()) == ("github_comfort", "general_tool_trust_or_distrust_factors"),
        errors,
        "GitHub comfort and general trust must stay in separate context questions",
    )
    _require(
        all(value is None for value in record["context_questions"].values()),
        errors,
        "blank records must not prefill context answers",
    )

    baseline = record["baseline_github_inspection"]
    _require(baseline.get("repository_page_url") == LOCKED_REPOSITORY_URL, errors, "baseline must use the locked GitHub repository page")
    _require(baseline.get("maximum_inspection_seconds") == BASELINE_MAX_SECONDS, errors, "baseline inspection must be capped at three minutes")
    _require(baseline.get("time_used_seconds") is None, errors, "blank records must not prefill baseline time used")
    _require(baseline.get("help_requested") is None, errors, "blank records must not prefill baseline help requested")
    _require(baseline.get("help_given") is None, errors, "blank records must not prefill baseline help given")

    errors.extend(validate_matched_answers(record, "before_project_reader"))
    errors.extend(validate_matched_answers(record, "after_project_reader"))

    use = record["project_reader_use"]
    _require(use.get("project_reader_url") == PROJECT_READER_URL, errors, "Project Reader URL is wrong")
    _require(use.get("repository_used") == LOCKED_REPOSITORY, errors, "Project Reader use must keep the locked repository")
    for field in (
        "session_completed",
        "task_outcome",
        "help_requested",
        "first_screen_comprehension",
        "time_to_first_useful_answer_seconds",
    ):
        _require(use.get(field) is None, errors, f"blank records must leave project_reader_use.{field} empty")

    for section_name in ("usability_follow_up", "matched_comparison_after_session", "interpretation_after_session"):
        section = record[section_name]
        _require(all(value is None for value in section.values()), errors, f"blank records must leave {section_name} empty")

    comparison = record["matched_comparison_after_session"]
    _require(tuple(comparison.keys()) == MATCHED_COMPARISON_FIELDS, errors, "matched comparison fields are incomplete")

    paid = record["paid_outcome"]
    _require(paid.get("locked_offer_id") == LOCKED_OFFER_ID, errors, "paid_outcome locked offer id is wrong")
    _require(paid.get("result") is None, errors, "blank records must not prefill paid-outcome results")

    for collection_path in (
        ("project_reader_use", "disclosure_controls_opened"),
        ("project_reader_use", "hesitation_or_confusion_events"),
        ("project_reader_use", "misunderstandings"),
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
        elif isinstance(value, int) and path not in ALLOWED_NUMBER_PATHS:
            errors.append(f"blank record contains a prefilled number at {_path_text(path)}")

    return errors


def validate_schema(kit_dir: Path) -> list[str]:
    errors: list[str] = []
    schema = _load_json(kit_dir / "RECORD_SCHEMA.json")

    _require(schema.get("title") == "Project Reader External Comprehension Session Record", errors, "schema title is wrong")
    _require(schema["properties"]["schema_version"]["const"] == SCHEMA_VERSION, errors, "schema_version const is wrong")
    participant_enum = schema["properties"]["participant_id"]["enum"]
    _require(tuple(participant_enum) == RECORD_IDS, errors, "schema participant IDs must be R01-R05")
    _require(
        schema["properties"]["comprehension_repository"]["properties"]["owner_repo"]["const"] == LOCKED_REPOSITORY,
        errors,
        "schema must lock the common comprehension repository",
    )
    _require(
        schema["properties"]["baseline_github_inspection"]["properties"]["maximum_inspection_seconds"]["const"] == BASELINE_MAX_SECONDS,
        errors,
        "schema must cap baseline inspection at three minutes",
    )
    _require(
        schema["properties"]["before_project_reader"]["$ref"] == "#/$defs/matched_answers",
        errors,
        "schema before_project_reader must use matched answers",
    )
    _require(
        schema["properties"]["after_project_reader"]["$ref"] == "#/$defs/matched_answers",
        errors,
        "schema after_project_reader must use matched answers",
    )
    _require(
        tuple(schema["$defs"]["matched_answers"]["required"]) == MATCHED_ANSWER_FIELDS,
        errors,
        "schema matched answers are missing required fields",
    )
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

    repositories = {
        _load_json(path)["comprehension_repository"]["owner_repo"]
        for path in record_paths
        if path.is_file()
    }
    _require(repositories == {LOCKED_REPOSITORY}, errors, "R01-R05 must all use the same locked comprehension repository")

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

    print("External comprehension field-test kit validates: matched baseline, 5 blank records, locked repository, locked offer, and required materials.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
