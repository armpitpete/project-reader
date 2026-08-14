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
    "9e0686923dfcf3b6c67d5131acc75cef417bee508e126c0c3ceb5bed0ebff813"
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
        "connect-src https://api.github.com https://raw.githubusercontent.com https://collect.merrinworld.uk; "
        "img-src 'none'; style-src 'unsafe-inline'; script-src 'self' https://collect.merrinworld.uk;"
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


def test_analytics_change_preserves_application_and_has_exact_reviewed_body() -> None:
    page_body = body(document())
    assert hashlib.sha256(page_body.encode("utf-8")).hexdigest() == BASELINE_BODY_SHA256
    assert '<script type="module" src="./app.js"></script>' in page_body
    assert '<script src="https://collect.merrinworld.uk/beacon.js" data-site="project_reader" defer></script>' in page_body
    assert "random site-local browser token" in page_body
