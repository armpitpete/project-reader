# Project Reader

**GitHub projects explained simply.**

Project Reader helps non-technical people, young people, and neurodivergent readers understand a GitHub project quickly.

It answers five questions:

1. What is this project?
2. How complete is it?
3. How likely is it to be finished?
4. What is done?
5. What is left to do?

It also offers:

- one clear next step;
- a simple explanation of the technology used and why;
- a safe **Contact the project owner** link;
- named evidence for important claims and scores;
- honest **unknown** states when the repository does not contain enough information.

## Product rule

The first screen must make sense in under 30 seconds. Technical details stay behind optional controls.

## Proven foundation

The first cited reader for `armpitpete/project-status-engine` is complete. It demonstrates:

- a plain-language purpose;
- evidence-backed status and defined-stage completion;
- **Already complete** instead of a misleading future forecast;
- completed and remaining outcomes;
- one evidence-backed next decision;
- educational technology cards;
- direct links to GitHub evidence.

## Collect a public evidence bundle

Automatic Public Evidence Collection v0.3 records facts for one public repository without interpreting them.

```bash
python scripts/collect_public_evidence.py \
  https://github.com/armpitpete/project-status-engine \
  --output evidence.json
```

The JSON bundle contains:

- the exact source commit;
- important files read through Gitingest;
- recognised progress records;
- currently open issues;
- currently open pull requests;
- the time the live queues were checked.

Gitingest remains the primary repository reader. When it omits an exact public file inside a dot-directory, Project Reader retrieves that named file directly from the same exact commit.

See `docs/EVIDENCE_BUNDLE.md` for the collection contract and authority precedence.

## Interpret an evidence bundle

Automatic Interpretation Contract v0.4 turns one v0.3 bundle into evidence-linked candidate statements for human review.

```bash
python scripts/interpret_evidence.py evidence.json \
  --output interpretation.json
```

The interpretation output:

- labels statements as `fact`, `interpretation` or `unknown`;
- identifies explicit owner-authority records;
- proposes purpose, done, remaining and technology statements only when supported;
- exposes stale or contradictory evidence;
- refuses completion percentages, likelihood forecasts and final status judgements.

See `docs/INTERPRETATION_CONTRACT.md` for the exact contract.

## Run the static proofs

Requires Python 3.12 or newer. Package installation is not needed to render the checked-in examples.

```bash
python scripts/render_sample.py
python scripts/render_project_status_engine.py
python -m http.server 8000 --directory prototype
```

Open:

- `http://localhost:8000/sample.html`
- `http://localhost:8000/project-status-engine.html`

## Develop and test

```bash
python -m venv .venv
. .venv/bin/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
```

GitHub Actions separately validates the deterministic test suite and a live public evidence-to-interpretation proof against the public proof repository.

## Dependency

Project Reader uses [Gitingest](https://github.com/coderamp-labs/gitingest) to collect a structured digest of repository files. Gitingest is MIT-licensed. Project Reader adds its own evidence contract, interpretation, assessment, education and accessible presentation layers.

## Current boundaries

Project Reader remains read-only. It does not yet contain:

- automatic completion or likelihood scoring from collected evidence;
- a final automatic project-status judgement;
- private repository access;
- owner accounts;
- writes to analysed repositories;
- stored contact messages;
- a multi-repository dashboard;
- public deployment.

## Working status

- **Status:** Automatic Interpretation Contract v0.4 in draft review
- **Completion:** Deterministic tests, static proofs and the live public evidence-to-interpretation validation pass
- **Next:** Review the bounded v0.4 draft before any scoring or final-status lane is authorised
