from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from functools import partial
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from threading import Thread
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from build_pages_site import build_pages_site


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DEFAULT_REPOSITORY = "armpitpete/sample-hold-lab"
READ_ENDPOINT = "https://reader-api.merrinworld.uk/api/v1/read"
FORBIDDEN_LEVEL_ONE = (
    re.compile(r"\bissues/\d+\b", re.I),
    re.compile(r"\bpulls?/\d+\b", re.I),
    re.compile(r"(?<![A-Za-z0-9])#\d+\b"),
    re.compile(r"\b[0-9a-f]{12,40}\b", re.I),
    re.compile(r"\b(?:README\.md|package\.json|pyproject\.toml)\b", re.I),
    re.compile(r"\.github/workflows", re.I),
    re.compile(r"\bnpm\s+(?:install|run)\b", re.I),
    re.compile(r"\b(?:build|deployment|workflow|manifest)\b", re.I),
)

from project_reader.api import APIConfig, default_pipeline


@contextmanager
def local_site(root: Path):
    handler = partial(SimpleHTTPRequestHandler, directory=str(root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def current_commit() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()


def assert_no_internal_result_scroll(page) -> None:
    offenders = page.evaluate(
        """
        () => {
          const result = document.querySelector("#reader-result");
          if (!result) return ["missing #reader-result"];
          const nodes = Array.from(result.querySelectorAll("*"));
          return nodes.flatMap((node) => {
            const style = getComputedStyle(node);
            const overflow = `${style.overflowX} ${style.overflowY} ${style.overflow}`;
            const canScroll = /(auto|scroll)/.test(overflow);
            const scrollable =
              canScroll
              && (node.scrollHeight > node.clientHeight + 2
                || node.scrollWidth > node.clientWidth + 2);
            return scrollable ? [`${node.tagName.toLowerCase()}.${node.className || ""}`] : [];
          });
        }
        """
    )
    if offenders:
        raise AssertionError(f"internal result scroll containers found: {offenders}")


def assert_no_horizontal_overflow(page) -> None:
    metrics = page.evaluate(
        """
        () => ({
          documentScrollWidth: document.documentElement.scrollWidth,
          documentClientWidth: document.documentElement.clientWidth,
          resultScrollWidth: document.querySelector("#reader-result")?.scrollWidth || 0,
          resultClientWidth: document.querySelector("#reader-result")?.clientWidth || 0,
        })
        """
    )
    if metrics["documentScrollWidth"] > metrics["documentClientWidth"] + 2:
        raise AssertionError(f"document has horizontal overflow: {metrics}")
    if metrics["resultScrollWidth"] > metrics["resultClientWidth"] + 2:
        raise AssertionError(f"result has horizontal overflow: {metrics}")


def assert_level_one(page) -> None:
    simple_text = page.locator("section.simple-reading").inner_text()
    required = (
        "Simple reading",
        "What is this project?",
        "What can someone do with it?",
        "What appears to work or be finished?",
        "What is unfinished or unclear?",
        "What was it made with?",
        "TypeScript is a way of writing instructions for a website or app.",
        "JavaScript, another coding language used to make pages respond",
        "CSS is a set of appearance rules for a web page.",
        "HTML describes what is on a web page",
        "the amount alone does not show what it does here",
        "View the project",
    )
    for phrase in required:
        if phrase not in simple_text:
            raise AssertionError(f"missing Level 1 phrase: {phrase}")
    if "Will the current plan be finished?" in simple_text:
        raise AssertionError("likelihood question leaked into Level 1")
    for pattern in FORBIDDEN_LEVEL_ONE:
        if pattern.search(simple_text):
            raise AssertionError(f"forbidden Level 1 token matched {pattern.pattern!r}")


def assert_disclosure_keyboard(page, summary_text: str, details_selector: str) -> None:
    details = page.locator(details_selector)
    summary = details.locator("summary").nth(0)
    summary.focus()
    page.keyboard.press("Enter")
    page.wait_for_function(
        "(selector) => document.querySelector(selector)?.open === true",
        arg=details_selector,
    )
    if summary_text not in details.inner_text():
        raise AssertionError(f"details did not expose {summary_text!r}")


def verify_links(page) -> None:
    required = (
        ("View the project", "https://github.com/armpitpete/sample-hold-lab"),
        ("Contact the project owner", "https://github.com/armpitpete"),
        ("Open original source", "https://raw.githubusercontent.com/armpitpete/sample-hold-lab/"),
    )
    for label, prefix in required:
        link = (
            page.locator("details.evidence-source-detail[open] a.source-action").first
            if label == "Open original source"
            else page.get_by_role("link", name=label).first
        )
        href = link.get_attribute("href") or ""
        target = link.get_attribute("target") or ""
        rel = link.get_attribute("rel") or ""
        if not href.startswith(prefix):
            raise AssertionError(f"{label!r} href did not start with {prefix!r}: {href!r}")
        if target != "_blank":
            raise AssertionError(f"{label!r} does not open outside the result: target={target!r}")
        if "noopener" not in rel or "noreferrer" not in rel:
            raise AssertionError(f"{label!r} missing safe rel: {rel!r}")


def install_local_api_pipeline(context, *, commit: str) -> None:
    cache: dict[str, dict[str, object]] = {}
    executor = ThreadPoolExecutor(max_workers=1)

    def read(repository: str) -> dict[str, object]:
        config = APIConfig(
            github_token=os.getenv("PROJECT_READER_GITHUB_TOKEN")
            or os.getenv("GITHUB_TOKEN"),
            deployed_commit=commit,
        )
        return {"ok": True, **default_pipeline(repository, config)}

    def handler(route) -> None:
        try:
            payload = json.loads(route.request.post_data or "{}")
            repository = payload.get("repository")
            if not isinstance(repository, str):
                raise ValueError("repository must be a string")
            if repository not in cache:
                cache[repository] = executor.submit(read, repository).result()
            route.fulfill(
                status=200,
                headers={
                    "content-type": "application/json; charset=utf-8",
                    "access-control-allow-origin": "*",
                },
                body=json.dumps(cache[repository], ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            )
        except Exception as error:
            route.fulfill(
                status=422,
                headers={
                    "content-type": "application/json; charset=utf-8",
                    "access-control-allow-origin": "*",
                },
                body=json.dumps(
                    {"ok": False, "code": "local_pipeline_failed", "detail": str(error)},
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            )

    context.route(READ_ENDPOINT, handler)


def run_viewport(page, *, url: str, repository: str, width: int, height: int, screenshot: Path) -> dict[str, object]:
    page.set_viewport_size({"width": width, "height": height})
    page.goto(url, wait_until="domcontentloaded")
    page.get_by_label("Public GitHub repository").fill(repository)
    page.get_by_role("button", name="Read this project").click()
    try:
        page.get_by_text("Reading complete.").wait_for(timeout=180_000)
    except Exception as error:
        status = page.locator("#status-line").inner_text(timeout=1_000)
        raise AssertionError(f"timed out waiting for reading completion; status line: {status!r}") from error

    if page.locator("iframe").count() != 0:
        raise AssertionError("result iframe still exists")
    page.locator("#reader-result[data-visible='true'] article.project-reader-result").wait_for()

    assert_level_one(page)
    assert_no_internal_result_scroll(page)
    assert_no_horizontal_overflow(page)

    assert_disclosure_keyboard(page, "Project status and reasons", "details.status-detail")
    status_text = page.locator("details.status-detail").inner_text()
    if "Will the current plan be finished?" not in status_text:
        raise AssertionError("likelihood question was not available in Level 2")

    assert_disclosure_keyboard(page, "Technical sources and repository details", "details.technical-sources")
    technical_text = page.locator("details.technical-sources").inner_text()
    for phrase in (
        "Original sources and readable previews",
        "README.md",
        "package.json",
        "Detected languages and amounts",
        "Source commit:",
        "Reading checked:",
    ):
        if phrase not in technical_text:
            raise AssertionError(f"missing Level 3 phrase: {phrase}")
    if "Readable preview rendered safely by Project Reader." in technical_text:
        raise AssertionError("repeated readable-preview label is still present")

    page.locator("details.evidence-source-detail").first.locator("summary").click()
    page.get_by_text("Open original source").first.wait_for()
    verify_links(page)
    assert_no_internal_result_scroll(page)
    assert_no_horizontal_overflow(page)
    page.screenshot(path=str(screenshot), full_page=True)

    metrics = page.evaluate(
        """
        () => ({
          pageScrollHeight: document.documentElement.scrollHeight,
          pageClientHeight: document.documentElement.clientHeight,
          resultHeight: document.querySelector("#reader-result")?.getBoundingClientRect().height || 0,
          resultOverflowY: getComputedStyle(document.querySelector("#reader-result")).overflowY,
          documentScrollWidth: document.documentElement.scrollWidth,
          documentClientWidth: document.documentElement.clientWidth,
          detailCount: document.querySelectorAll("article.project-reader-result > section.disclosures > details").length,
        })
        """
    )
    return {
        "viewport": f"{width}x{height}",
        "screenshot": str(screenshot),
        "metrics": metrics,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify issue #22 visual hierarchy against Project Reader.")
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY)
    parser.add_argument("--commit", default=current_commit())
    parser.add_argument("--output", type=Path, default=Path(tempfile.gettempdir()) / "project-reader-issue22-visual")
    parser.add_argument("--site-url", help="Use an already deployed Project Reader URL instead of a local Pages build.")
    parser.add_argument(
        "--disable-web-security",
        action="store_true",
        help="Allow a local pre-merge Pages build to call the public API despite CORS.",
    )
    parser.add_argument(
        "--local-api-pipeline",
        action="store_true",
        help="Route the frontend read request to the local Python Project Reader pipeline.",
    )
    args = parser.parse_args()

    from playwright.sync_api import sync_playwright

    output = args.output
    site_dir = output / "site"
    screenshots = output / "screenshots"
    screenshots.mkdir(parents=True, exist_ok=True)
    if not args.site_url:
        build_pages_site(commit=args.commit, output=site_dir)

    site_context = local_site(site_dir) if not args.site_url else None
    if site_context is None:
        url_manager = None
        url = args.site_url
    else:
        url_manager = site_context
        url = url_manager.__enter__()

    results: list[dict[str, object]] = []
    try:
        with sync_playwright() as playwright:
            launch_args = ["--disable-web-security"] if args.disable_web_security else []
            browser = playwright.chromium.launch(args=launch_args)
            try:
                context = browser.new_context(ignore_https_errors=False)
                if args.local_api_pipeline:
                    install_local_api_pipeline(context, commit=args.commit)
                page = context.new_page()
                results.append(
                    run_viewport(
                        page,
                        url=url,
                        repository=args.repository,
                        width=1280,
                        height=900,
                        screenshot=screenshots / "sample-hold-lab-desktop.png",
                    )
                )
                results.append(
                    run_viewport(
                        page,
                        url=url,
                        repository=args.repository,
                        width=390,
                        height=900,
                        screenshot=screenshots / "sample-hold-lab-narrow.png",
                    )
                )
            finally:
                browser.close()
    finally:
        if url_manager is not None:
            url_manager.__exit__(None, None, None)

    summary = {
        "schema_version": 1,
        "issue": 22,
        "repository": args.repository,
        "commit": args.commit,
        "site": str(url),
        "api_mode": "local-python-pipeline" if args.local_api_pipeline else "deployed-api",
        "results": results,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
