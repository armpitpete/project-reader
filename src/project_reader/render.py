from __future__ import annotations

from html import escape
from pathlib import Path
import re
from urllib.parse import urlparse

from .models import Claim, Evidence, ProjectReading, RepositoryLanguage, Technology


_MAX_EVIDENCE_PREVIEW_CHARS = 12_000
_LINK = re.compile(r"(!)?\[([^\]]{0,240})\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_CODE_SPAN = re.compile(r"`([^`\n]+)`")
_BOLD = re.compile(r"\*\*([^*\n]+)\*\*")
_ITALIC = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
_TABLE_SEPARATOR = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")


RESULT_CSS = """
.project-reader-result {
  color-scheme: light;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 18px;
  line-height: 1.65;
  color: #1f2933;
  background: #faf9f6;
  max-width: 42rem;
}
.project-reader-result * {
  box-sizing: border-box;
}
.project-reader-result h1,
.project-reader-result h2,
.project-reader-result h3,
.project-reader-result h4,
.project-reader-result h5,
.project-reader-result h6 {
  color: #101820;
  line-height: 1.2;
  letter-spacing: 0;
}
.project-reader-result h1 {
  font-size: 2rem;
  margin: 0 0 .7rem;
}
.project-reader-result h2 {
  font-size: 1.35rem;
  margin: 0 0 .45rem;
}
.project-reader-result h3 {
  font-size: 1.08rem;
  margin-top: 1.5rem;
}
.project-reader-result h4 {
  font-size: 1rem;
  margin: 1rem 0 .5rem;
}
.project-reader-result h5,
.project-reader-result h6 {
  font-size: .98rem;
  margin: .85rem 0 .45rem;
}
.project-reader-result p,
.project-reader-result li {
  max-width: 62ch;
}
.project-reader-result a {
  color: #1b5e7a;
  text-underline-offset: .18em;
  overflow-wrap: anywhere;
}
.project-reader-result code {
  overflow-wrap: anywhere;
  word-break: break-word;
}
.project-reader-result :focus-visible {
  outline: 4px solid #0f5132;
  outline-offset: 4px;
}
.reader-flow {
  display: grid;
  gap: 1.75rem;
}
.reader-question {
  padding: .25rem 0 1.25rem;
  border-bottom: 1px solid #ded7ca;
}
.project-name,
.answer {
  font-size: 1.15rem;
  font-weight: 750;
  margin: .15rem 0 .4rem;
}
.project-reader-result ul,
.project-reader-result ol {
  padding-left: 1.25rem;
}
.project-reader-result li {
  margin: .55rem 0;
}
.disclosures {
  display: grid;
  gap: .6rem;
  margin-top: 2.5rem;
}
.project-reader-result details {
  border-top: 1px solid #ded7ca;
  padding: 1rem 0;
}
.project-reader-result summary {
  cursor: pointer;
  font-size: 1.08rem;
  font-weight: 800;
}
.evidence-map {
  display: grid;
  gap: .75rem;
  list-style: none;
  padding-left: 0;
}
.evidence-map li {
  display: grid;
  gap: .25rem;
}
.evidence-list,
.source-meta {
  padding-left: 1.35rem;
}
.evidence-list > li {
  margin: .8rem 0;
}
.evidence-source {
  display: flex;
  flex-wrap: wrap;
  gap: .65rem;
  align-items: baseline;
  margin: .65rem 0;
}
.evidence-source a,
.source-action {
  font-weight: 760;
}
.evidence-preview {
  max-width: 100%;
  overflow-wrap: anywhere;
}
.evidence-preview pre,
.evidence-preview code {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.evidence-preview pre {
  border: 1px solid #ded7ca;
  background: #fff;
  padding: .85rem;
  overflow: visible;
}
.evidence-preview table {
  width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
}
.evidence-preview th,
.evidence-preview td {
  border: 1px solid #ded7ca;
  padding: .45rem .55rem;
  text-align: left;
  vertical-align: top;
}
.evidence-preview blockquote {
  border-left: 4px solid #ded7ca;
  margin: 1rem 0;
  padding-left: 1rem;
  color: #3f4a56;
}
.evidence-note,
.evidence,
.evidence-strength,
.source-meta {
  font-size: .95rem;
}
.evidence-strength {
  margin-left: .35rem;
}
.tech-grid {
  display: grid;
  gap: 1.25rem;
  margin-top: 1rem;
}
.technical-section {
  margin-top: 1.5rem;
}
.language-list {
  display: grid;
  gap: .85rem;
  padding-left: 0;
  list-style: none;
}
.language-card {
  border-top: 1px solid #ded7ca;
  padding-top: .75rem;
}
.language-card p {
  margin: .35rem 0;
}
.evidence-link {
  font-size: .95rem;
}
.tech-card {
  border-top: 1px solid #ded7ca;
  padding-top: .75rem;
}
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: .75rem;
  margin-top: 1.5rem;
}
.button {
  display: inline-block;
  border: 2px solid #1f2933;
  border-radius: .4rem;
  color: #1f2933;
  padding: .65rem .85rem;
  text-decoration: none;
  font-weight: 750;
}
@media (max-width: 700px) {
  .project-reader-result {
    font-size: 17px;
  }
  .project-reader-result h1 {
    font-size: 1.7rem;
  }
  .actions {
    display: grid;
  }
}
@media (prefers-reduced-motion: reduce) {
  .project-reader-result *,
  .project-reader-result *::before,
  .project-reader-result *::after {
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: .01ms !important;
  }
}
""".strip()


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


def _external_attrs(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme in {"http", "https"}:
        return ' target="_blank" rel="noopener noreferrer"'
    if parsed.scheme == "mailto":
        return ' rel="noopener noreferrer"'
    return ""


def _external_link(url: str, label: str, *, class_name: str | None = None) -> str:
    safe = _safe_url(url)
    class_html = f' class="{escape(class_name)}"' if class_name else ""
    return (
        f'<a{class_html} href="{escape(safe)}"{_external_attrs(safe)}>'
        f"{escape(label)}</a>"
    )


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
        _external_link(evidence_by_key[key].source, evidence_by_key[key].label)
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


def _stash(html: str, placeholders: list[str]) -> str:
    token = f"@@PROJECT_READER_HTML_{len(placeholders)}@@"
    placeholders.append(html)
    return token


def _render_inline_markdown(text: str) -> str:
    placeholders: list[str] = []

    def link(match: re.Match[str]) -> str:
        alt_marker, label, url = match.groups()
        if alt_marker:
            return _stash(f'<span class="image-alt">Image: {escape(label)}</span>', placeholders)
        try:
            safe = _safe_url(url)
        except ValueError:
            return _stash(escape(label), placeholders)
        return _stash(
            f'<a href="{escape(safe)}"{_external_attrs(safe)}>{escape(label)}</a>',
            placeholders,
        )

    def code(match: re.Match[str]) -> str:
        return _stash(f"<code>{escape(match.group(1))}</code>", placeholders)

    rendered = _LINK.sub(link, text)
    rendered = _CODE_SPAN.sub(code, rendered)
    rendered = escape(rendered)
    rendered = _BOLD.sub(r"<strong>\1</strong>", rendered)
    rendered = _ITALIC.sub(r"<em>\1</em>", rendered)
    for index, html in enumerate(placeholders):
        rendered = rendered.replace(f"@@PROJECT_READER_HTML_{index}@@", html)
    return rendered


def _flush_paragraph(buffer: list[str], output: list[str]) -> None:
    if buffer:
        output.append(f"<p>{_render_inline_markdown(' '.join(buffer))}</p>")
        buffer.clear()


def _flush_list(kind: str | None, items: list[str], output: list[str]) -> None:
    if kind and items:
        output.append(f"<{kind}>{''.join(f'<li>{item}</li>' for item in items)}</{kind}>")
        items.clear()


def _split_table_row(line: str) -> list[str]:
    stripped = line.strip().strip("|")
    return [cell.strip() for cell in stripped.split("|")]


def _render_table(lines: list[str]) -> str:
    headers = _split_table_row(lines[0])
    body_lines = lines[2:]
    head = "".join(f"<th>{_render_inline_markdown(cell)}</th>" for cell in headers)
    rows = []
    for line in body_lines:
        cells = _split_table_row(line)
        rows.append(
            "<tr>"
            + "".join(f"<td>{_render_inline_markdown(cell)}</td>" for cell in cells)
            + "</tr>"
        )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def _render_markdown(content: str) -> str:
    lines = content[:_MAX_EVIDENCE_PREVIEW_CHARS].splitlines()
    output: list[str] = []
    paragraph: list[str] = []
    list_kind: str | None = None
    list_items: list[str] = []
    index = 0

    while index < len(lines):
        raw = lines[index]
        stripped = raw.strip()

        if stripped.startswith(("```", "~~~")):
            _flush_paragraph(paragraph, output)
            _flush_list(list_kind, list_items, output)
            list_kind = None
            fence = stripped[:3]
            code: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith(fence):
                code.append(lines[index])
                index += 1
            output.append(f"<pre><code>{escape(chr(10).join(code))}</code></pre>")
        elif not stripped:
            _flush_paragraph(paragraph, output)
            _flush_list(list_kind, list_items, output)
            list_kind = None
        elif stripped.startswith("#"):
            match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
            if match:
                _flush_paragraph(paragraph, output)
                _flush_list(list_kind, list_items, output)
                list_kind = None
                level = min(6, len(match.group(1)) + 3)
                output.append(f"<h{level}>{_render_inline_markdown(match.group(2))}</h{level}>")
            else:
                paragraph.append(stripped)
        elif (
            "|" in stripped
            and index + 1 < len(lines)
            and _TABLE_SEPARATOR.match(lines[index + 1])
        ):
            _flush_paragraph(paragraph, output)
            _flush_list(list_kind, list_items, output)
            list_kind = None
            table_lines = [stripped, lines[index + 1].strip()]
            index += 2
            while index < len(lines) and "|" in lines[index].strip():
                table_lines.append(lines[index].strip())
                index += 1
            index -= 1
            output.append(_render_table(table_lines))
        elif match := re.match(r"^[-*+]\s+(.+)$", stripped):
            _flush_paragraph(paragraph, output)
            if list_kind not in {None, "ul"}:
                _flush_list(list_kind, list_items, output)
            list_kind = "ul"
            list_items.append(_render_inline_markdown(match.group(1)))
        elif match := re.match(r"^\d+[.)]\s+(.+)$", stripped):
            _flush_paragraph(paragraph, output)
            if list_kind not in {None, "ol"}:
                _flush_list(list_kind, list_items, output)
            list_kind = "ol"
            list_items.append(_render_inline_markdown(match.group(1)))
        elif match := re.match(r"^>\s?(.*)$", stripped):
            _flush_paragraph(paragraph, output)
            _flush_list(list_kind, list_items, output)
            list_kind = None
            output.append(f"<blockquote><p>{_render_inline_markdown(match.group(1))}</p></blockquote>")
        else:
            _flush_list(list_kind, list_items, output)
            list_kind = None
            paragraph.append(stripped)
        index += 1

    _flush_paragraph(paragraph, output)
    _flush_list(list_kind, list_items, output)
    if len(content) > _MAX_EVIDENCE_PREVIEW_CHARS:
        output.append(
            '<p class="evidence-note">This readable preview is shortened. '
            "Use the original source link for the complete file.</p>"
        )
    return "\n".join(output) or "<p>This evidence file is empty.</p>"


