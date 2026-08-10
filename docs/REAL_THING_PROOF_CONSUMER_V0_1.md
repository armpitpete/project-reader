# Real-Thing Proof consumer v0.1

Project Reader is a deployed downstream consumer of the canonical Real-Thing Proof / Project Status v2 controls.

## Exact authorities

- Threadkeeper: `armpitpete/threadkeeper@a5bc55336c86097301b378d8654ac92a26ef81e5`
- Project Status v2: `armpitpete/merrin-project-controls@7bc8b7f5ef921851ad163093f089d28d8128bf6c`
- Local canonical lifecycle record: `project-status.json`

Project Reader does not redefine the shared lifecycle schema or validator.

## Current direct evidence boundary

The current record is grounded in the exact SD-016 path:

- accepted design authority: Issue #41;
- implementation candidate: PR #43 head `887381979687ba76db9e8b27edcd30883b4a2d6a`;
- exact-head automated checks: runs `30934400339` and `30934402526`;
- protected exact-head review: review `4857302288`;
- merged/default-branch identity: `4e64c5486863a41fc011078c502bb8fd3b827460`;
- production deployment and verification: run `30935272781` and Issue #41 production evidence.

Those records support direct PASS through `live-behaviour` for the explicit claims they exercised.

They do **not** establish human acceptance. In particular, the workflow job named `live-browser-acceptance` is automated browser evidence, not a person accepting the experience.

## Legacy progress record

`.project/progress.json` remains a historical release-stage record. Its former unqualified `complete: true` field is replaced by `bounded_release_stages_complete: true` plus an explicit completion scope.

That means all ten issue #36 release stages were completed. It does not mean the whole Project Reader lifecycle, human acceptance, external comprehension or commercial validation was complete.

## Local validation boundary

`scripts/validate_real_thing_adoption.py` verifies only Project Reader's exact adoption record and the known ambiguity regressions. It is not a general Project Status implementation. Later lifecycle semantics remain canonical in `merrin-project-controls`.

## Current truthful status

- planning/release stage estimate: 100%;
- verified lifecycle state: `live-behaviour-verified`;
- human acceptance: `INSUFFICIENT`;
- lifecycle completion: not claimed.
