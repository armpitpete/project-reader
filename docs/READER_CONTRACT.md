# Complete Project Reading v0.5

## Purpose

This contract turns one Public Evidence Bundle v0.3 into a complete ordinary-reader Project Reader page.

It uses the v0.4 interpretation layer as evidence preparation, then produces the public reading model and HTML surface.

## Reader questions

The page must allow a non-technical reader to understand:

1. what the project is;
2. what has been completed;
3. what remains;
4. how complete the recognised owner-authority work is;
5. how likely the current defined milestone is to finish;
6. why the assessment should be trusted;
7. how the project was made;
8. how to contact the project owner.

## First-screen rule

The first screen stays simple:

- project name;
- plain-language explanation;
- current status;
- completion;
- likelihood;
- completed work;
- remaining work;
- next step;
- project and contact links.

Technical evidence, technology explanations and scoring detail stay behind optional controls.

## Evidence boundary

Project Reader may assess completion only from recognised owner-authority records collected in the evidence bundle.

It must not silently treat open issues, pull requests, recent activity, README prose or technology files as the finish line.

When recognised authority is missing or contradictory, the reader must show an unknown or low-confidence state instead of inventing a score.

## Assessment boundary

Completion measures readable work items from the selected owner-authority records. When an authority record gives completed and total units, those units remain part of the completion arithmetic instead of being collapsed into a binary item.

Likelihood is a broad evidence-labelled forecast for the current defined milestone. It is not a promise about human behaviour or future events.

When the current defined work is complete, Project Reader says `Already complete` instead of making a future forecast.

When the collected evidence does not prove forecast signals such as recent progress, delivery history, repository health or blocker manageability, Project Reader must show an explicit unknown likelihood rather than converting missing evidence into score points.

## Contact boundary

The default contact route is the GitHub owner profile for the repository. Project Reader does not store messages, create accounts or send contact requests.

Contact URL overrides are validated before rendering and must use a recognised safe URL scheme.

## Still excluded

This lane does not add:

- private repository access;
- writes to analysed repositories;
- owner accounts;
- stored contact messages;
- multi-repository dashboards;
- public deployment.
