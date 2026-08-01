# Project Reader

**Public GitHub projects explained simply.**

Project Reader helps non-technical people, young people and neurodivergent readers understand what a public GitHub project says about itself.

Public reader:

https://armpitpete.github.io/project-reader/

## What the reader answers

The simple reading starts with:

1. What is this project?
2. What can someone do with it?
3. What appears to work or be finished?
4. What is unfinished or unclear?
5. What was it made with?
6. Where can I see it?

Completion, likelihood, evidence links and technical details remain available behind closed optional sections.

## Browser-only public reading

Project Reader v1.0 runs entirely in the visitor's browser. It requests public repository information directly from GitHub's REST API.

It may read:

- public repository metadata;
- the README;
- `.project/progress.json` when present and valid;
- GitHub's repository-language totals.

It never receives a GitHub token and has no repository write path. It does not send the repository address to a Project Reader server.

## Evidence rules

Project Reader:

- calculates defined-stage completion only from valid numeric stages in `.project/progress.json`;
- respects an owner record that disables an overall percentage;
- reports unknown when completion or likelihood is unsupported;
- does not treat activity, open issues, repository age or code volume as completion evidence;
- does not claim that browser reading proves external comprehension or commercial demand.

## Input and limits

Accepted input:

- `owner/name`;
- a root `https://github.com/owner/name` address.

Only public repositories are supported. GitHub applies an unauthenticated public API rate limit.

## Python evidence toolkit

The repository retains the earlier Python evidence, interpretation and rendering packages as a tested reference implementation and command-line toolkit.

Examples:

```bash
python scripts/collect_public_evidence.py \
  https://github.com/armpitpete/project-status-engine \
  --output evidence.json

python scripts/interpret_evidence.py evidence.json \
  --output interpretation.json

python scripts/render_evidence_reading.py evidence.json \
  --output project-reading.html
```

## Develop and test

Requires Python 3.12 or newer.

```bash
python -m venv .venv
. .venv/bin/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
```

Static proofs:

```bash
python scripts/render_sample.py
python scripts/render_project_status_engine.py
python -m http.server 8000 --directory prototype
```

## Boundaries

Project Reader remains read-only. It does not provide:

- private repository access;
- user accounts;
- writes to analysed repositories;
- stored contact messages;
- a multi-repository dashboard;
- external comprehension or commercial validation.

## Working status

- **Implementation:** v1.0 browser-only completion candidate is implemented on issue #25.
- **Testing:** awaiting exact-head GitHub Actions validation.
- **Merge:** awaiting protected review and guarded merge.
- **Deployment:** awaiting GitHub Pages deployment from the accepted merge commit.
- **Product classification:** finished public prototype after those mechanical release gates pass; not an externally validated commercial service.
