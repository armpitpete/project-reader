# Project Reader

**Public GitHub projects explained in ordinary language.**

Public reader:

https://armpitpete.github.io/project-reader/

## Status

Project Reader is under active v1.2 acceptance repair and is **not complete**.

Issue #36 records two owner-supplied failures found after the v1.1 closure:

- `cloudflare/cloudflared` was wrongly classified as a website instead of a command-line tunnel client and daemon;
- the reader stopped completely when GitHub's anonymous public API allowance was exhausted.

Authoritative repair base: `f110d11249f47dd63136a2ef34565b898faed595`.

The live v1.1 site remains available while the correction is validated. It must not be treated as the final accepted product.

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

The public reader runs entirely in the visitor's browser. It applies bounded deterministic rules to public README evidence and available repository metadata.

It distinguishes common project forms including:

- applications and products;
- learning courses and curricula;
- libraries and frameworks;
- command-line tools;
- command-line network clients and background services;
- websites and web applications;
- documentation collections;
- templates and starter projects;
- research and dataset repositories;
- mixed or unclear projects.

It extracts evidence-backed purpose, audience, useful actions, visible capabilities, explicit limitations and planned work. Short supporting README passages remain available for inspection.

A bounded correction and polish layer removes irrelevant social, localisation, deprecated-version and incidental dependency links from primary actions, improves raw README wording and prioritises the most useful starting action.

No hosted artificial-intelligence service is used.

## v1.2 acceptance targets

### Cloudflare cloudflared

The reader must explain that `cloudflared` is:

- the command-line client and background service for Cloudflare Tunnel;
- used to create outbound connections between a local service or origin and Cloudflare's network;
- for people who run or develop networked services;
- an implemented tunnel client and daemon, not a website;
- accessible through useful installation, documentation, usage, container and source actions.

Deprecated versions, Cap'n Proto requirements and other incidental links must not occupy the primary action list.

### Anonymous API exhaustion

A first-time visitor must still receive a useful reduced reading when `api.github.com` is unavailable or rate-limited.

The fallback:

- fetches the public README from `raw.githubusercontent.com`;
- requires no account or GitHub token;
- labels unavailable licence, branch, language and owner-progress metadata;
- preserves HTTPS-only links and read-only operation;
- does not replace the whole answer with “open GitHub”.

## Retained acceptance evidence

The v1.1 Synth One and AI For Beginners contracts remain active regression gates:

- Synth One must be understood as a playable iPhone/iPad synthesizer and open-source codebase for musicians and developers.
- AI For Beginners must be understood as a beginner curriculum with lessons, quizzes, labs, translations and clear course starting actions.

For repositories without recognised owner-defined completion authority, overall completion remains unknown.

## Browser-only public reading

When available, Project Reader may read:

- public repository metadata;
- the README;
- `.project/progress.json` when present and valid;
- GitHub's repository-language totals.

When the metadata API is unavailable, the reader uses only the public README and submitted repository identity. Missing metadata is stated rather than guessed.

The browser receives no GitHub token and has no repository write path. It does not send the repository address to a Project Reader server.

## Evidence rules

Project Reader:

- lets richer README evidence outrank a short repository slogan;
- does not infer purpose or completion from stars, age, activity or language volume;
- does not classify a project as a website merely because it handles HTTP, origins, proxies or web servers;
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

Only public repositories are supported. Unusual or badly structured READMEs can still be misunderstood, so the evidence view remains part of the product.

## Develop and test

Requires Python 3.12 or newer and Node.js 22 or newer.

```bash
python -m venv .venv
. .venv/bin/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
node tests/browser_comprehension_contract.mjs
node tests/network_and_fallback_contract.mjs
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
