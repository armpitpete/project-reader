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
- evidence for every score;
- honest **unknown** states when the repository does not contain enough information.

## Product rule

The first screen must make sense in under 30 seconds. Technical details stay behind optional controls.

## Current state

Foundation v0.1 contains:

- the product contract;
- the completion and likelihood assessment model;
- strict data models;
- a Gitingest ingestion wrapper;
- a plain HTML renderer;
- a sample project reading;
- tests for the scoring rules.

It does **not** yet contain AI project interpretation, GitHub API evidence collection, accounts, writes to repositories, or deployment.

## Run the proof

Requires Python 3.12 or newer.

```bash
python -m venv .venv
. .venv/bin/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python scripts/render_sample.py
python -m http.server 8000 --directory prototype
```

Open `http://localhost:8000/sample.html`.

## Test

```bash
pytest
```

## Dependency

Project Reader uses [Gitingest](https://github.com/coderamp-labs/gitingest) to collect a structured digest of repository files. Gitingest is MIT-licensed. Project Reader adds its own project evidence, assessment, education, and accessible presentation layers.

## Working status

- **Status:** Foundation
- **Completion:** Not yet measured
- **Next:** Prove one public repository can be read into the agreed five-question page using cited evidence.
