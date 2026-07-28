# Roadmap

## Foundation v0.1 — complete

- [x] Lock the KISS first-screen contract
- [x] Separate completion from likelihood of completion
- [x] Define evidence and uncertainty rules
- [x] Define YP and ND educational presentation rules
- [x] Add Gitingest as the repository-ingestion dependency
- [x] Add deterministic scoring models and tests
- [x] Add a static accessible reader proof

## First real proof v0.2 — complete

- [x] Read one named public repository
- [x] Collect README, status, issues, pull requests, releases, milestones, and recent workflow evidence
- [x] Produce a cited plain-language project explanation
- [x] Produce an evidence-labelled completion result
- [x] Produce an evidence-labelled likelihood result
- [x] Identify done, remaining, and one next step
- [x] Explain the detected technologies and why they are used
- [x] Inspect and correct the page with a non-technical reader lens
- [x] Accept the live Gitingest GitHub Actions proof

## Automatic Public Evidence Collection v0.3 — complete

- [x] Accept one public GitHub repository address
- [x] Capture the exact default-branch source commit
- [x] Read important files through Gitingest at that commit
- [x] Collect all currently open issues and pull requests
- [x] Detect recognised progress records using fixed precedence
- [x] Produce a structured JSON evidence bundle
- [x] Reject private repositories and unsupported hosts
- [x] Accept the live collector GitHub Actions proof
- [x] Review and merge the bounded collector

Merged to `main` at `d18f29314dc0acecb403c4deb0313a5bb557afd0`.

## No active development lane

The next product lane requires separate protected authority. The completed collector remains factual, public-only, single-repository and read-only.

## Blocked until separately authorised

- Automatic interpretation
- Automatic completion and likelihood scoring from collected evidence
- Private repository access
- User accounts
- Repository writes
- Contact-form message storage
- Multi-repository dashboard
- Public deployment
