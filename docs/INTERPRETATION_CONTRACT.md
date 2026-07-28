# Automatic Interpretation Contract v0.4

## Purpose

This contract turns one factual Public Evidence Bundle v0.3 into reviewable candidate statements. It does not publish a final project reading.

The output helps a reviewer answer:

- what purpose the repository explicitly states;
- which records carry owner authority;
- which work items those records mark done or unfinished;
- which technologies are directly supported by collected repository files;
- where evidence is absent, partial, stale or contradictory.

## Input boundary

The interpreter accepts exactly one JSON evidence bundle with `schema_version: 1`.

The bundle must identify:

- one public GitHub repository;
- one exact 40-character source commit;
- the time its live issue and pull-request queues were checked;
- collected important files with exact-commit provenance;
- recognised progress records;
- open issues and pull requests with inspectable repository URLs.

It performs no network requests and does not collect additional evidence.

## Candidate statement kinds

Every candidate statement is labelled as one of:

| Kind | Meaning |
|---|---|
| `fact` | The collected repository evidence states this directly. |
| `interpretation` | The statement is a bounded reading of explicit evidence. |
| `unknown` | The evidence is insufficient, incomplete or contradictory. |

Candidate statements contain evidence keys. They are not silently promoted into final reader claims.

## Evidence precedence

Owner-authority records use the precedence already recorded by v0.3:

1. `.project/progress.json`;
2. `PROJECT_STATUS.md` or `STATUS.md`;
3. `ROADMAP.md` or `MILESTONES.md`;
4. recognised status, roadmap or milestone documents under `docs/`.

`README.md` is the preferred source for the stated project purpose, but it is not automatically the completion authority.

Open issues, pull requests and recent activity are not treated as completion or as the project finish line.

## Purpose rule

The interpreter examines complete plain-language paragraphs from `README.md` first.

Purpose selection is deterministic:

- paragraphs gain weight for purpose-like action words such as *helps*, *explains*, *collects* or *provides*;
- paragraphs gain weight for project nouns such as *tool*, *application*, *system*, *repository* or *service*;
- support appeals, funding notices, legal notices, warnings and contribution notices are penalised;
- the highest-scoring paragraph is selected;
- an earlier paragraph wins an equal score;
- a minimum purpose score is required.

When no usable README purpose exists, the same rule may return the strongest purpose-like paragraph from a recognised project-status record as an `interpretation`.

A truncated file cannot provide a purpose fact or interpretation. When no complete purpose-like paragraph exists, the output returns an `unknown` purpose instead of inventing one.

## Done and remaining work

Machine progress stages are interpreted only when they contain:

- a readable label or identifier;
- a numeric `completed` value;
- a positive numeric `total` value;
- a completed value between zero and the total.

A stage is a done candidate only when `completed` equals `total`. Otherwise it is an unfinished candidate. The interpreter reports counts, not percentages.

Recognised Markdown authority records may provide work states through explicit checked and unchecked task items.

When every readable authority item is complete, the output may state only that no unfinished item is listed in the recognised authority records. It must not claim that the whole project is complete.

## Conflict rule

The interpreter compares work items with the same normalised label.

- A higher-precedence authority record may supply the candidate statement while the lower-precedence disagreement remains visible.
- If equal-ranked authority records disagree, the state is returned as `unknown`.
- No contradiction is silently discarded.

## Exact provenance rule

A collected file is usable only when all of the following agree with the evidence bundle:

- repository owner and name;
- exact source commit;
- exact repository path.

The accepted URL forms are:

- an exact GitHub `/blob/<commit>/<path>` URL;
- an exact `raw.githubusercontent.com/<owner>/<repository>/<commit>/<path>` URL.

Query strings, fragments, different repositories, different commits and different paths are rejected. The exclusion appears as a `stale_evidence` conflict and remains visible in the evidence index.

Truncated files are explicitly flagged. A truncated authority record is not used to define done or remaining work, and a truncated purpose source is not used for the purpose candidate.

## Queue evidence rule

Each open issue and pull request is represented by an evidence reference containing its exact GitHub URL.

When open queues exist, the interpreter may state that the bundle records those entries only when the candidate cites the corresponding queue evidence keys. The statement remains `unknown` for remaining-work purposes because queue state does not prove the owner-authorised finish line.

Malformed, duplicate or cross-repository queue references make the evidence bundle invalid rather than producing an uninspectable claim.

## Technology rule

Technology candidates require a collected manifest or build file. Public Evidence Bundle v0.3 collects the following root files when present:

- `pyproject.toml` or `requirements*.txt` for Python;
- `package.json` for JavaScript, Node.js or TypeScript;
- `Cargo.toml` for Rust;
- `go.mod` for Go;
- `Gemfile` for Ruby;
- `Dockerfile` for Docker.

A casual technology mention in prose is not enough. When no recognised supporting file is present, technology remains `unknown`.

## Structured output

The JSON output contains:

- repository and exact source-commit context;
- one purpose candidate;
- explicit owner-authority records;
- done candidates;
- remaining candidates;
- technology candidates;
- uncertainties;
- conflicts;
- file and live-queue evidence references;
- explicit refusals.

## Explicit refusals

v0.4 refuses to produce:

- a completion percentage;
- a likelihood assessment;
- a final status judgement.

## Still excluded

This lane does not add:

- deployment;
- private repository access;
- repository writes;
- accounts;
- stored contact messages;
- multi-repository support.
