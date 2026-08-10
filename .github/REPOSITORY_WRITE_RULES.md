# Repository Write Rules

This repository follows Threadkeeper's canonical repository-write policy and consumes the canonical Real-Thing Proof / Project Status v2 control without redefining it.

## Exact authorities

- Threadkeeper repository-write and Real-Thing Proof authority: `armpitpete/threadkeeper@a5bc55336c86097301b378d8654ac92a26ef81e5`
- Project Status v2 authority: `armpitpete/merrin-project-controls@7bc8b7f5ef921851ad163093f089d28d8128bf6c`
- Canonical schema: `schemas/project-status.schema.json`
- Canonical semantic validator: `scripts/validate_project_status.py`
- Local lifecycle record: `project-status.json`

Local checks may verify Project Reader's exact adoption record and evidence pointers. They must not create a competing lifecycle vocabulary or weaken the canonical semantics.

## Governing rule

> Never test a proxy when the claim concerns the real thing. Never allow `complete` to absorb implementation, deployment, live verification and human acceptance into one vague word.

Planning percentages and bounded release-stage counts are not lifecycle proof. Automated browser acceptance is automated evidence and must not be relabelled as human acceptance.

## Existing write boundary

The canonical Threadkeeper policy continues to govern exact-SHA branch writes, narrow operations, non-force updates, bounded recovery and evidence recording. This repository-specific notice strengthens that policy only by pinning the lifecycle authorities above.
