from __future__ import annotations

from html import escape
from pathlib import Path

from .models import ProjectReading


def _items(values: tuple[str, ...], symbol: str) -> str:
    return "".join(f"<li><span aria-hidden='true'>{symbol}</span> {escape(value)}</li>" for value in values)


def render_html(reading: ProjectReading, destination: Path) -> None:
    completion = (
        f"{reading.completion.percentage}% complete"
        if reading.completion.percentage is not None
        else "Completion not yet measurable"
    )
    technology_cards = "".join(
        f"""
        <article class="tech-card">
          <h3>{escape(technology.name)}</h3>
          <p><strong>What is it?</strong> {escape(technology.simple_explanation)}</p>
          <p><strong>What does it do here?</strong> {escape(technology.use_here)}</p>
          <p><strong>Why was it used?</strong> {escape(technology.reason_used)}</p>
          <p class="evidence">Reason: {escape(technology.reason_strength.value)}</p>
          <p><strong>Where can I see it?</strong> {escape(technology.location)}</p>
          <p><strong>Why does it matter?</strong> {escape(technology.why_it_matters)}</p>
        </article>
        """
        for technology in reading.technologies
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
.evidence {{ font-size: .9rem; }}
:focus-visible {{ outline: 4px solid currentColor; outline-offset: 4px; }}
@media (prefers-reduced-motion: no-preference) {{ a.button:hover {{ transform: translateY(-2px); }} }}
</style>
</head>
<body>
<main>
<p><strong>Project Reader</strong></p>
<h1>{escape(reading.name)}</h1>
<p class="lead">{escape(reading.explanation)}</p>
<p><strong>Status:</strong> {escape(reading.status)}</p>

<section class="score-grid" aria-label="Project scores">
  <article class="score">
    <h2>How complete?</h2>
    <p class="big">{escape(completion)}</p>
    <p>{escape(reading.completion.explanation)}</p>
    <p class="evidence">Evidence: {escape(reading.completion.evidence_strength.value)}</p>
  </article>
  <article class="score">
    <h2>Likely to finish?</h2>
    <p class="big">{escape(reading.likelihood.label)}</p>
    <p>Estimated range: {reading.likelihood.range_low}–{reading.likelihood.range_high}%</p>
    <p>{escape(reading.likelihood.timeframe)}</p>
    <p class="evidence">Confidence: {escape(reading.likelihood.confidence)}</p>
  </article>
</section>

<section class="panel">
<h2>Done</h2>
<ul>{_items(reading.done, '✓')}</ul>
</section>

<section class="panel">
<h2>Still to do</h2>
<ul>{_items(reading.remaining, '○')}</ul>
</section>

<section>
<h2>Next</h2>
<p class="next">{escape(reading.next_step)}</p>
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
<p>The completion score uses accepted work against a defined finish line. The likelihood result uses project evidence and is a forecast, not a promise.</p>
</details>
</main>
</body>
</html>"""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(html, encoding="utf-8")
