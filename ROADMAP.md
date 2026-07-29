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

## Automatic Interpretation Contract v0.4 — complete

- [x] Accept one Public Evidence Bundle v0.3
- [x] Identify the strongest explicit project-purpose evidence
- [x] Identify and preserve owner-authority records
- [x] Distinguish facts, interpretations and unknowns
- [x] Detect stale evidence and work-state conflicts
- [x] Require repository-file support for technology claims
- [x] Produce evidence-linked purpose, done, remaining and technology candidates
- [x] Refuse unsupported claims
- [x] Produce structured interpretation JSON
- [x] Accept the live evidence-to-interpretation GitHub Actions proof
- [x] Review and merge the bounded interpretation contract

Merged to `main` at `dd217070be8808ef884edbd6b9b0554dcc559c9f`.

## Complete Project Reading v0.5 — current

- [x] Convert one v0.3 evidence bundle through the v0.4 interpretation layer
- [x] Build the final `ProjectReading` model from owner-authority evidence
- [x] Render a simple first screen for ordinary readers
- [x] Show completion and likelihood without treating activity as progress
- [x] Show done work, remaining work and the next useful step
- [x] Keep trust evidence, technology detail and scoring explanation in optional layers
- [x] Provide a safe GitHub owner contact route
- [x] Add deterministic tests for the evidence-to-reader path
- [x] Add a command-line renderer for complete project readings
- [x] Review and merge the bounded v0.5 candidate
- [x] Select and execute a public release surface

Implemented and merged to `main` at `f0858c4d114f2c2dacde35822adfd2f37bd59421`.

Public proof workflow merged at `3da3d44cf0b0c5a6b69ef59a5009d0fb9f38759e`.

Deployment permission correction merged at `a9c45794927c607317392dc6dbdf471f22489ece`.

Public proof deployed from `a9c45794927c607317392dc6dbdf471f22489ece`:

https://armpitpete.github.io/project-reader/

## External Comprehension and Service Proof v0.6 — next

- [ ] Test the deployed proof with at least five non-technical, young or neurodivergent readers
- [ ] Record before/after understanding evidence
- [ ] Test one concrete paid outcome without building accounts first
- [ ] Record payment or refusal evidence
- [ ] Decide the next deployment, private-access or account-work step from evidence

Tracked by issue #5. External comprehension success is not yet proven.

## Blocked until separately authorised

- Private repository access
- User accounts
- Repository writes
- Contact-form message storage
- Multi-repository dashboard
