# Public Repository Reading v0.7

Issue #14 adds a public read path for visitors who want Project Reader to analyse a supported public GitHub repository.

## Architecture

- GitHub Pages serves the browser frontend from `https://armpitpete.github.io/project-reader/`.
- The frontend sends one JSON request to `https://reader-api.merrinworld.uk/api/v1/read`.
- The Oracle VPS runs `project-reader-api.service` as the unprivileged `project-reader` account.
- Apache/Virtualmin terminates HTTPS for `reader-api.merrinworld.uk` and proxies to `127.0.0.1:8091`.
- The Python API calls the existing Project Reader authority pipeline:
  - `project_reader.evidence.collect_public_evidence`
  - `project_reader.interpretation.interpret_evidence_bundle`
  - `project_reader.reading.build_project_reading`
  - `project_reader.render.render_html_string`

The browser receives rendered Project Reader HTML from that Python pipeline. It does not receive GitHub tokens, server paths or server credentials.

## Public API

### `GET /health`

Returns a minimal process health JSON response.

### `GET /ready`

Returns a minimal readiness JSON response.

### `GET /api/v1/status`

Returns the configured routes, CORS origins, read-only boundary, public limits and authority pipeline.

### `POST /api/v1/read`

Request:

```json
{
  "repository": "owner/name"
}
```

`https://github.com/owner/name` is also accepted. Other hosts, schemes, repository subpaths, private repositories, malformed values and ambiguous values are refused.

Successful response:

```json
{
  "ok": true,
  "repository": "owner/name",
  "repository_url": "https://github.com/owner/name",
  "source_commit": "40-character Git SHA",
  "checked_at": "UTC timestamp",
  "status": "Unknown",
  "completion": {
    "label": "Unknown",
    "percentage": null,
    "evidence_strength": "unknown",
    "explanation": "Completion cannot be measured."
  },
  "likelihood": {
    "label": "Unknown",
    "confidence": "Low",
    "timeframe": "Insufficient evidence."
  },
  "evidence_summary": {
    "important_file_count": 1,
    "progress_record_count": 0,
    "repository_language_count": 1,
    "open_issue_count": 0,
    "open_pull_request_count": 0
  },
  "result_html": "<!doctype html>..."
}
```

The completion, likelihood, status and HTML are produced from the existing evidence and interpretation authority. Missing or conflicting owner-authority evidence remains unknown.

## Safety Handling

- Read-only API; no GitHub writes.
- Public repositories only.
- HTTPS GitHub repository addresses only.
- CORS is limited to `https://armpitpete.github.io` by default.
- JSON request bodies are capped by `PROJECT_READER_MAX_REQUEST_BYTES`.
- Repository size is capped by `PROJECT_READER_MAX_REPOSITORY_SIZE_KB` before Gitingest reads the repository.
- Reads are bounded by `PROJECT_READER_READ_TIMEOUT_SECONDS`.
- A process-local sliding-window rate limit is configured with `PROJECT_READER_RATE_LIMIT_REQUESTS` and `PROJECT_READER_RATE_LIMIT_WINDOW_SECONDS`.
- Error responses use safe public messages and do not echo raw upstream URLs or token values.
- The frontend uses a sandboxed result iframe and no browser-side credentials.

## Oracle Deployment

Prepare the VPS once:

```bash
sudo mkdir -p /opt/project-reader
sudo git clone https://github.com/armpitpete/project-reader.git /opt/project-reader
sudo cp /opt/project-reader/config/env.example /opt/project-reader/config/env
sudo chmod 600 /opt/project-reader/config/env
```

Set `/opt/project-reader/config/env` values for production:

```bash
PROJECT_READER_BIND_HOST=127.0.0.1
PROJECT_READER_BIND_PORT=8091
PROJECT_READER_API_BASE_URL=https://reader-api.merrinworld.uk
PROJECT_READER_ALLOWED_ORIGINS=https://armpitpete.github.io
PROJECT_READER_DEPLOYED_COMMIT=<merged-main-commit>
PROJECT_READER_MAX_REQUEST_BYTES=4096
PROJECT_READER_MAX_REPOSITORY_SIZE_KB=50000
PROJECT_READER_READ_TIMEOUT_SECONDS=120
PROJECT_READER_RATE_LIMIT_REQUESTS=20
PROJECT_READER_RATE_LIMIT_WINDOW_SECONDS=60
PROJECT_READER_GITHUB_TOKEN=
```

Deploy an exact commit:

```bash
sudo /opt/project-reader/scripts/deploy_server.sh \
  --expected-commit <merged-main-commit> \
  --install-apache
```

The script follows the current Merrin server pattern: exact expected commit, clean checkout, environment-file hash preservation, systemd installation, service restart, local health checks, local read proof, optional Apache install, public HTTPS checks and CORS preflight verification.

## Required DNS

`reader-api.merrinworld.uk` must resolve to Merrin's Oracle VPS before the public HTTPS verification can pass.

## Live Proof Set

`scripts/live_repository_proofs.py` reads three public repositories through the same Python authority pipeline:

- `armpitpete/project-status-engine`: mixed-language repository with recognised owner-authority completion records.
- `armpitpete/over-my-home`: public repository with missing owner-authority completion records, so completion stays unknown.
- `armpitpete/sample-hold-lab`: separate public repository proving the reader is not tied to the prepared example.
