# Corpus exceptions

## E001 — U03 repository moved before evaluation

Frozen corpus entry:

- `U03` — `AudacityTeam/Audacity`

Eligibility check result:

- GitHub returned repository not found before any Project Reader benchmark evaluation was run.
- The current official repository is `audacity/audacity`.

Disposition:

- preserve `U03` unchanged in the frozen `manifest.json` as historical evidence;
- mark it `UNAVAILABLE_PRE_EVALUATION` in benchmark accounting;
- add replacement `U03R1` — `audacity/audacity` to Supplement 001;
- create the replacement expectation before Project Reader evaluates it;
- count `U03R1` in the 30-repository active benchmark corpus and do not count unavailable `U03` in aggregate performance.

This is not a benchmark-driven substitution: the replacement was made because the frozen repository identity no longer resolves, before Project Reader output for either identity was observed.