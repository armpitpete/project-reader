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
_HASH = re.compile(r"\b[0-9a-f]{12,40}\b", re.I)
_ISSUE_PATH = re.compile(r"\b(?:issues|pull|pulls)/\d+\b", re.I)
_ISSUE_NUMBER = re.compile(r"(?<![A-Za-z0-9])#\d+\b")
_FILE_PATH = re.compile(
    r"(?<![A-Za-z0-9])(?:\.github/[\w./-]+|[\w.-]+\.(?:md|markdown|json|toml|ya?ml|js|jsx|ts|tsx|css|html|py|sh|ps1|yml|yaml))(?![A-Za-z0-9])",
    re.I,
)
_COMMAND = re.compile(r"\b(?:npm|pnpm|yarn|python|pip|uvicorn|git)\s+[A-Za-z0-9:_./ -]+")


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
.reader-flow > h1 {
  margin-bottom: -.35rem;
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
.detail-note {
  color: #3f4a56;
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


def _simple_text(value: str) -> str:
    result = value
    replacements = (
        ("owner-authority", "approved"),
        ("Owner-authority", "Approved"),
        ("authority-backed", "evidence-backed"),
        ("Authority-backed", "Evidence-backed"),
        ("technology manifest", "technology list"),
        ("Technology manifest", "Technology list"),
        ("deployment workflow", "publishing setup"),
        ("Deployment workflow", "Publishing setup"),
    )
    for old, new in replacements:
        result = result.replace(old, new)
    result = _ISSUE_PATH.sub("a GitHub item", result)
    result = _ISSUE_NUMBER.sub("a numbered GitHub item", result)
    result = _HASH.sub("an exact saved version", result)
    result = _FILE_PATH.sub("a project file", result)
    result = _COMMAND.sub("a setup instruction", result)
    return result


def _claim_text(claim: Claim, *, simple: bool = False) -> str:
    return escape(_simple_text(claim.text) if simple else claim.text)


def _items(values: tuple[Claim, ...], *, simple: bool = False) -> str:
    return "".join(f"<li>{_claim_text(value, simple=simple)}</li>" for value in values)


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


def _remaining_content(reading: ProjectReading, *, simple: bool = False) -> str:
    if reading.remaining:
        return f"<ul>{_items(reading.remaining, simple=simple)}</ul>"
    if reading.remaining_empty:
        return f"<p>{_claim_text(reading.remaining_empty, simple=simple)}</p>"
    return "<p>Project Reader did not find clear public evidence listing unfinished work.</p>"


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
        ("What appears to work or be finished?", done_keys or reading.completion.evidence_keys),
        ("What is unfinished or unclear?", remaining_keys),
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


def _question_reason_summary(reading: ProjectReading) -> str:
    done_keys = _unique(
        tuple(key for claim in reading.done for key in claim.evidence_keys)
    )
    remaining_keys = _unique(
        tuple(key for claim in reading.remaining for key in claim.evidence_keys)
        + (reading.remaining_empty.evidence_keys if reading.remaining_empty else ())
    )
    rows = (
        ("Project description", reading.explanation.evidence_keys),
        ("Finished or working parts", done_keys or reading.completion.evidence_keys),
        ("Unfinished or unclear parts", remaining_keys),
        ("Completion and likelihood", _unique(reading.likelihood.evidence_keys + reading.completion.evidence_keys)),
        ("Suggested next step", reading.next_step.evidence_keys),
    )

    def summary(keys: tuple[str, ...]) -> str:
        count = len(_unique(keys))
        if count == 0:
            return "No direct public evidence was connected to this answer."
        if count == 1:
            return "One collected public evidence item supports this answer."
        return f"{count} collected public evidence items support this answer."

    return "".join(
        f"""
        <li>
          <strong>{escape(label)}</strong>
          <span>{escape(summary(keys))}</span>
        </li>
        """
        for label, keys in rows
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
        return '<p class="evidence-note">No readable text preview is available for this source.</p>'
    if item.content_format == "markdown":
        return _render_markdown(item.content)
    return _render_text_evidence(item.content, truncated=item.truncated)


def _source_status(item: Evidence) -> str:
    if item.content is None:
        return "No readable preview is available."
    if item.truncated:
        return "Readable preview below is shortened."
    return "Readable preview below."


def _evidence_items(reading: ProjectReading) -> str:
    return "".join(
        f"""
        <li id="evidence-{escape(item.key)}">
          <details class="evidence-source-detail">
            <summary>{escape(item.label)}</summary>
            <div class="evidence-source">
              {_external_link(item.source, "Open original source", class_name="source-action")}
              <span class="evidence-note">{escape(_source_status(item))}</span>
            </div>
            <div class="evidence-preview">{_evidence_preview(item)}</div>
          </details>
        </li>
        """
        for item in reading.evidence
    )


def _format_percentage(value: float) -> str:
    return f"{value:.1f}".rstrip("0").rstrip(".")


def _status_reason_section(reading: ProjectReading) -> str:
    completion = escape(_completion_text(reading))
    completion_explanation = escape(_completion_explanation(reading.completion.explanation))
    likelihood = escape(_likelihood_answer(reading))
    likelihood_explanation = escape(_likelihood_explanation(reading))
    uncertainty = (
        "Project Reader cannot give a measured completion answer from the collected evidence."
        if reading.completion.percentage is None
        else "Project Reader found a defined set of planned parts for this reading."
    )
    if reading.likelihood.label == "Unknown":
        uncertainty += " It also does not have enough evidence for a clear likelihood answer."
    elif reading.likelihood.label == "Already complete":
        uncertainty += " The current planned work appears finished in the collected evidence."

    contact = (
        f'<p>{_external_link(reading.contact_url, "Contact the project owner", class_name="button")}</p>'
        if reading.contact_url
        else ""
    )

    return f"""<details class="status-detail">
<summary>Project status and reasons</summary>
<p class="detail-note">This section explains completion, likelihood and uncertainty. Exact source names and technical details are in the next section.</p>
<section class="technical-section" aria-labelledby="status-completion">
  <h2 id="status-completion">Completion</h2>
  <p class="answer">{completion}</p>
  <p>{completion_explanation}</p>
</section>
<section class="technical-section" aria-labelledby="status-likelihood">
  <h2 id="status-likelihood">Will the current plan be finished?</h2>
  <p class="answer">{likelihood}</p>
  <p>{likelihood_explanation}</p>
</section>
<section class="technical-section" aria-labelledby="status-uncertainty">
  <h2 id="status-uncertainty">Uncertainty</h2>
  <p>{escape(uncertainty)}</p>
</section>
<section class="technical-section" aria-labelledby="status-reasons">
  <h2 id="status-reasons">Simplified supporting reasons</h2>
  <ul class="evidence-map">{_question_reason_summary(reading)}</ul>
  <p>GitHub issues are public discussion pages. Pull requests are proposed changes. Project Reader keeps their exact numbers and links in the technical sources section.</p>
</section>
<section class="technical-section" aria-labelledby="status-next-step">
  <h2 id="status-next-step">Useful next step</h2>
  <p>{_claim_text(reading.next_step, simple=True)}</p>
  {contact}
</section>
</details>"""


def _technical_sources_section(reading: ProjectReading) -> str:
    if not reading.evidence:
        return """<details class="technical-sources">
<summary>Technical sources and repository details</summary>
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

    return f"""<details class="technical-sources">
<summary>Technical sources and repository details</summary>
<p>This section keeps the exact issue and pull-request identifiers, file paths, package manifests, README technical sections, commands, workflows, deployment details, commits, hashes, timestamps and original source links.</p>
<h3>Exact links behind the answers</h3>
<ul class="evidence-map">{_question_evidence(reading, evidence_by_key)}</ul>
<h3>Original sources and readable previews</h3>
<ol class="evidence-list">{_evidence_items(reading)}</ol>
{_technical_section(reading)}
{source_meta_html}
</details>"""


def _language_evidence_link(language: RepositoryLanguage) -> str:
    if not language.evidence_keys:
        return ""
    key = escape(language.evidence_keys[0])
    return f' <a class="evidence-link" href="#evidence-{key}">Evidence</a>'


_LANGUAGE_CATALOGUE: dict[str, tuple[str, str, str]] = {
    "typescript": (
        "TypeScript is a way of writing instructions for a website or app. It is based on JavaScript, another coding language used to make pages respond when someone presses a button, moves a control or enters information. TypeScript adds checks that can warn about some mistakes before the program is used.",
        "It can help make buttons, controls and information on a page behave in a planned way.",
        "A project might use it when the makers want warnings about some mistakes before people use the page or app.",
    ),
    "javascript": (
        "JavaScript is a coding language used to tell a web page what to do after it opens.",
        "It can make buttons respond, page sections change, forms check information, or controls move.",
        "A project might use it when a page needs to react to what someone does.",
    ),
    "html": (
        "HTML describes what is on a web page, such as headings, paragraphs, pictures, buttons and forms. It gives the page its basic structure.",
        "It can put the main parts of a page in order so people and screen readers can follow them.",
        "A project might use it because every web page needs a clear structure.",
    ),
    "css": (
        "CSS is a set of appearance rules for a web page. It controls things people can see, such as spacing, text size, colours and where items sit on the screen.",
        "It can make a page easier to read on large screens and small screens.",
        "A project might use it to keep the page clear, readable and consistent.",
    ),
    "python": (
        "Python is a coding language written to be comparatively easy for people to read.",
        "It can help sort information, check files, make reports, answer requests, or repeat tasks.",
        "A project might use it when the makers want clear instructions that are practical to maintain.",
    ),
    "c++": (
        "C++ is a coding language often used for programs that need careful control over speed and computer memory.",
        "It can help make games, audio tools, desktop programs or parts of a program that must respond quickly.",
        "A project might use it when speed and detailed control matter.",
    ),
    "c": (
        "C is an older coding language used for instructions that work close to a computer's basic parts.",
        "It can help make small, fast pieces of software or instructions for devices.",
        "A project might use it when it needs simple instructions with careful control over the computer.",
    ),
    "c#": (
        "C# is a coding language often used to make apps, tools and games.",
        "It can help make windows, screens, game behaviour, stored information and app actions.",
        "A project might use it when the makers want one language for a complete app or game.",
    ),
    "java": (
        "Java is a coding language designed so the same program can work on many kinds of computers.",
        "It can help make phone apps, business tools, learning examples and larger programs.",
        "A project might use it when the program needs to work in many places.",
    ),
    "go": (
        "Go is a coding language designed for clear programs that can handle many tasks at once.",
        "It can help make tools that answer requests, move information around, or run background jobs.",
        "A project might use it when the makers want a small, fast program that is straightforward to operate.",
    ),
    "rust": (
        "Rust is a coding language designed to help avoid some memory mistakes while still running quickly.",
        "It can help make tools, games, device instructions or important parts of larger programs.",
        "A project might use it when both speed and mistake-checking are important.",
    ),
    "php": (
        "PHP is a coding language often used to make web pages on a website.",
        "It can help choose what information a page should show before someone sees it.",
        "A project might use it when a website needs pages made from stored information.",
    ),
    "ruby": (
        "Ruby is a coding language designed to be pleasant for people to write and read.",
        "It can help make websites, tools, reports and repeated project tasks.",
        "A project might use it when the makers value readable instructions and quick changes.",
    ),
    "swift": (
        "Swift is a coding language often used for apps on Apple devices.",
        "It can help make screens, buttons, saved information and app behaviour.",
        "A project might use it when the project is meant for iPhone, iPad, Mac or similar devices.",
    ),
    "kotlin": (
        "Kotlin is a coding language often used for Android apps and other programs.",
        "It can help make screens, buttons, stored information and app behaviour.",
        "A project might use it when the makers want modern app instructions that are checked for some mistakes.",
    ),
    "dart": (
        "Dart is a coding language often used to make apps that share much of the same work across phones, computers and web pages.",
        "It can help make screens, controls and app behaviour.",
        "A project might use it when the makers want one app idea to work in several places.",
    ),
    "shell": (
        "A shell script is a saved list of computer instructions that a person could otherwise type one by one.",
        "It can help repeat setup chores, checks or file tasks.",
        "A project might use it so people do not have to remember a long set of steps.",
    ),
    "powershell": (
        "PowerShell is a way to write repeatable computer instructions, especially on Windows.",
        "It can help set up files, check a project, or repeat maintenance tasks.",
        "A project might use it to make Windows tasks easier to repeat.",
    ),
    "sourcepawn": (
        "SourcePawn is a coding language used to change how some shared online games behave.",
        "It can add game rules, player messages, controls or small custom features.",
        "A project might use it when the project is about custom behaviour for those games.",
    ),
    "pawn": (
        "Pawn is a small coding language used inside some games and tools.",
        "It can add custom rules or actions to a larger project.",
        "A project might use it when it needs small instructions inside another program.",
    ),
    "json": (
        "JSON is a text format for storing labelled information in a way programs can read.",
        "It can hold settings, lists, records or status information.",
        "A project might use it when information needs to be easy for both people and programs to check.",
    ),
    "markdown": (
        "Markdown is a plain writing format that uses simple marks for headings, lists and links.",
        "It can help make project notes readable on GitHub and in other tools.",
        "A project might use it for README files, plans, notes or instructions.",
    ),
    "yaml": (
        "YAML is a text format often used for settings and lists.",
        "It can help describe project checks, options or repeated tasks.",
        "A project might use it when settings need to be readable as plain text.",
    ),
    "dockerfile": (
        "A Dockerfile is a recipe that tells Docker how to prepare the pieces a program needs to run.",
        "It can help make the same project setup repeatable on another computer.",
        "A project might use it so people can prepare the project in a consistent way.",
    ),
    "scss": (
        "SCSS is a way of writing CSS, the appearance rules that control web page spacing, text size, colours and layout.",
        "It can help organise appearance rules before they become ordinary CSS.",
        "A project might use it when a web page has many appearance rules to maintain.",
    ),
    "jupyter notebook": (
        "A Jupyter Notebook is a document that mixes writing, code and visible results in one place.",
        "It can help explain data, calculations or experiments step by step.",
        "A project might use it when the work needs both notes and results together.",
    ),
    "vue": (
        "Vue is a way to make parts of a web page change when someone uses it.",
        "It can help connect page controls to information shown on the screen.",
        "A project might use it when a page has many changing parts.",
    ),
    "svelte": (
        "Svelte is a way to write web page parts that can change when someone uses them.",
        "It can help make controls, forms and changing page sections.",
        "A project might use it when the makers want web page parts that are organised and responsive.",
    ),
    "makefile": (
        "A Makefile is a recipe of repeated project tasks.",
        "It can help run checks, prepare files or repeat steps in the same order.",
        "A project might use it so common tasks have one named place.",
    ),
}


def _language_catalogue_entry(name: str) -> tuple[str, str, str]:
    normal = name.casefold()
    return _LANGUAGE_CATALOGUE.get(
        normal,
        (
            f"{name} is a kind of project file or coding language detected in this project.",
            "Project Reader does not yet have a plain example for what it helps make happen.",
            "Project Reader should not guess why this project uses it without clearer evidence.",
        ),
    )


def _language_role_unknown() -> str:
    return (
        "Project Reader found this kind of file in the project, but the amount alone does not show "
        "what it does here."
    )


def _simple_language_section(reading: ProjectReading) -> str:
    if not reading.repository_languages:
        return """
<section class="reader-question" aria-labelledby="question-made-with">
  <h2 id="question-made-with">What was it made with?</h2>
  <p>Project Reader does not have current public language evidence for this project.</p>
</section>
"""

    items = "".join(
        (
            lambda entry: f"""
        <li class="language-card">
          <h3>{escape(language.name)}</h3>
          <p><strong>What is it?</strong> {escape(entry[0])}</p>
          <p><strong>What can it help make happen?</strong> {escape(entry[1])}</p>
          <p><strong>Why might a project use it?</strong> {escape(entry[2])}</p>
          <p><strong>What does it do in this project?</strong> {escape(_language_role_unknown())}</p>
        </li>
        """
        )(_language_catalogue_entry(language.name))
        for language in reading.repository_languages
    )
    return f"""
<section class="reader-question" aria-labelledby="question-made-with">
  <h2 id="question-made-with">What was it made with?</h2>
  <p>Project Reader found these kinds of files. This is not the same as proving what each one is used for.</p>
  <ul class="language-list">{items}</ul>
</section>
"""


def _repository_language_technical_section(reading: ProjectReading) -> str:
    if not reading.repository_languages:
        return """
<section class="technical-section">
  <h3>Detected languages and amounts</h3>
  <p>Project Reader does not have current GitHub language evidence for this repository.</p>
</section>
"""

    items = "".join(
        f"""
        <li class="language-card">
          <h4>{escape(language.name)}</h4>
          <p><strong>Beginner explanation:</strong> {escape(_language_catalogue_entry(language.name)[0])}</p>
          <p><strong>Project-specific role:</strong> {_language_role_unknown()}</p>
          <p><strong>Detected amount:</strong> {escape(_format_percentage(language.percentage))}% of detected code. {_language_evidence_link(language)}</p>
        </li>
        """
        for language in reading.repository_languages
    )
    return f"""
<section class="technical-section">
  <h3>Detected languages and amounts</h3>
  <p>These percentages describe detected repository code volume measured by GitHub Linguist. They do not prove importance, difficulty, authorship effort, why a language was chosen or what it does in this specific project.</p>
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

    return f"""
{_repository_language_technical_section(reading)}
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
"""


def _project_use_content(reading: ProjectReading) -> str:
    if "does not state a clear purpose" in reading.explanation.text.casefold():
        return "<p>Project Reader does not have enough clear public evidence to say this yet.</p>"
    return f"<p>{_claim_text(reading.explanation, simple=True)}</p>"


def render_html_fragment(reading: ProjectReading) -> str:
    done_content = (
        f"<ul>{_items(reading.done, simple=True)}</ul>"
        if reading.done
        else "<p>Nothing is clearly shown as working or finished yet.</p>"
    )
    project_action = (
        _external_link(reading.project_url, "View the project", class_name="button")
        if reading.project_url
        else ""
    )
    actions_html = (
        f'<nav class="actions" aria-label="Project link">{project_action}</nav>'
        if project_action
        else ""
    )

    html = f"""<style data-project-reader-result-style>
{RESULT_CSS}
</style>
<article class="project-reader-result">
<section class="reader-flow simple-reading" aria-label="Simple reading">
  <h1>Simple reading</h1>
  <section class="reader-question" aria-labelledby="question-project">
    <h2 id="question-project">What is this project?</h2>
    <p class="project-name">{escape(reading.name)}</p>
    <p>{_claim_text(reading.explanation, simple=True)}</p>
  </section>

  <section class="reader-question" aria-labelledby="question-use">
    <h2 id="question-use">What can someone do with it?</h2>
    {_project_use_content(reading)}
  </section>

  <section class="reader-question" aria-labelledby="question-finished">
    <h2 id="question-finished">What appears to work or be finished?</h2>
    {done_content}
  </section>

  <section class="reader-question" aria-labelledby="question-remaining">
    <h2 id="question-remaining">What is unfinished or unclear?</h2>
    {_remaining_content(reading, simple=True)}
  </section>

  {_simple_language_section(reading)}

  {actions_html}
</section>

<section class="disclosures" aria-label="More detail">
{_status_reason_section(reading)}
{_technical_sources_section(reading)}
</section>
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
