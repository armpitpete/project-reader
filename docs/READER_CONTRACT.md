# ND/YP Project Reading v0.6

## Purpose

This contract turns one Public Evidence Bundle v0.6 into a complete ordinary-reader Project Reader page.

It uses the v0.4 interpretation layer as evidence preparation, then produces the public reading model and HTML surface.

## Reader questions

The page must allow a non-technical reader to understand:

1. what the project is;
2. what has been completed;
3. what remains;
4. how complete the recognised authority work is;
5. how likely the current plan is to finish;
6. why the assessment should be trusted;
7. how the project was made;
8. how to contact the project owner.

## First-screen rule

The first screen stays simple. The first visible reading flow answers only:

1. `What is this project?`
2. `What has been finished?`
3. `What is still to do?`
4. `Will the current plan be finished?`
5. `What happens next?`

It uses plain British English, short lines, generous spacing and a single column. It says `planned parts` rather than `defined stages`, and says `The current plan is finished` rather than `Already complete`.

Commit hashes, collection timestamps, inline citation numbers, deployment metadata, owner-authority terminology and technology implementation detail stay out of the primary flow.

Evidence stays available through one `How do we know?` disclosure. Repository languages, support tools, formats and Project Reader analysis details stay in one separate `Technical details` disclosure.

## Evidence boundary

Project Reader may assess completion only from recognised owner-authority records collected in the evidence bundle.

It must not silently treat open issues, pull requests, recent activity, README prose or technology files as the finish line.

When recognised authority is missing or contradictory, the reader must show an unknown or low-confidence state instead of inventing a score.

## Assessment boundary

Completion measures readable work items from the selected owner-authority records. When an authority record gives completed and total units, those units remain part of the completion arithmetic instead of being collapsed into a binary item.

Likelihood is a broad evidence-labelled forecast for the current plan. It is not a promise about human behaviour or future events.

When the current planned work is complete, Project Reader says `The current plan is finished` instead of making a future forecast.

When the collected evidence does not prove forecast signals such as recent progress, delivery history, repository health or blocker manageability, Project Reader must show an explicit unknown likelihood rather than converting missing evidence into score points.

## Contact boundary

The default contact route is the GitHub owner profile for the repository. Project Reader does not store messages, create accounts or send contact requests.

Contact URL overrides are validated before rendering and must use a recognised safe URL scheme.

## Technical detail boundary

Repository languages are shown as GitHub Linguist percentages under `Repository languages`. They describe detected repository code volume only. They must not be used to infer importance, difficulty, authorship effort, architecture or why a language was chosen.

Support tools are shown separately from repository languages and only when direct manifest or build evidence supports them.

Formats and outputs are shown separately from programming languages. HTML, JSON and Markdown can be presented as formats when evidence supports that use.

`How Project Reader analysed this` must make clear that Project Reader's own implementation is separate from the technology used by the repository being analysed.

## Still excluded

This lane does not add:

- private repository access;
- writes to analysed repositories;
- owner accounts;
- stored contact messages;
- multi-repository dashboards;
- public deployment.
