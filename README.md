# Project Reader

**GitHub projects explained simply.**

Project Reader helps non-technical people, young people, and neurodivergent readers understand a GitHub project quickly.

It answers the ordinary-reader questions:

1. What is this project?
2. What has been completed?
3. What remains?
4. How complete is the defined work?
5. How likely is the current milestone to finish?
6. Why should the assessment be trusted?
7. How was the project made?
8. How can the project owner be contacted?

## Product rule

The first screen must make sense in under 30 seconds. Technical details stay behind optional controls.

## Proven foundation

The first public Project Reader proof is deployed at:

https://armpitpete.github.io/project-reader/

It reads `armpitpete/project-status-engine` and demonstrates:

- a plain-language purpose;
- evidence-backed status and defined-stage completion;
- **Already complete** instead of a misleading future forecast;
- completed and remaining outcomes;
- one evidence-backed next decision;
- educational technology cards;
- direct links to GitHub evidence.

The deployed proof was produced from Project Reader commit `408629af6a6f2de0d7f2843bd7e4399e4fac8aa8`.

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
- stays separate from the final reader page so evidence can be inspected before assessment.

See `docs/INTERPRETATION_CONTRACT.md` for the exact contract.

## Render a complete project reading

Complete Project Reading v0.5 turns one v0.3 evidence bundle into the ordinary-reader page.

```bash
python scripts/render_evidence_reading.py evidence.json \
  --output project-reading.html
```

The rendered page answers:

- what the project is;
- what has been completed;
- what remains;
- how complete the recognised owner-authority work is;
- how likely the current defined milestone is to finish;
- why the assessment should be trusted;
- how the project was made;
- how to contact the project owner.

The first screen stays simple. Evidence, technology explanations and scoring detail stay behind optional controls.

See `docs/READER_CONTRACT.md` for the final reader contract.

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

Project Reader remains read-only. It does not contain:

- private repository access;
- owner accounts;
- writes to analysed repositories;
- stored contact messages;
- a multi-repository dashboard;
- external comprehension proof from real readers.

## Working status

- **Implemented:** Complete Project Reading v0.5 is implemented.
- **Tested:** Deterministic tests, static proofs, live public evidence checks and unsafe URL checks pass.
- **Merged:** v0.5 implementation merged at `f0858c4d114f2c2dacde35822adfd2f37bd59421`; public proof workflow merged at `3da3d44cf0b0c5a6b69ef59a5009d0fb9f38759e`; deployment permission correction merged at `a9c45794927c607317392dc6dbdf471f22489ece`; Pages OIDC workflow hardening merged at `408629af6a6f2de0d7f2843bd7e4399e4fac8aa8`.
- **Deployed:** Read-only public proof is live at `https://armpitpete.github.io/project-reader/` from deployed commit `408629af6a6f2de0d7f2843bd7e4399e4fac8aa8`.
- **External comprehension:** Not yet proven. Issue #5 is the next real-world testing lane.
