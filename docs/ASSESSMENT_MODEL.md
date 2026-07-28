# Completion Assessment Model v0.1

## Two separate measures

### Percentage complete

Measures how much of a defined body of work is accepted as done.

A percentage is shown only when a finish line and bounded work list exist.

```text
completion = accepted completed weight / total defined weight
```

Incomplete, in-progress, blocked, and unknown work is not counted as done.

### Likely chance of completion

Estimates whether the current milestone or project is likely to reach its stated finish within a named period.

It uses seven evidence signals:

| Signal | Maximum |
|---|---:|
| Clear finish line | 20 |
| Recent meaningful progress | 20 |
| Remaining work is bounded | 15 |
| Clear next step | 15 |
| Blockers are manageable | 15 |
| Previous milestones were delivered | 10 |
| Repository health | 5 |

Total: 100.

The internal score is translated into a broad label and range:

| Score | Label |
|---:|---|
| 85–100 | Very likely |
| 70–84 | Likely |
| 50–69 | Uncertain |
| 30–49 | Unlikely |
| 0–29 | Very unlikely |

The public page must include:

- the label;
- a rounded range, never spurious decimal precision;
- the timeframe;
- assessment confidence;
- the strongest positive evidence;
- the strongest risk.

## Confidence

- **High:** most signals have direct, current evidence.
- **Medium:** useful evidence exists, but some signals depend on inference.
- **Low:** the repository is incomplete, contradictory, or stale.

## Required caveat

This is an evidence-based project forecast, not a promise about human behaviour or future events.
