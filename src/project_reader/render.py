from __future__ import annotations

from html import escape
from pathlib import Path

from .models import Claim, ProjectReading


def _citations(keys: tuple[str, ...], evidence_numbers: dict[str, int]) -> str:
    if not keys:
        return ""
    links = " ".join(
        f'<a class="citation" href="#evidence-{escape(key)}" aria-label="Evidence {evidence_numbers[key]}">[{evidence_numbers[key]}]</a>'
        for key in keys
    )
    return f' <span class="citations">{links}</span>'


def _claim(claim: Claim, evidence_numbers: dict[str, int]) -> str:
    return f"{escape(claim.text)}{_citations(claim.evidence_keys, evidence_numbers)}"


def _items(values: tuple[Claim, ...], symbol: str, evidence_numbers: dict[str, int]) -> str:
    return "".join(
        f"<li><span aria-hidden='true'>{symbol}</span> {_claim(value, evidence_numbers)}</li>"
        for value in values
    )


def render_html(reading: ProjectReading, destination: Path) -> None:
    evidence_numbers = {item.key: index for index, item in enumerate(reading.evidence, start=1)}
    completion = (
        f"{reading.completion.percentage}% {reading.completion.scope_label}"
        if reading.completion.percentage is not None
        else "Completion not yet measurable"
    )
    likelihood_range = (
        "The defined finish has been reached."
        if reading.likelihood.label == "Already complete"
        else f"Estimated range: {reading.likelihood.range_low}–{reading.likelihood.range_high}%"
    )
    technology_cards = "".join(
        f"""
        <article class="tech-card">
          <h3>{escape(technology.name)}</h3>
          <p><strong>What is it?</strong> {escape(technology.simple_explanation)}</p>
          <p><strong>What does it do here?</strong> {escape(technology.use_here)}</p>
          <p><strong>Why was it used?</strong> {escape(technology.reason_used)}{_citations(technology.evidence_keys, evidence_numbers)}</p>
          <p class="evidence">Reason: {escape(technology.reason_strength.value)}</p>
          <p><strong>Where can I see it?</strong> {escape(technology.location)}</p>
          <p><strong>Why does it matter?</strong> {escape(technology.why_it_matters)}</p>
        </article>
        """
        for technology in reading.technologies
    )
    evidence_items = "".join(
        f"""
        <li id="evidence-{escape(item.key)}">
          <a href="{escape(item.source)}">{escape(item.label)}</a>
          <span class="evidence-strength">{escape(item.strength.value)}</span>
        </li>
        """
        for item in reading.evidence
    )

    evidence_section = (
        f"""<details>
<summary>Evidence</summary>
<ol class=\"evidence-list\">{evidence_items}</ol>
</details>"""
        if reading.evidence
        else ""
    )

    reading_meta_parts: list[str] = []
    if reading.source_commit:
        reading_meta_parts.append(
            f"<strong>Source commit:</strong> <code>{escape(reading.source_commit)}</code>"
        )
    if reading.assessed_at:
        reading_meta_parts.append(f"<strong>Reading checked:</strong> {escape(reading.assessed_at)}")
    if reading.open_work_checked_at:
        reading_meta_parts.append(
            f"<strong>Issues and pull requests checked:</strong> {escape(reading.open_work_checked_at)}"
        )
    reading_meta = (
        f'<p class="reading-meta">{" · ".join(reading_meta_parts)}</p>'
        if reading_meta_parts
        else ""
    )

    remaining_content = (
        f"<ul>{_items(reading.remaining, '○', evidence_numbers)}</ul>"
        if reading.remaining
        else (
            f'<p>{_claim(reading.remaining_empty, evidence_numbers)}</p>'
            if reading.remaining_empty
            else "<p>Nothing currently listed.</p>"
        )
    )

    html = f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(reading.name)} — Project Reader</title>