def _render_text_evidence(content: str, *, truncated: bool) -> str:
    preview = content[:_MAX_EVIDENCE_PREVIEW_CHARS]
    note = (
        '<p class="evidence-note">This readable preview is shortened. '
        "Use the original source link for the complete file.</p>"
        if truncated or len(content) > _MAX_EVIDENCE_PREVIEW_CHARS
        else ""
    )
    return f"<pre><code>{escape(preview)}</code></pre>{note}"


def _evidence_preview(item: Evidence) -> str:
    if item.content is None:
        return (
            '<p class="evidence-note">Project Reader has an exact source link for this evidence, '
            "but no readable inline text preview is available.</p>"
        )
    if item.content_format == "markdown":
        return _render_markdown(item.content)
    return _render_text_evidence(item.content, truncated=item.truncated)


def _evidence_items(reading: ProjectReading) -> str:
    return "".join(
        f"""
        <li id="evidence-{escape(item.key)}">
          <details class="evidence-source-detail">
            <summary>{escape(item.label)} <span class="evidence-strength">{escape(item.strength.value)}</span></summary>
            <div class="evidence-source">
              {_external_link(item.source, "Open original source", class_name="source-action")}
              <span class="evidence-note">Readable preview rendered safely by Project Reader.</span>
            </div>
            <div class="evidence-preview">{_evidence_preview(item)}</div>
          </details>
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
<h3>Readable evidence and exact sources</h3>
<ol class="evidence-list">{_evidence_items(reading)}</ol>
{source_meta_html}
</details>"""


def _language_evidence_link(language: RepositoryLanguage) -> str:
    if not language.evidence_keys:
        return ""
    key = escape(language.evidence_keys[0])
    return f' <a class="evidence-link" href="#evidence-{key}">Evidence</a>'


_LANGUAGE_CATALOGUE: dict[str, tuple[str, str]] = {
    "typescript": (
        "TypeScript is JavaScript with extra checks that help developers catch some mistakes before the program runs.",
        "It is usually used for larger websites and apps where developers want safer interactive code.",
    ),
    "javascript": (
        "JavaScript is a programming language that can make websites and tools interactive.",
        "It is usually used in browsers, web apps, build tools and some servers.",
    ),
    "html": (
        "HTML gives a web page its structure, such as headings, text, forms and buttons.",
        "It is usually used to describe the content a browser should show.",
    ),
    "css": (
        "CSS controls how a web page looks, including spacing, layout, size and colour.",
        "It is usually used to style HTML so pages are readable and responsive.",
    ),
    "python": (
        "Python is a programming language designed to be readable and practical.",
        "It is usually used for scripts, web services, data work, automation and tests.",
    ),
    "c++": (
        "C++ is a programming language used when software needs close control over speed and memory.",
        "It is usually used for engines, desktop apps, games, audio tools and performance-sensitive systems.",
    ),
    "c": (
        "C is a small, low-level programming language that works close to the computer.",
        "It is usually used for operating systems, embedded software and performance-critical libraries.",
    ),
    "c#": (
        "C# is a programming language from Microsoft for building apps, services and games.",
        "It is usually used with .NET, Windows software, web services and Unity projects.",
    ),
    "java": (
        "Java is a programming language designed to run on many kinds of computers.",
        "It is usually used for Android apps, servers, business systems and teaching.",
    ),
    "shell": (
        "Shell scripts are command-line instructions saved in files.",
        "They are usually used to automate setup, deployment, tests and maintenance tasks.",
    ),
    "powershell": (
        "PowerShell is a command and scripting language often used on Windows and servers.",
        "It is usually used for automation, administration, setup scripts and deployment tasks.",
    ),
    "sourcepawn": (
        "SourcePawn is a scripting language used for Source engine game server plugins.",
        "It is usually used to customise game server behaviour, commands and rules.",
    ),
    "pawn": (
        "Pawn is a small scripting language used to embed custom logic in other systems.",
        "It is usually used for plugins, game servers and constrained scripting environments.",
    ),
}


def _language_catalogue_entry(name: str) -> tuple[str, str]:
    normal = name.casefold()
    return _LANGUAGE_CATALOGUE.get(
        normal,
        (
            f"{name} is a repository language detected by GitHub Linguist.",
            "Project Reader does not yet have a beginner catalogue entry for this language, so it only reports the measured evidence.",
        ),
    )


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
        <li class="language-card">
          <h4>{escape(language.name)}</h4>
          <p><strong>What is it?</strong> {escape(_language_catalogue_entry(language.name)[0])}</p>
          <p><strong>What does it usually do?</strong> {escape(_language_catalogue_entry(language.name)[1])}</p>
          <p><strong>What does it do in this project?</strong> Project Reader has not collected project-specific evidence explaining this language's role here. The percentage alone is not enough to infer that.</p>
          <p><strong>Detected amount:</strong> {escape(_format_percentage(language.percentage))}% of detected code. {_language_evidence_link(language)}</p>
        </li>
        """
        for language in reading.repository_languages
    )
    return f"""
<section class="technical-section">
  <h3>Repository languages</h3>
  <p>These percentages describe detected repository code volume. They do not prove importance, difficulty, authorship effort, why a language was chosen or what it does in this specific project.</p>
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


def render_html_fragment(reading: ProjectReading) -> str:
    done_content = (
        f"<ul>{_items(reading.done)}</ul>"
        if reading.done
        else "<p>Nothing is confirmed as finished yet.</p>"
    )
    actions = "".join(
        (
            _external_link(reading.project_url, "View the project", class_name="button")
            if reading.project_url
            else "",
            _external_link(reading.contact_url, "Contact the project owner", class_name="button")
            if reading.contact_url
            else "",
        )
    )
    actions_html = (
        f'<nav class="actions" aria-label="Project links">{actions}</nav>'
        if actions
        else ""
    )

    html = f"""<style data-project-reader-result-style>
{RESULT_CSS}
</style>
<article class="project-reader-result">
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
</article>"""
    return "\n".join(line.rstrip() for line in html.splitlines()) + "\n"


def render_html_string(reading: ProjectReading) -> str:
    fragment = render_html_fragment(reading)
    html = f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(reading.name)} - Project Reader</title>
</head>
<body>
<main>
{fragment}</main>
</body>
</html>"""
    return "\n".join(line.rstrip() for line in html.splitlines()) + "\n"


def render_html(reading: ProjectReading, destination: Path) -> None:
    html = render_html_string(reading)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(html, encoding="utf-8")
