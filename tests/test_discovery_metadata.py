from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


PUBLIC_HTML = Path("prototype/public-reader.html")
DESCRIPTION = (
    "Understand what a public GitHub project is, who it is for "
    "and what you can do with it."
)
PUBLIC_URL = "https://armpitpete.github.io/project-reader/"
BASELINE_BODY_SHA256 = (
    "896d7eb8e34412250e87418acb55d83889675ad95bd1bebf20b7be4b418971c2"
)


def document() -> str:
    return PUBLIC_HTML.read_text(encoding="utf-8")


def head(html: str) -> str:
    return html.split("<head>", 1)[1].split("</head>", 1)[0]


def body(html: str) -> str:
    return html.split("<body>", 1)[1]


def test_public_shell_exposes_complete_discovery_identity() -> None:
    html = document()
    page_head = head(html)

    expected_fragments = {
        "<title>Project Reader</title>",
        f'<meta name="description" content="{DESCRIPTION}">',
        f'<link rel="canonical" href="{PUBLIC_URL}">',
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="Project Reader">',
        '<meta property="og:title" content="Project Reader">',
        f'<meta property="og:description" content="{DESCRIPTION}">',
        f'<meta property="og:url" content="{PUBLIC_URL}">',
        '<meta name="twitter:card" content="summary">',
        '<meta name="twitter:title" content="Project Reader">',
        f'<meta name="twitter:description" content="{DESCRIPTION}">',
    }

    for fragment in expected_fragments:
        assert page_head.count(fragment) == 1

    assert (
        "default-src 'none'; base-uri 'none'; form-action 'self'; "
        "connect-src https://api.github.com https://raw.githubusercontent.com; "
        "img-src 'none'; style-src 'unsafe-inline'; script-src 'self';"
    ) in page_head


def test_structured_identity_matches_visible_project_reader_wording() -> None:
    html = document()
    matches = re.findall(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
        head(html),
        flags=re.DOTALL,
    )
    assert len(matches) == 1

    assert json.loads(matches[0]) == {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": "Project Reader",
        "url": PUBLIC_URL,
        "description": DESCRIPTION,
    }

    assert f"<p>{DESCRIPTION}</p>" in body(html)


def test_metadata_repair_does_not_change_visible_body_or_application() -> None:
    page_body = body(document())
    assert hashlib.sha256(page_body.encode("utf-8")).hexdigest() == BASELINE_BODY_SHA256
    assert '<script type="module" src="./app.js"></script>' in page_body
