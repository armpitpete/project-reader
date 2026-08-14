# Real-Thing Proof consumer v0.1

Project Reader is a deployed downstream consumer of the canonical Real-Thing Proof / Project Status v2 controls.

## Exact authorities

- Threadkeeper: `armpitpete/threadkeeper@a5bc55336c86097301b378d8654ac92a26ef81e5`
- Project Status v2: `armpitpete/merrin-project-controls@7bc8b7f5ef921851ad163093f089d28d8128bf6c`
- Local lifecycle record: `project-status.json`
- Immutable canonical-validator snapshot: `vendor/merrin-project-controls/7bc8b7f5ef921851ad163093f089d28d8128bf6c/validate_project_status.py`

CI executes that pinned validator before Project Reader-specific checks. The local validator is additive only and does not own lifecycle status derivation.

## Current product evidence boundary

The lifecycle record now concerns the **current deployed Project Reader product state**, not the narrow SD-016 sitemap lane by itself.

Current product main before this adoption PR is:

`71685832a9378d2f74ab22294416d67475f368e3`

That state combines:

- the accepted v1.2 public-prototype work tracked through Issue #36 / PR #37;
- the later production sitemap change tracked through Issue #41 / PR #43;
- the privacy-first Merrin Analytics change merged as PR #46.

Direct current-state evidence establishes:

- documented design scope: current ROADMAP plus the bounded sitemap and analytics changes;
- repository implementation: current main `71685832a9378d2f74ab22294416d67475f368e3`;
- automated checks: run `31487906093` and the Pages build/deployment run `31487906058`;
- merge/default-branch identity: `71685832a9378d2f74ab22294416d67475f368e3`;
- production deployment and exact live verification: run `31487906058`.

The record intentionally does **not** promote earlier narrower review evidence to review of the current product state. No review submission was found for PR #46, so `independent-review` is `INSUFFICIENT`.

The owner explicitly accepted the earlier v1.2 prototype, but that acceptance predates the later analytics product change. It is therefore not promoted to acceptance of the current live state. `human-acceptance` remains `INSUFFICIENT`.

Because an earlier required stage is insufficient, the canonical validator derives the current lifecycle `verified` value as `insufficient` even though deployment and live behaviour have direct evidence.

## Planning boundary

The current planning estimate is 75%, not 100%.

It is a transparent planning heuristic: six of eight explicit closure gates have direct evidence, while current-state independent review and human acceptance remain open. It does not determine lifecycle verification.

## Legacy progress record

`.project/progress.json` remains a historical release-stage record. Its former unqualified `complete: true` field is replaced by `bounded_release_stages_complete: true` plus an explicit completion scope.

That means all ten Issue #36 release stages were completed. It does not mean the whole current Project Reader lifecycle, current-state human acceptance, external comprehension or commercial validation is complete.

## Local validation boundary

`scripts/validate_real_thing_adoption.py` first executes the immutable vendored canonical validator. Only after canonical acceptance does it apply Project Reader-specific checks, including:

- rejecting `100%` planning progress while remaining work is declared;
- rejecting automated workflow evidence as human acceptance;
- preserving the bounded legacy release-completion wording.

Regression tests explicitly prove that the local path cannot accept a record rejected by the canonical claimed-to-verified derivation.

## Current truthful status

- planning estimate: 75%;
- claimed lifecycle state: `live-behaviour-verified`;
- verified lifecycle state: `insufficient`;
- independent review of current product state: `INSUFFICIENT`;
- human acceptance of current live state: `INSUFFICIENT`;
- lifecycle completion: not claimed.

This truthful product status does not prevent the repository from completing adoption of the Project Status control itself.
