# Repository Write Rules

This repository follows Threadkeeper's canonical repository-write policy and consumes the canonical Real-Thing Proof / Project Status v2 control without redefining it.

## Exact authorities

- Threadkeeper repository-write and Real-Thing Proof authority: `armpitpete/threadkeeper@a5bc55336c86097301b378d8654ac92a26ef81e5`
- Project Status v2 authority: `armpitpete/merrin-project-controls@7bc8b7f5ef921851ad163093f089d28d8128bf6c`
- Canonical schema at that authority: `schemas/project-status.schema.json`
- Canonical semantic validator at that authority: `scripts/validate_project_status.py`
- Immutable vendored validator snapshot: `vendor/merrin-project-controls/7bc8b7f5ef921851ad163093f089d28d8128bf6c/validate_project_status.py`
- Local lifecycle record: `project-status.json`

CI must execute the vendored canonical validator against `project-status.json` before the Project Reader-specific adoption checks. Local checks are additive only: they may verify Project Reader evidence boundaries and legacy compatibility, but they must not create a competing lifecycle vocabulary, claimed-to-verified derivation, or weaker completion rule.

## Governing rule

> Never test a proxy when the claim concerns the real thing. Never allow `complete` to absorb implementation, deployment, live verification and human acceptance into one vague word.

Planning percentages and bounded release-stage counts are not lifecycle proof. Automated browser acceptance is automated evidence and must not be relabelled as human acceptance.

## Existing write boundary

The canonical Threadkeeper policy continues to govern exact-SHA branch writes, narrow operations, non-force updates, bounded recovery and evidence recording. This repository-specific notice strengthens that policy only by pinning and executing the lifecycle authority above.
