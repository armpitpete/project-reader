# Project Reader v1.3 Unseen Generalisation Scorecard

Baseline Project Reader: `1332e0a6baab8b3dd03dff30473ac52edda2b52e`

Raw evidence:

- workflow run: `33251172617`
- artifact: `project-reader-v1.3-unseen-raw-results`
- artifact id: `9714406709`
- artifact digest: `sha256:a378330050924956b173a2f24c0bf0a81ee0d529d33feffd05ec52b7dad62dc9`
- raw result generated: `2026-08-29T11:53:48Z`
- repositories read successfully: `30/30`
- production interpretation modules during run: exact frozen v1.2 blobs required by `BENCHMARK_CONTRACT.md`

The expected readings and conclusion thresholds were committed before this raw run.

## Result

**DOES_NOT_YET_GENERALISE**

The frozen contract says this conclusion applies when 12 or more of 30 repositories have a critical failure, or when a systematic failure makes the aggregate threshold misleading.

Observed critical failures: **14/30**.

Across the eight dimensions there were 240 applicable scores:

- PASS: **69**
- PARTIAL: **81**
- FAIL: **90**
- PASS + PARTIAL: **150/240 = 62.5%**

This is well below the frozen `GENERALISES` threshold of at least 24/30 repositories without a critical failure and at least 85% PASS-or-PARTIAL dimension scores with PASS outnumbering PARTIAL.

## Dimension totals

| Dimension | PASS | PARTIAL | FAIL |
|---|---:|---:|---:|
| Classification | 8 | 10 | 12 |
| Purpose | 14 | 7 | 9 |
| Audience | 7 | 23 | 0 |
| Actions | 7 | 22 | 1 |
| Capabilities | 2 | 5 | 23 |
| Unfinished / limits | 17 | 3 | 10 |
| Unsupported claims | 14 | 2 | 14 |
| Important omissions | 0 | 9 | 21 |

The largest systematic failure is **capability extraction: 23/30 FAIL**. The second major problem is that classification errors frequently become unsupported factual claims rather than staying uncertain.

## Per-repository matrix

Legend: `P` = PASS, `~` = PARTIAL, `F` = FAIL.

| ID | Repository | Class | Purpose | Audience | Actions | Caps | Limits | Unsupported | Omissions | Critical |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| U01 | obsproject/obs-studio | F | F | ~ | ~ | F | P | F | F | YES |
| U02 | keepassxreboot/keepassxc | F | ~ | ~ | ~ | P | P | F | ~ | YES |
| U03R1 | audacity/audacity | ~ | P | ~ | ~ | F | F | P | F | no |
| U04 | BurntSushi/ripgrep | P | P | ~ | ~ | ~ | P | P | ~ | no |
| U05 | sharkdp/bat | P | P | ~ | F | F | P | P | F | no |
| U06 | junegunn/fzf | P | F | ~ | ~ | F | P | F | F | YES |
| U07 | tailscale/tailscale | ~ | ~ | ~ | ~ | F | F | P | F | no |
| U08 | syncthing/syncthing | F | ~ | ~ | ~ | F | P | F | F | YES |
| U09 | caddyserver/caddy | F | ~ | ~ | ~ | P | P | F | ~ | YES |
| U10 | pallets/flask | F | F | P | ~ | F | P | F | F | YES |
| U11 | expressjs/express | P | P | ~ | ~ | F | F | P | F | no |
| U12 | tokio-rs/tokio | P | P | P | P | ~ | P | P | ~ | no |
| U13 | OpenTTD/OpenTTD | ~ | P | ~ | P | ~ | ~ | P | ~ | no |
| U14 | wesnoth/wesnoth | ~ | ~ | ~ | P | F | P | P | F | no |
| U15 | arduino/ArduinoCore-avr | ~ | P | ~ | ~ | F | P | P | F | no |
| U16 | raspberrypi/pico-sdk | P | P | P | P | ~ | F | P | ~ | no |
| U17 | mdn/content | P | P | P | ~ | F | P | P | ~ | no |
| U18 | rust-lang/book | ~ | P | ~ | ~ | F | F | P | F | no |
| U19 | kubernetes/website | ~ | P | ~ | ~ | F | P | ~ | ~ | no |
| U20 | ossu/computer-science | P | F | ~ | ~ | F | F | F | F | YES |
| U21 | jwasham/coding-interview-university | F | F | P | ~ | F | F | F | F | YES |
| U22 | mlabonne/llm-course | F | F | ~ | ~ | F | P | F | F | YES |
| U23 | google-deepmind/alphafold | F | ~ | ~ | P | F | F | F | F | YES |
| U24 | tensorflow/models | ~ | P | P | P | F | ~ | P | ~ | no |
| U25 | fivethirtyeight/data | ~ | P | ~ | ~ | F | F | P | F | no |
| U26 | vega/vega-datasets | F | ~ | ~ | ~ | F | F | F | F | YES |
| U27 | obsidianmd/obsidian-sample-plugin | ~ | P | ~ | ~ | F | ~ | ~ | F | no |
| U28 | prettier/prettier-vscode | F | F | ~ | P | F | P | F | F | YES |
| U29 | sindresorhus/awesome | F | F | ~ | ~ | ~ | P | F | F | YES |
| U30 | public-apis/public-apis | F | F | P | ~ | F | P | F | F | YES |

