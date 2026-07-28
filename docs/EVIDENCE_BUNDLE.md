# Public Evidence Bundle v0.3

## Purpose

The collector records inspectable facts about one public GitHub repository. It does not explain the project, calculate completion, forecast delivery, or decide what should happen next.

## Input

One public repository address:

```text
owner/name
```

or:

```text
https://github.com/owner/name
```

Other hosts and private repositories are rejected.

## Collection sequence

1. Read public repository metadata from GitHub.
2. Resolve the default branch to one exact 40-character commit.
3. Run Gitingest against the exact commit URL.
4. Extract important files from Gitingest's file blocks.
5. Collect all currently open issues and pull requests.
6. Detect recognised progress records.
7. Write one JSON evidence bundle.

## Progress-record precedence

Detection is deterministic. It does not decide whether a record is truthful.

| Rank | Record |
|---:|---|
| 1 | `.project/progress.json` |
| 2 | `PROJECT_STATUS.md` or `STATUS.md` |
| 3 | `ROADMAP.md` or `MILESTONES.md` |
| 4 | status, roadmap, or milestone documents under `docs/` |

`README.md` is retained as a project overview but is not automatically treated as the completion authority.

## Bundle fields

- `schema_version`
- `checked_at`
- `repository`
- `repository_url`
- `default_branch`
- `source_commit`
- `source_url`
- `gitingest_summary`
- `important_files`
- `progress_records`
- `open_issues`
- `open_pull_requests`

Each important file records:

- path;
- detected role;
- SHA-256 hash of the complete ingested text;
- character count;
- up to 30,000 characters of text;
- whether the stored text was truncated.

Machine-readable progress JSON also records only structural facts when available:

- valid JSON;
- schema version;
- stage count;
- whether an `overall.enabled` Boolean exists.

## Time boundary

Repository files are pinned to `source_commit`. Open issues and pull requests are live queue facts captured at `checked_at`; they can change after the bundle is written.

## Explicit exclusions

v0.3 does not include:

- interpretation;
- completion scoring;
- likelihood forecasting;
- technology explanations;
- private repository access;
- repository writes;
- deployment;
- multi-repository collection.
