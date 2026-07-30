# Public Evidence Bundle v0.6

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

1. Read public repository metadata from GitHub, using an optional token only for GitHub API facts.
2. Resolve the default branch to one exact 40-character commit.
3. Collect GitHub Linguist repository language data for the repository.
4. Run Gitingest anonymously against the exact public commit URL.
5. Extract important files from Gitingest's file blocks.
6. Recover only exact named public files that Gitingest omitted.
7. Collect all currently open issues and pull requests.
8. Record `checked_at` after both live queues have returned.
9. Detect recognised progress records.
10. Write one JSON evidence bundle.

## Important-file scope

The bounded important-file set contains:

- project overview and contribution files;
- recognised progress and status records;
- recognised status, roadmap and milestone files under `docs/`;
- root technology manifests and build files needed by the v0.4 interpretation contract.

Recognised root technology files are:

- `pyproject.toml`;
- `package.json`;
- `Cargo.toml`;
- `go.mod`;
- `Gemfile`;
- `Dockerfile`;
- `requirements*.txt`.

These files are collected as factual source text only. v0.3 does not interpret or explain the technology.

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
- `repository_languages`
- `important_files`
- `progress_records`
- `open_issues`
- `open_pull_requests`

Each repository language records:

- language name;
- byte count reported by GitHub Linguist;
- percentage of detected repository code volume;
- the GitHub language API URL used as evidence;
- the source commit Project Reader had resolved before collection.

Each important file records:

- path;
- detected role;
- collection method: `gitingest` or `exact_public_file`;
- exact source URL;
- exact source commit;
- SHA-256 hash of the complete collected text;
- character count;
- up to 30,000 characters of text;
- whether the stored text was truncated.

Machine-readable progress JSON also records only structural facts when available:

- valid JSON;
- schema version;
- stage count;
- whether an `overall.enabled` Boolean exists.

## Time boundary

Repository files are pinned to `source_commit`. Repository language percentages are collected from GitHub's language API and recorded with the resolved source commit. Open issues and pull requests are live queue facts. `checked_at` is generated immediately after both queues have been fetched and cannot be supplied by the caller. The queues can change after the bundle is written.

## Failure boundary

GitHub API, Gitingest, exact-file and network failures are returned as controlled evidence-collection errors. The command-line tool reports the error without an uncontrolled traceback.

## Explicit exclusions

v0.6 does not include:

- interpretation;
- completion scoring;
- likelihood forecasting;
- technology explanations;
- project-specific architecture or language-rationale claims;
- private repository access;
- repository writes;
- deployment;
- multi-repository collection.