## Critical failures

The 14 critical failures are:

- **U01 OBS Studio** — classified as documentation; purpose does not state recording/streaming.
- **U02 KeePassXC** — a CLI component is promoted to the identity of the whole password-manager application.
- **U06 fzf** — merchandise promotion is selected as the project purpose.
- **U08 Syncthing** — classified as documentation rather than a synchronization program/service.
- **U09 Caddy** — classified as documentation rather than a server platform/web server.
- **U10 Flask** — classified as an end-user application instead of a Python web framework.
- **U20 OSSU Computer Science** — correctly recognizes curriculum form but invents a 14-week path, practical labs and other unsupported course facts.
- **U21 Coding Interview University** — classified as a command-line tool instead of a study plan.
- **U22 LLM Course** — classified as documentation and uses social/profile promotion as purpose instead of the course.
- **U23 AlphaFold** — classified as documentation rather than research/inference software.
- **U26 Vega Datasets** — classified as documentation rather than a dataset collection.
- **U28 prettier-vscode** — classified as a command-line tool and describes Prettier core instead of the VS Code extension.
- **U29 Awesome** — classified as a library/framework and uses sponsor text as purpose instead of the curated directory.
- **U30 Public APIs** — classified as web-app/library material and uses an APILayer sponsor description instead of the community API directory.

## Stratum result

| Stratum | Repositories | Critical failures |
|---|---:|---:|
| Application/product | 3 | 2 |
| Command-line tool | 3 | 1 |
| Network/background service | 3 | 2 |
| Library/framework | 3 | 1 |
| Game | 2 | 0 |
| Hardware/embedded | 2 | 0 |
| Documentation/reference | 3 | 0 |
| Course/curriculum | 3 | 3 |
| Research | 2 | 1 |
| Dataset | 2 | 1 |
| Plugin/extension | 2 | 1 |
| Mixed/reference collection | 2 | 2 |

The result is not simply “some obscure types are hard.” There are failures in ordinary applications, frameworks, services, courses and extensions.

## Scoring notes

A critical failure was recorded only where the frozen contract allowed it:

- classification FAIL that changes what an ordinary reader would think the thing is;
- purpose FAIL; or
- a material unsupported claim stated as fact.

Unknown/mixed classifications were often scored PARTIAL rather than FAIL when the following purpose sentence still told the reader what the project really was. This makes the critical-failure count conservative rather than maximally punitive.

The raw output remains the authority for what Project Reader actually produced. This scorecard is the semantic evaluation against the pre-committed expected readings.