<style>
:root {{ color-scheme: light; font-family: system-ui, sans-serif; line-height: 1.55; }}
body {{ margin: 0; background: #f7f5ef; color: #1d1d1b; }}
main {{ max-width: 760px; margin: auto; padding: 2rem 1.1rem 4rem; }}
h1 {{ font-size: clamp(2rem, 8vw, 3.5rem); line-height: 1; margin-bottom: .4rem; }}
h2 {{ margin-top: 2.2rem; }}
.lead {{ font-size: 1.18rem; max-width: 62ch; }}
.reading-meta {{ font-size: .9rem; }}
.score-grid {{ display: grid; grid-template-columns: repeat(auto-fit,minmax(220px,1fr)); gap: 1rem; margin: 1.5rem 0; }}
.score, .panel, .tech-card {{ background: white; border: 2px solid #1d1d1b; border-radius: 16px; padding: 1rem; box-shadow: 4px 4px 0 #1d1d1b; }}
.big {{ font-size: 1.75rem; font-weight: 800; margin: .2rem 0; }}
ul {{ padding-left: 0; list-style: none; }}
li {{ margin: .65rem 0; }}
.next {{ font-size: 1.15rem; border-left: 6px solid currentColor; padding-left: 1rem; }}
.actions {{ display: flex; flex-wrap: wrap; gap: .7rem; margin-top: 2rem; }}
a.button, button {{ display: inline-block; background: #fff; color: #1d1d1b; border: 2px solid #1d1d1b; border-radius: 999px; padding: .75rem 1rem; font-weight: 700; text-decoration: none; }}
details {{ margin-top: 2rem; }}
summary {{ cursor: pointer; font-weight: 800; font-size: 1.15rem; }}
.tech-grid {{ display: grid; gap: 1rem; margin-top: 1rem; }}
.evidence, .evidence-strength, .citations {{ font-size: .9rem; }}
.citation {{ font-weight: 800; }}
.evidence-list {{ list-style: decimal; padding-left: 1.5rem; }}
.evidence-strength {{ margin-left: .5rem; }}
:focus-visible {{ outline: 4px solid currentColor; outline-offset: 4px; }}
@media (prefers-reduced-motion: no-preference) {{ a.button:hover {{ transform: translateY(-2px); }} }}
</style>
</head>
<body>
<main>
<p><strong>Project Reader</strong></p>
<h1>{escape(reading.name)}</h1>
<p class="lead">{_claim(reading.explanation, evidence_numbers)}</p>
<p><strong>Status:</strong> {escape(reading.status)}{_citations(reading.status_evidence_keys, evidence_numbers)}</p>
{reading_meta}

<section class="score-grid" aria-label="Project scores">
  <article class="score">
    <h2>How complete?</h2>
    <p class="big">{escape(completion)}</p>
    <p>{escape(reading.completion.explanation)}{_citations(reading.completion.evidence_keys, evidence_numbers)}</p>
    <p class="evidence">Evidence: {escape(reading.completion.evidence_strength.value)}</p>
  </article>
  <article class="score">
    <h2>Likely to finish?</h2>
    <p class="big">{escape(reading.likelihood.label)}</p>
    <p>{escape(likelihood_range)}{_citations(reading.likelihood.evidence_keys, evidence_numbers)}</p>
    <p>{escape(reading.likelihood.timeframe)}</p>
    <p class="evidence">Confidence: {escape(reading.likelihood.confidence)}</p>
  </article>
</section>

<section class="panel">
<h2>Done</h2>
<ul>{_items(reading.done, '✓', evidence_numbers)}</ul>
</section>

<section class="panel">
<h2>Still to do</h2>
{remaining_content}
</section>

<section>
<h2>Next</h2>
<p class="next">{_claim(reading.next_step, evidence_numbers)}</p>
</section>

<div class="actions">
  {f'<a class="button" href="{escape(reading.project_url)}">View the project</a>' if reading.project_url else ''}
  {f'<a class="button" href="{escape(reading.contact_url)}">Contact the project owner</a>' if reading.contact_url else ''}
</div>

<details>
<summary>How was this made?</summary>
<div class="tech-grid">{technology_cards}</div>
</details>

<details>
<summary>Why these scores?</summary>
<p>The completion score uses accepted work against a defined finish line. A completed project is marked as already complete rather than given a speculative future probability.</p>
</details>

{evidence_section}
</main>
</body>
</html>"""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(html, encoding="utf-8")
