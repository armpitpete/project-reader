# Scoring And Decision Method

This method defines interpretation before sessions begin. It is an operational product test for five convenience-sample sessions, not a scientifically validated scale and not population research.

Preserve individual failures even when an aggregate threshold passes. Do not force percentages, confidence scores, or certainty levels. Use the participant's own words when they describe completion or likelihood.

## Matched Before-And-After Comparison

Each R01-R05 session uses the same comprehension repository, `armpitpete/sample-hold-lab`.

Compare the six ordinary-GitHub baseline answers with the six Project Reader answers only after the session notes are complete:

1. what the project is;
2. what appears finished;
3. what appears unfinished or uncertain;
4. how complete it appears;
5. how likely the current plan is to finish;
6. what evidence supports trust or distrust.

Code the comparison as facilitator interpretation, not as participant statements.

`clearer`: after Project Reader, the participant gives a more specific, more evidence-grounded, or less mistaken answer.

`unchanged`: the after answer is materially similar to the baseline answer.

`less_clear`: after Project Reader, the participant becomes more confused, less grounded in evidence, or more mistaken.

`incomparable`: the participant skipped, stopped, could not inspect one side, or the notes are not clean enough to compare.

Also record whether:

- a misunderstanding was corrected;
- Project Reader created new unsupported certainty;
- trust improved, stayed unchanged, or reduced;
- Project Reader enabled an answer that the ordinary GitHub page did not.

Do not infer improvement from politeness, speed, or lack of complaint alone.

## Record-Level Coding

Code each participant only after the matched comparison and session notes are complete.

### Comprehension

Pass when the participant can, without being taught the answer during the task:

- explain what `armpitpete/sample-hold-lab` is in ordinary language;
- identify either completed work, remaining work, uncertainty, or evidence shown by the page;
- avoid a major mistaken belief such as "Project Reader writes to GitHub", "the score is guaranteed", or "unknown means failed".

Use `pass`, `partial`, or `fail`. The code is directional product evidence, not a grade for the participant.

### Usability

Pass when the participant can:

- reach a Project Reader result for `armpitpete/sample-hold-lab`;
- find a first useful answer within three minutes of the result loading;
- continue without blocking help.

Use `pass`, `partial`, or `fail`.

### Trust

Pass when the participant can:

- name at least one reason they trust or distrust the result;
- identify that evidence or uncertainty is available;
- understand that the page has limits and does not prove unsupported claims.

Use `pass`, `partial`, or `fail`. Keep this separate from general trust context and from the paid-outcome result.

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
- Matched-comparison signal: at least 4 of 5 are `clearer` or honestly `unchanged` from an already adequate baseline, with no repeated new unsupported certainty.
- Paid-outcome signal: at least one `paid` or one explicit "yes, I will buy at GBP 25" commitment.
- Severe blocker: any safety, privacy, misleading-claim, or repeated product misunderstanding that would make the current surface irresponsible to promote.

Partial results do not silently become passes. Record them as partial and explain the pattern.

## Recommendation Rules

Use the most conservative rule that fits the evidence.

`keep`: comprehension, usability and trust thresholds pass; matched comparison shows no repeated harm; no severe blocker; paid outcome is not required for keep.

`correct`: at least one threshold misses because of fixable wording, layout, explanation, evidence display, or task-flow problems.

`expand`: all `keep` conditions pass and the paid-outcome signal is present, or participants clearly ask to use the same service for additional public repositories without being prompted.

`pause`: there is a severe blocker, repeated misunderstanding of what the product proves, privacy risk, new unsupported certainty created by the page, or the facilitator cannot collect clean evidence without changing the method.

`retire`: fewer than 2 of 5 pass comprehension, fewer than 2 of 5 pass usability, and qualitative notes show that small corrections are unlikely to fix the service concept.

If rules conflict, choose the more cautious recommendation and explain why.

## Reporting Rules

- Separate observed facts, participant statements, interpretation and decisions.
- Quote participant statements only when they do not identify the person.
- Include failures and confusion even when the final recommendation is `keep` or `expand`.
- Do not claim external success until real records exist.
