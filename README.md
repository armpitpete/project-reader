# Project Reader

**Public GitHub projects explained in ordinary language.**

Public reader:

https://armpitpete.github.io/project-reader/

## Status

Project Reader v1.1 is complete as a finished public prototype.

- Accepted implementation head: `6d79145e981ef6d553a4f682db70b73381231cc8`
- Implementation and deployment commit: `4a140dad75f1b14819f41162380ce5ace10025cc`
- Public deployment evidence: issue #33 comment `5153152571`
- Runtime: browser-only and read-only
- Hosted artificial-intelligence service: none

The v1.1 repair followed owner-supplied screenshots showing that the earlier release mostly repeated repository descriptions and language totals. The corrected reader now interprets bounded README evidence and produces materially different explanations for different kinds of project.

## What the reader answers

The plain reading starts with:

1. What is this?
2. Who is it for?
3. What can I do with it?
4. What already exists?
5. What is unfinished or uncertain?
6. Where should I start?

Completion and likelihood remain separate optional questions. They stay unknown unless a recognised owner progress record supports them.

## Deterministic README comprehension

The public reader runs entirely in the visitor's browser. It requests public repository information directly from GitHub and applies bounded deterministic rules to the README and repository metadata.

It can distinguish common project forms including:

- applications and products;
- learning courses and curricula;
- libraries and frameworks;
- command-line tools;
- websites and web applications;
- documentation collections;
- templates and starter projects;
- research and dataset repositories;
- mixed or unclear projects.

It extracts evidence-backed purpose, audience, useful actions, visible capabilities, explicit limitations and planned work. Short supporting README passages remain available for inspection.

A final bounded polish layer removes irrelevant social, localisation and software-development-kit links from primary actions, improves raw README wording and prioritises the most useful starting action.

No hosted artificial-intelligence service is used.

## Acceptance evidence

The release was tested against the two repositories that exposed the earlier failure.

### AudioKit Synth One

The reader now explains that Synth One is:

- a playable open-source synthesizer app for iPhone and iPad;
- for musicians using the app and developers studying or contributing to the code;
- built from synthesizer parts such as oscillators, filters, reverbs and effects;
- accompanied by completed work, planned updates and contribution ideas;
- available through useful app, feature, source-code and contribution actions.

### AI For Beginners

The reader now explains that AI For Beginners is:

- a beginner curriculum for learning artificial intelligence;
- organised as 24 lessons over roughly 12 weeks;
- supported by quizzes, practical labs, notebooks and translations;
- a course rather than a software application;
- accessible through course setup, lesson-list, resource and source-repository actions.

For both repositories, overall completion remains unknown because no recognised owner-defined completion measure is available.

## Browser-only public reading

Project Reader may read:

- public repository metadata;
- the README;
- `.project/progress.json` when present and valid;
- GitHub's repository-language totals.

It receives no GitHub token in the public browser and has no repository write path. It does not send the repository address to a Project Reader server.

## Evidence rules

Project Reader:

- lets richer README evidence outrank a short repository slogan;
- does not infer purpose or completion from stars, age, activity or language volume;
- calculates defined-stage completion only from valid numeric stages in `.project/progress.json`;
- respects an owner record that disables an overall percentage;
- reports unknown when completion or likelihood is unsupported;
- keeps implementation languages secondary to project purpose and user actions;
- omits language rows below 0.1% after rounding;
- does not invent a generic purpose for an unknown language;
- does not claim external comprehension or commercial demand.

## Input and limits

Accepted input:

- `owner/name`;
- a root `https://github.com/owner/name` address.

Only public repositories are supported. GitHub applies an unauthenticated public API rate limit. Unusual or badly structured READMEs can still be misunderstood, so the evidence view remains part of the product.

## Develop and test

Requires Python 3.12 or newer and Node.js 22 or newer.

```bash
python -m venv .venv
. .venv/bin/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
node tests/browser_comprehension_contract.mjs
```

Live acceptance:

```bash
GITHUB_TOKEN=... node tests/live_browser_acceptance.mjs
```

Build the public artifact:

```bash
python scripts/build_pages_site.py \
  --commit 0123456789abcdef0123456789abcdef01234567 \
  --output public
```

## Python evidence toolkit

The repository retains the earlier Python evidence, interpretation and rendering packages as a tested reference implementation and command-line toolkit. They are not the public browser runtime.

## Boundaries

Project Reader remains read-only. It does not provide:

- private repository access;
- user accounts;
- writes to analysed repositories;
- stored contact messages;
- a multi-repository dashboard;
- hosted artificial-intelligence interpretation;
- external comprehension or commercial-validation claims.
