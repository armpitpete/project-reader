from __future__ import annotations

from html import escape
from pathlib import Path
from urllib.parse import urlparse

from .models import Claim, Evidence, ProjectReading, RepositoryLanguage, Technology


def _safe_url(value: str) -> str:
    candidate = value.strip()
    parsed = urlparse(candidate)
    if not candidate or candidate != value or any(ord(char) < 32 for char in candidate):
        raise ValueError("Rendered URLs must be complete http, https or mailto URLs.")
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return candidate
    if parsed.scheme == "mailto" and parsed.path:
        return candidate
    raise ValueError("Rendered URLs must be complete http, https or mailto URLs.")


def _unique(keys: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(keys))


def _claim_text(claim: Claim) -> str:
    return escape(claim.text)


def _items(values: tuple[Claim, ...]) -> str:
    return "".join(f"<li>{_claim_text(value)}</li>" for value in values)


def _planned_parts() -> str:
    return "planned parts"


def _completion_text(reading: ProjectReading) -> str:
    if reading.completion.percentage is None:
        return "We cannot measure the planned parts yet."
    return f"{reading.completion.percentage}% of {_planned_parts()}"


def _completion_explanation(value: str) -> str:
    return (
        value.replace("defined work units", "planned parts")
        .replace("defined stages", "planned parts")
        .replace("accepted as done", "accepted as finished")
    )


def _likelihood_answer(reading: ProjectReading) -> str:
    if reading.likelihood.label == "Already complete":
        return "The current plan is finished"
    if reading.likelihood.label == "Unknown":
        return "We do not know yet"
    return f"{reading.likelihood.label} to be finished"


def _likelihood_explanation(reading: ProjectReading) -> str:
    if reading.likelihood.label == "Already complete":
        return "The evidence says the current planned work has been reached."
    if reading.likelihood.label == "Unknown":
        return "The collected evidence is not enough for a clear answer."
    return (
        f"Project Reader estimates a broad range of "
        f"{reading.likelihood.range_low}-{reading.likelihood.range_high}%."
    )


def _remaining_content(reading: ProjectReading) -> str:
    if reading.remaining:
        return f"<ul>{_items(reading.remaining)}</ul>"
    if reading.remaining_empty:
        return f"<p>{_claim_text(reading.remaining_empty)}</p>"
    return "<p>Nothing is currently listed.</p>"


def _evidence_links(keys: tuple[str, ...], evidence_by_key: dict[str, Evidence]) -> str:
    known_keys = [key for key in _unique(keys) if key in evidence_by_key]
    if not known_keys:
        return "<span>No direct evidence link is available for this answer.</span>"
    return ", ".join(
        f'<a href="{escape(_safe_url(evidence_by_key[key].source))}">'
        f"{escape(evidence_by_key[key].label)}</a>"
        for key in known_keys
    )


def _question_evidence(reading: ProjectReading, evidence_by_key: dict[str, Evidence]) -> str:
    done_keys = _unique(
        tuple(key for claim in reading.done for key in claim.evidence_keys)
    )
    remaining_keys = _unique(
        tuple(key for claim in reading.remaining for key in claim.evidence_keys)
        + (reading.remaining_empty.evidence_keys if reading.remaining_empty else ())
    )
    rows = (
        ("What is this project?", reading.explanation.evidence_keys),
        ("What has been finished?", done_keys or reading.completion.evidence_keys),
        ("What is still to do?", remaining_keys),
        (
            "Will the current plan be finished?",
            _unique(reading.likelihood.evidence_keys + reading.completion.evidence_keys),
        ),
        ("What happens next?", reading.next_step.evidence_keys),
    )
    return "".join(
        f"""
        <li>
          <strong>{escape(question)}</strong>
          <span>{_evidence_links(keys, evidence_by_key)}</span>
        </li>
        """
        for question, keys in rows
    )


def _evidence_items(reading: ProjectReading) -> str:
    return "".join(
        f"""
        <li id="evidence-{escape(item.key)}">
          <a href="{escape(_safe_url(item.source))}">{escape(item.label)}</a>
          <span class="evidence-strength">{escape(item.strength.value)}</span>
        </li>
        """
        for item in reading.evidence
    )


def _format_percentage(value: float) -> str:
    return f"{value:.1f}".rstrip("0").rstrip(".")


