# Project Reader Unseen Generalisation Benchmark v1.3

Issue: #48

## Question

Does the current Project Reader comprehension implementation generalise to unfamiliar public GitHub repositories, or does it mainly perform well on projects already represented by tuned rules and regression fixtures?

## Production freeze

Feature development and production comprehension-rule changes are frozen until the first benchmark run is complete and reviewed.

This benchmark lane may add only research records, benchmark tooling, benchmark tests and documentation. It must not modify the production reader, its public UI, its production comprehension rules or deployment behaviour.

## Frozen-before-evaluation rule

The repository corpus, expected-reading records and scoring rules must be committed before the benchmark runner is allowed to evaluate Project Reader output for those repositories.

The first corpus commit is evidence of the pre-evaluation state. A repository may not be silently replaced after its Project Reader output has been observed. If a repository becomes unavailable or unsuitable, record the reason and treat it as a benchmark exception; any replacement belongs to a separately frozen supplement.

## Known tuned / non-unseen exclusions

The benchmark must not use repositories already named in Project Reader acceptance, regression, development or live-proof work, including:

- `AudioKit/AudioKitSynthOne`
- `microsoft/AI-For-Beginners`
- `cloudflare/cloudflared`
- `armpitpete/project-status-engine`
- `armpitpete/over-my-home`
- `armpitpete/sample-hold-lab`

A benchmark repository is also ineligible if inspection of the Project Reader repository shows it was previously used to create or repair a comprehension rule.

## Corpus

Thirty public repositories are frozen in `manifest.json`. The corpus intentionally spans:

- applications/products
- command-line tools
- network/background services
- libraries/frameworks
- games
- hardware/embedded projects
- documentation/reference collections
- courses/curricula
- research repositories
- datasets
- plugins/extensions
- mixed/reference collections

The category in the manifest is a stratification label, not a score target. The expected-reading record may conclude that the repository's actual form is more nuanced.

## Expected reading

Before Project Reader output is evaluated, each repository receives a human-created expected-reading record based on the repository's public README and repository identity.

Expected records must stay broad. They are not intended to prescribe exact wording. They record:

1. acceptable project type(s)
2. core purpose
3. intended audience when explicitly supported
4. useful actions / starting points
5. implemented capabilities that are central and explicit
6. unfinished work or limitations when explicit
7. claims that would be materially wrong or unsupported

Unknown is valid. Absence of README evidence must not be turned into an expected fact.

## Scoring dimensions

Each dimension is scored independently as `PASS`, `PARTIAL`, `FAIL`, or `NOT_APPLICABLE`:

- `classification`
- `purpose`
- `audience`
- `actions`
- `capabilities`
- `unfinished_or_limits`
- `unsupported_claims`
- `important_omissions`

### Score meanings

- `PASS`: materially correct for an ordinary reader; no important correction required.
- `PARTIAL`: useful but incomplete, overly broad, or containing a non-fatal material error.
- `FAIL`: materially misleading, wrong, fabricated, or misses the central nature of the project.
- `NOT_APPLICABLE`: the public evidence does not support judging that dimension.

`unsupported_claims` is inverted in meaning: PASS means no material unsupported claim was found; FAIL means a material unsupported claim was presented as fact.

## Aggregate interpretation

The benchmark report must publish raw counts as well as any summary percentage.

A repository is a **critical failure** if either:

- classification is FAIL and changes what an ordinary reader would think the thing is; or
- purpose is FAIL; or
- unsupported_claims is FAIL because Project Reader states a material unsupported claim as fact.

Initial conclusion rules:

- `GENERALISES`: at least 24/30 repositories have no critical failure, no project-form stratum is dominated by critical failures, and at least 85% of all applicable dimension scores are PASS or PARTIAL with PASS outnumbering PARTIAL.
- `MIXED`: useful performance but the GENERALISES threshold is not met and fewer than 12/30 repositories have a critical failure.
- `DOES_NOT_YET_GENERALISE`: 12 or more repositories have a critical failure, or a systematic failure makes the aggregate threshold misleading.

These thresholds are frozen before the run. The final report may explain limitations but must not move thresholds after seeing results.

## Anti-overfitting

Do not change production comprehension rules during the first run.

When a benchmark failure suggests a general repair:

1. preserve the original failure;
2. state the general rule being proposed;
3. keep the failed repository in the historical benchmark result;
4. evaluate the repair against a separately frozen held-out or new unseen set.

A repaired benchmark example is regression evidence, not evidence of generalisation.

## Outputs

The lane is complete only when it contains:

- frozen corpus manifest;
- expected-reading records for all 30 repositories;
- machine-checkable expected/result schemas;
- runner using the current production comprehension implementation without modifying it;
- raw Project Reader output for every successfully read repository;
- per-dimension scores and reasons;
- aggregate scorecard by project form and dimension;
- failure catalogue;
- evidence-backed conclusion: `GENERALISES`, `MIXED`, or `DOES_NOT_YET_GENERALISE`;
- explicit limitations and unavailable-repository exceptions.

## Boundaries

No deployment. No private repositories. No production UI change. No production comprehension-rule change. No hosted AI added to Project Reader. No fabricated human-comprehension, satisfaction, trust, demand or commercial evidence.