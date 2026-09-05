# Project Reader v1.3 — Independent Hostile Scoring

Baseline under test: `1332e0a6baab8b3dd03dff30473ac52edda2b52e`

Canonical raw run: `33251172617`  
Raw artifact digest: `sha256:a378330050924956b173a2f24c0bf0a81ee0d529d33feffd05ec52b7dad62dc9`

## Independence method

- The raw benchmark artifact and the frozen `expected-readings.json` / `BENCHMARK_CONTRACT.md` were read first.
- A complete 30×8 semantic score matrix was produced **without reading the existing `scores.json` or `SCORECARD.md`**.
- That blind matrix was serialized before comparison; SHA-256: `02d1822b1613b4bbf0fddbbc27f8f075c3fd7a3ffcbb97fca6330f970dd76c3d`.
- Only after that matrix was locked were the existing scores read and compared.
- No production comprehension code was changed.

This is independent **scoring**, not an independent reconstruction of the exact upstream source state. The first run retained README SHA-256 values but did not pin upstream repository commits or retain the README bodies. Therefore this review judges recorded Project Reader output against the pre-committed expected readings; it cannot independently prove that every expected reading exactly matched the upstream README state at run time.

## Independent conclusion

**DOES_NOT_YET_GENERALISE**

- Critical failures: **15/30** (frozen failure gate: ≥12)
- Applicable dimension scores: **224**
- PASS: **51**
- PARTIAL: **80**
- FAIL: **93**
- NOT_APPLICABLE: **16**
- PASS + PARTIAL among applicable: **131/224 = 58.5%**

The conclusion is robust to scoring disagreement: the independent critical-failure count remains above the frozen 12-repository failure threshold.

## Per-repository matrix

Legend: `P` PASS, `~` PARTIAL, `F` FAIL, `—` NOT_APPLICABLE.

| ID | Class | Purpose | Audience | Actions | Caps | Limits | Unsupported | Omissions | Critical |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| U01 | F | F | F | ~ | F | — | F | F | YES |
| U02 | F | ~ | F | ~ | P | — | F | ~ | YES |
| U03R1 | ~ | P | ~ | ~ | F | F | P | F | no |
| U04 | P | P | ~ | ~ | ~ | — | P | ~ | no |
| U05 | P | P | ~ | ~ | F | — | P | ~ | no |
| U06 | P | F | ~ | P | F | — | P | F | YES |
| U07 | ~ | ~ | ~ | ~ | F | F | P | F | no |
| U08 | F | ~ | ~ | ~ | F | — | F | ~ | YES |
| U09 | F | ~ | ~ | ~ | P | — | F | ~ | YES |
| U10 | F | F | P | ~ | F | F | F | F | YES |
| U11 | P | P | ~ | ~ | F | F | P | F | no |
| U12 | P | P | ~ | P | F | — | P | ~ | no |
| U13 | ~ | P | ~ | P | ~ | F | P | ~ | no |
| U14 | ~ | ~ | F | P | F | — | P | F | no |
| U15 | ~ | P | ~ | ~ | F | — | P | F | no |
| U16 | P | P | P | P | F | F | P | F | no |
| U17 | P | P | P | ~ | F | — | P | ~ | no |
| U18 | ~ | P | ~ | ~ | F | F | P | ~ | no |
| U19 | ~ | P | ~ | ~ | F | — | ~ | ~ | no |
| U20 | P | ~ | ~ | ~ | F | F | F | F | YES |
| U21 | F | ~ | ~ | ~ | F | F | F | F | YES |
| U22 | F | F | ~ | ~ | F | — | P | F | YES |
| U23 | F | ~ | ~ | P | F | F | F | F | YES |
| U24 | ~ | P | ~ | P | F | ~ | P | ~ | no |
| U25 | ~ | P | ~ | ~ | F | F | P | ~ | no |
| U26 | F | ~ | ~ | ~ | F | F | F | F | YES |
| U27 | ~ | ~ | ~ | ~ | F | F | F | F | YES |
| U28 | F | F | F | P | F | — | F | F | YES |
| U29 | F | F | ~ | F | ~ | — | F | F | YES |
| U30 | F | F | P | ~ | F | — | F | F | YES |

## Critical failures

- **U01** — OBS Studio is presented as documentation; the purpose misses recording/streaming.
- **U02** — KeePassXC is presented as a command-line tool; the visible type claim materially misstates the password-manager application.
- **U06** — fzf's purpose is replaced by merchandise promotion, so the core fuzzy-finder function disappears.
- **U08** — Syncthing is presented as documentation rather than a synchronization program/service.
- **U09** — Caddy is presented as documentation rather than a server platform/web server.
- **U10** — Flask is presented as an end-user software application and its framework purpose is lost.
- **U20** — OSSU is correctly recognized as curriculum, but unsupported 14-week/labs/topic claims are stated as facts.
- **U21** — Coding Interview University is presented as a command-line tool instead of a study plan.
- **U22** — The LLM Course is presented as documentation and social/profile promotion replaces the course purpose.
- **U23** — AlphaFold is presented as documentation rather than research/inference software.
- **U26** — Vega Datasets is presented as documentation rather than a dataset collection/data package.
- **U27** — The visible classification adds a materially unsupported command-line-tool identity to an Obsidian plugin starter/template.
- **U28** — prettier-vscode is presented as a command-line tool and the purpose describes Prettier core instead of the VS Code extension.
- **U29** — Awesome is presented as a library/framework and sponsor material replaces the curated-directory purpose.
- **U30** — Public APIs is presented as web-app/library material and APILayer sponsor copy replaces the community API-directory purpose.

## Comparison with the original scoring

- The blind independent matrix differs from the existing scorecard in **42/240 cells**.
- Excluding the 16 independently N/A cells, this scorer is harsher in **16** cells, more lenient in **10**, and identical in **198**.
- Original critical failures: **14/30**. Independent critical failures: **15/30**.
- The extra independent critical failure is **U27**, because the visible command-line-tool identity is treated as a material unsupported claim rather than merely a partial classification error.
- The original report treated all 240 cells as applicable. This review marks 16 `unfinished_or_limits` cells N/A where the frozen expectation contains no explicit limit. That follows the contract's N/A rule more closely and avoids awarding automatic PASS credit for absence of a testable limit.

## Hostile findings

1. **Capability extraction is worse than the original scorecard suggests:** 25/30 FAIL independently.
2. **Classification vocabulary leaks into false factual identity claims.** A wrong label is repeated into the purpose sentence instead of being contained as uncertainty.
3. **README prominence is unsafe.** Sponsor/social/promotional material can outrank the project's own identity.
4. **Repository scope is not reliably distinguished from adjacent product scope.** `prettier-vscode` is the clearest example.
5. **Course-number extraction is unsafe.** OSSU shows that nearby numbers/topics can become invented structure.
6. **Primary-user audience extraction is weak.** Several outputs default to developers while omitting the actual users.
7. **The benchmark's source-freeze is incomplete.** README hashes prove what was read but do not make the source reconstructable without retained content or upstream commit pins.

## Gate decision

The independent review **confirms the frozen v1.3 failure conclusion**. Feature development should remain frozen except for a bounded v1.4 generalisation-repair lane. The original 30 repositories must become regression cases only; a new independently frozen held-out set is required to claim improved generalisation.