def _evidence_section(reading: ProjectReading) -> str:
    if not reading.evidence:
        return """<details class="evidence-disclosure">
<summary>How do we know?</summary>
<p>No source evidence was attached to this reading. Project Reader should show unknowns when evidence is missing.</p>
</details>"""

    evidence_by_key = {item.key: item for item in reading.evidence}
    source_meta: list[str] = []
    if reading.source_commit:
        source_meta.append(
            f"<li><strong>Source commit:</strong> <code>{escape(reading.source_commit)}</code></li>"
        )
    if reading.assessed_at:
        source_meta.append(
            f"<li><strong>Reading checked:</strong> {escape(reading.assessed_at)}</li>"
        )
    if reading.open_work_checked_at:
        source_meta.append(
            "<li><strong>Issues and pull requests checked:</strong> "
            f"{escape(reading.open_work_checked_at)}</li>"
        )
    source_meta_html = (
        f'<ul class="source-meta">{"".join(source_meta)}</ul>' if source_meta else ""
    )

    return f"""<details class="evidence-disclosure">
<summary>How do we know?</summary>
<p>Every important answer above is connected to collected evidence. If evidence is missing, stale or contradictory, Project Reader must say that the answer is unknown.</p>
<h3>Evidence behind the five answers</h3>
<ul class="evidence-map">{_question_evidence(reading, evidence_by_key)}</ul>
<h3>All evidence sources</h3>
<ol class="evidence-list">{_evidence_items(reading)}</ol>
{source_meta_html}
</details>"""


def _language_evidence_link(language: RepositoryLanguage) -> str:
    if not language.evidence_keys:
        return ""
    key = escape(language.evidence_keys[0])
    return f' <a class="evidence-link" href="#evidence-{key}">Evidence</a>'


def _repository_language_section(reading: ProjectReading) -> str:
    if not reading.repository_languages:
        return """
<section class="technical-section">
  <h3>Repository languages</h3>
  <p>Project Reader does not have current GitHub language evidence for this repository.</p>
</section>
"""

    items = "".join(
        f"""
        <li>
          <strong>{escape(language.name)}</strong>
          <span>{escape(_format_percentage(language.percentage))}% of detected code</span>
          {_language_evidence_link(language)}
        </li>
        """
        for language in reading.repository_languages
    )
    return f"""
<section class="technical-section">
  <h3>Repository languages</h3>
  <p>These percentages describe detected repository code volume. They do not prove importance, difficulty, authorship effort or why a language was chosen.</p>
  <ul class="language-list">{items}</ul>
</section>
"""


def _is_format_detail(technology: Technology) -> bool:
    normal = technology.name.casefold()
    return (
        "html" in normal
        or "json" in normal
        or "markdown" in normal
        or "format" in normal
    )


def _technology_cards(technologies: tuple[Technology, ...]) -> str:
    return "".join(
        f"""
        <article class="tech-card">
          <h4>{escape(technology.name)}</h4>
          <p><strong>What is it?</strong> {escape(technology.simple_explanation)}</p>
          <p><strong>What does it do here?</strong> {escape(technology.use_here)}</p>
          <p><strong>Why was it used?</strong> {escape(technology.reason_used)}</p>
          <p class="evidence">Evidence strength: {escape(technology.reason_strength.value)}</p>
          <p><strong>Where can I see it?</strong> {escape(technology.location)}</p>
          <p><strong>Why does it matter?</strong> {escape(technology.why_it_matters)}</p>
        </article>
        """
        for technology in technologies
    )


def _technical_section(reading: ProjectReading) -> str:
    language_names = {language.name.casefold() for language in reading.repository_languages}
    support_tools = tuple(
        technology
        for technology in reading.technologies
        if technology.name.casefold() not in language_names
        and not _is_format_detail(technology)
    )
    format_details = tuple(
        technology for technology in reading.technologies if _is_format_detail(technology)
    )
    support_html = _technology_cards(support_tools) or (
        "<p>No support tools are confirmed by the collected evidence.</p>"
    )
    format_html = _technology_cards(format_details) or (
        "<p>No formats or outputs are confirmed by the collected evidence.</p>"
    )

    return f"""<details class="technical-detail">
<summary>Technical details</summary>
{_repository_language_section(reading)}
<section class="technical-section">
  <h3>Support tools</h3>
  <div class="tech-grid">{support_html}</div>
</section>
<section class="technical-section">
  <h3>Formats and outputs</h3>
  <div class="tech-grid">{format_html}</div>
</section>
<section class="technical-section">
  <h3>How Project Reader analysed this</h3>
  <p>Project Reader collected public GitHub facts, exact repository files, open issue and pull request queues, and GitHub Linguist language data. Project Reader's own implementation is separate from the repository being analysed.</p>
</section>
</details>"""


def render_html_string(reading: ProjectReading) -> str:
    done_content = (
        f"<ul>{_items(reading.done)}</ul>"
        if reading.done
        else "<p>Nothing is confirmed as finished yet.</p>"
    )
    actions = "".join(
        (
            f'<a class="button" href="{escape(_safe_url(reading.project_url))}">'
            "View the project</a>"
            if reading.project_url
            else "",
            f'<a class="button" href="{escape(_safe_url(reading.contact_url))}">'
            "Contact the project owner</a>"
            if reading.contact_url
            else "",
        )
    )
    actions_html = (
        f'<nav class="actions" aria-label="Project links">{actions}</nav>'
        if actions
        else ""
    )

    html = f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(reading.name)} - Project Reader</title>
