from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from project_reader.interpretation import (
    InterpretationError,
    interpret_evidence_bundle,
    write_interpretation_bundle,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Produce reviewable candidate interpretations from one v0.3 evidence bundle."
    )
    parser.add_argument("evidence", type=Path, help="v0.3 evidence JSON file")
    parser.add_argument("--output", type=Path, required=True, help="interpretation JSON file to write")
    args = parser.parse_args()

    try:
        payload = json.loads(args.evidence.read_text(encoding="utf-8"))
        result = interpret_evidence_bundle(payload)
        write_interpretation_bundle(result, args.output)
    except (OSError, json.JSONDecodeError, InterpretationError) as error:
        parser.exit(2, f"Project Reader: {error}\n")

    print(
        f"Wrote {args.output} for {result.repository} at {result.source_commit} "
        f"with {len(result.done)} done candidate(s), "
        f"{len(result.remaining)} remaining candidate(s), and "
        f"{len(result.conflicts)} conflict(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
