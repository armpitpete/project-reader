from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from project_reader.interpretation import InterpretationError, interpret_evidence_bundle
from project_reader.reading import build_project_reading
from project_reader.render import render_html


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a complete Project Reader page from one v0.3 evidence bundle."
    )
    parser.add_argument("evidence", type=Path, help="v0.3 evidence JSON file")
    parser.add_argument("--output", type=Path, required=True, help="HTML file to write")
    parser.add_argument("--name", help="Optional display name for the project")
    parser.add_argument("--contact-url", help="Optional contact URL for the project owner")
    args = parser.parse_args()

    try:
        payload = json.loads(args.evidence.read_text(encoding="utf-8"))
        interpretation = interpret_evidence_bundle(payload)
        reading = build_project_reading(
            interpretation,
            project_name=args.name,
            contact_url=args.contact_url,
        )
        render_html(reading, args.output)
    except (OSError, json.JSONDecodeError, InterpretationError, ValueError) as error:
        parser.exit(2, f"Project Reader: {error}\n")

    print(
        f"Wrote {args.output} for {interpretation.repository} at "
        f"{interpretation.source_commit}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