<style>
:root {{
  color-scheme: light;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 18px;
  line-height: 1.65;
}}
* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
  margin: 0;
  background: #faf9f6;
  color: #1f2933;
}}
main {{
  max-width: 42rem;
  margin: auto;
  padding: 2rem 1rem 4rem;
}}
h1, h2, h3 {{
  color: #101820;
  line-height: 1.2;
  letter-spacing: 0;
}}
h1 {{
  font-size: 2rem;
  margin: 0 0 .7rem;
}}
h2 {{
  font-size: 1.35rem;
  margin: 0 0 .45rem;
}}
h3 {{
  font-size: 1.08rem;
  margin-top: 1.5rem;
}}
h4 {{
  font-size: 1rem;
  margin: 0 0 .5rem;
}}
p, li {{
  max-width: 62ch;
}}
.reader-flow {{
  display: grid;
  gap: 1.75rem;
}}
.reader-question {{
  padding: .25rem 0 1.25rem;
  border-bottom: 1px solid #ded7ca;
}}
.project-name, .answer {{
  font-size: 1.15rem;
  font-weight: 750;
  margin: .15rem 0 .4rem;
}}
ul, ol {{
  padding-left: 1.25rem;
}}
li {{
  margin: .55rem 0;
}}
.disclosures {{
  display: grid;
  gap: .6rem;
  margin-top: 2.5rem;
}}
details {{
  border-top: 1px solid #ded7ca;
  padding: 1rem 0;
}}
summary {{
  cursor: pointer;
  font-size: 1.08rem;
  font-weight: 800;
}}
.evidence-map {{
  display: grid;
  gap: .75rem;
  list-style: none;
  padding-left: 0;
}}
.evidence-map li {{
  display: grid;
  gap: .25rem;
}}
.evidence-list, .source-meta {{
  padding-left: 1.35rem;
}}
.evidence, .evidence-strength, .source-meta {{
  font-size: .95rem;
}}
.evidence-strength {{
  margin-left: .35rem;
}}
.tech-grid {{
  display: grid;
  gap: 1.25rem;
  margin-top: 1rem;
}}
.technical-section {{
  margin-top: 1.5rem;
}}
.language-list {{
  display: grid;
  gap: .55rem;
  padding-left: 1.25rem;
}}
.language-list li {{
  display: grid;
  gap: .15rem;
}}
.evidence-link {{
  font-size: .95rem;
}}
.tech-card {{
  border-top: 1px solid #ded7ca;
  padding-top: .75rem;
}}
.actions {{
  display: flex;
  flex-wrap: wrap;
  gap: .75rem;
  margin-top: 1.5rem;
}}
.button {{
  display: inline-block;
  border: 2px solid #1f2933;
  border-radius: .4rem;
  color: #1f2933;
  padding: .65rem .85rem;
  text-decoration: none;
  font-weight: 750;
}}
a {{
  color: #1b5e7a;
  text-underline-offset: .18em;
}}
:focus-visible {{
  outline: 4px solid #0f5132;
  outline-offset: 4px;
}}
@media (max-width: 700px) {{
  main {{
    max-width: none;
    padding: 1.25rem 1rem 3rem;
  }}
  h1 {{
    font-size: 1.7rem;
  }}
}}
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: .01ms !important;
  }}
}}
</style>
</head>
<body>
<main>
<section class="reader-flow" aria-label="Project reading">
  <section class="reader-question" aria-labelledby="question-project">
    <h1 id="question-project">What is this project?</h1>
    <p class="project-name">{escape(reading.name)}</p>
    <p>{_claim_text(reading.explanation)}</p>
  </section>

  <section class="reader-question" aria-labelledby="question-finished">
    <h2 id="question-finished">What has been finished?</h2>
    {done_content}
  </section>

  <section class="reader-question" aria-labelledby="question-remaining">
    <h2 id="question-remaining">What is still to do?</h2>
    {_remaining_content(reading)}
  </section>

  <section class="reader-question" aria-labelledby="question-plan">
    <h2 id="question-plan">Will the current plan be finished?</h2>
    <p class="answer">{escape(_likelihood_answer(reading))}</p>
    <p>{escape(_completion_text(reading))}. {escape(_completion_explanation(reading.completion.explanation))}</p>
    <p>{escape(_likelihood_explanation(reading))}</p>
  </section>

  <section class="reader-question" aria-labelledby="question-next">
    <h2 id="question-next">What happens next?</h2>
    <p>{_claim_text(reading.next_step)}</p>
  </section>
</section>

<section class="disclosures" aria-label="More detail">
{_evidence_section(reading)}
{_technical_section(reading)}
</section>

{actions_html}
</main>
<script>
for (const summary of document.querySelectorAll("details > summary")) {{
  summary.addEventListener("keydown", (event) => {{
    if (event.key === "Enter" || event.key === " ") {{
      event.preventDefault();
      const details = summary.parentElement;
      if (details instanceof HTMLDetailsElement) {{
        details.open = !details.open;
      }}
    }}
  }});
}}
</script>
</body>
</html>"""
    html = "\n".join(line.rstrip() for line in html.splitlines()) + "\n"
    return html


def render_html(reading: ProjectReading, destination: Path) -> None:
    html = render_html_string(reading)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(html, encoding="utf-8")
