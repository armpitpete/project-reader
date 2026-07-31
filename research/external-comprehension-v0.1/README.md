# External Comprehension Field-Test Kit v0.1

This kit prepares issue #5 field evidence collection without starting it.

Use it for five real sessions with anonymous participant IDs `R01` through `R05`. Do not commit completed participant records. The required workflow is to copy a blank record template outside the repository, complete it there, and summarize only the aggregate findings.

Authoritative test surface:

- common comprehension repository: `armpitpete/sample-hold-lab`
- ordinary GitHub page: https://github.com/armpitpete/sample-hold-lab
- Project Reader: https://armpitpete.github.io/project-reader/
- Public API: https://reader-api.merrinworld.uk
- v0.7 merge: `a0acb879d6bd853c9e63c71e0334d84c06e21012`

The kit contains:

- `FACILITATOR_GUIDE.md` - neutral 15-20 minute session guide with matched before-and-after comprehension questions.
- `PARTICIPANT_SHEET.md` - one-page participant instructions.
- `RECORD_SCHEMA.json` - structure for anonymous records.
- `records/R01.json` through `records/R05.json` - blank templates only.
- `SCORING_AND_DECISION_METHOD.md` - pre-session interpretation and decision rules.
- `PAID_OUTCOME_TEST.md` - locked single-offer demand test card.
- `SUMMARY_TEMPLATE.md` - aggregate evidence summary template.

Run the validation check before using the kit:

```bash
python scripts/validate_external_comprehension_kit.py
```

Boundaries:

- Do not fabricate reader comprehension, trust, usability, payment, commitment or refusal evidence.
- Do not contact people from this repository-preparation lane.
- Do not create accounts, payment links, contracts or private repository support.
- Do not alter or redeploy the Project Reader product to run this kit.
- Do not close issue #5 from this lane.
