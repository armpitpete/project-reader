# Scoring And Decision Method

This method defines success before sessions begin. It is an operational product test for five convenience-sample sessions, not a scientifically validated scale and not population research.

Preserve individual failures even when an aggregate threshold passes.

## Record-Level Coding

Code each participant only after the session notes are complete.

### Comprehension

Pass when the participant can, without being taught the answer during the task:

- explain that Project Reader reads a public GitHub project in ordinary language;
- identify either completed work, remaining work, uncertainty, or evidence shown by the page;
- avoid a major mistaken belief such as "Project Reader writes to GitHub", "the score is guaranteed", or "unknown means failed".

Use `pass`, `partial`, or `fail`.

### Usability

Pass when the participant can:

- reach a Project Reader result for a supported public repository;
- find a first useful answer within three minutes of the result loading;
- continue without blocking help.

Use `pass`, `partial`, or `fail`.

### Trust

Pass when the participant can:

- name at least one reason they trust or distrust the result;
- identify that evidence or uncertainty is available;
- understand that the page has limits and does not prove unsupported claims.

Use `pass`, `partial`, or `fail`.

### Paid Outcome

Use only the locked offer in `PAID_OUTCOME_TEST.md`. Record exactly one of:

- `paid`;
- `explicit_commitment`;
- `refused`;
- `not_offered`.

Do not treat interest, politeness, a request for more information, or "maybe later" as payment or commitment.

## Aggregate Thresholds

After all five records exist, count each dimension separately:

- Comprehension strong signal: at least 4 of 5 pass.
- Usability strong signal: at least 4 of 5 pass.
- Trust strong signal: at least 3 of 5 pass.
- Paid-outcome signal: at least one `paid` or one explicit "yes, I will buy at £25" commitment.
- Severe blocker: any safety, privacy, misleading-claim, or repeated product misunderstanding that would make the current surface irresponsible to promote.

Partial results do not silently become passes. Record them as partial and explain the pattern.

## Recommendation Rules

Use the most conservative rule that fits the evidence.

`keep`: comprehension, usability and trust thresholds pass; no severe blocker; paid outcome is not required for keep.

`correct`: at least one threshold misses because of fixable wording, layout, explanation, evidence display, or task-flow problems.

`expand`: all `keep` conditions pass and the paid-outcome signal is present, or participants clearly ask to use the same service for additional public repositories without being prompted.

`pause`: there is a severe blocker, repeated misunderstanding of what the product proves, privacy risk, or the facilitator cannot collect clean evidence without changing the method.

`retire`: fewer than 2 of 5 pass comprehension, fewer than 2 of 5 pass usability, and qualitative notes show that small corrections are unlikely to fix the service concept.

If rules conflict, choose the more cautious recommendation and explain why.

## Reporting Rules

- Separate observed facts, participant statements, interpretation and decisions.
- Quote participant statements only when they do not identify the person.
- Include failures and confusion even when the final recommendation is `keep` or `expand`.
- Do not claim external success until real records exist.
