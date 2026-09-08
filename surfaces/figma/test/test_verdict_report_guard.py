"""Client-side verdict-report guard (surfaces/figma/src/ui.ts::isVerdictReportPaste /
updateRun). A pasted verdict report must never reach a job submission -- found live: it did,
because the hosted engine's own guard (synth/engine.py::VERDICT_REPORT_HEADING) was written
this session but never deployed, so the job ran against the old parser, structured the report
deterministically, and failed confidence_threshold on every claim at real cost and wall time
(docs/part3-notes.md, 2026-09-08). This is the client-side check that refuses before the run
button is even clickable, independent of what's deployed on the hosted engine.

Requires the playwright Python package with Chromium installed; serves the repository root
over HTTP so dist/ui.html's relative fetches (the sample transcript used here) resolve.
"""
from __future__ import annotations

import http.server
import socketserver
import threading
from pathlib import Path

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
UI = "/surfaces/figma/dist/ui.html"

# The exact shape surfaces/figma/src/ui.ts::verdictMarkdown prints (the header text is the marker
# both this guard and synth/engine.py::VERDICT_REPORT_HEADING key off of).
VERDICT_MD = (
    "# Motif critique\n\n"
    "This is a Motif critique, not a synthesis. It has no confidence values, so it cannot be "
    "checked again -- paste the document it critiques instead.\n\n"
    "Question: What are the barriers?\nRun: 20260908-test\n\n"
    "## I-01 — Some claim\n\n**Claim:** Something was claimed.\n"
)

# A legitimate synthesis report (synth/report.py's shape) -- must NOT trip the guard.
SYNTHESIS_MD = (
    "# Synthesis — C run 20260904\n\n"
    "## I-01 — Some finding\n\n**Claim:** People find this hard.\n**Evidence:** alice:0002\n"
)


@pytest.fixture(scope="module")
def server():
    """Binds port 0 -- an OS-assigned free port -- rather than a fixed one: a fixed port left
    two consecutive suite runs racing the previous run's socket through TCP TIME_WAIT, flaky
    even with server_close() (which does release it, just not always fast enough for a second
    process to rebind milliseconds later)."""
    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=str(ROOT), **k)  # noqa: E731
    srv = socketserver.TCPServer(("127.0.0.1", 0), handler)
    srv.allow_reuse_address = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv
    srv.shutdown()
    srv.server_close()


def _setup_critique_mode(page, base: str, document_text: str) -> None:
    page.goto(base + "?harness=1")
    page.evaluate("localStorage.setItem('anthropic_key', 'sk-ant-harness-0000000000000000')")
    # A second navigation, key already in localStorage, so the setup screen (not the key screen)
    # is what "?files=" lands on -- same two-step pattern harness_scan_restyle.py uses.
    page.goto(base + "?harness=1&files=/data/raw/Dataset-2/Michelle.docx")
    page.wait_for_selector("#screen-setup:not([hidden])")
    page.wait_for_function("document.querySelectorAll('#file-list li').length === 1")
    page.click("#mode-critique")
    page.fill("#document", document_text)
    page.wait_for_timeout(150)


def test_verdict_report_paste_is_refused_before_submission(server) -> None:
    base = f"http://127.0.0.1:{server.server_address[1]}{UI}"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_context(viewport={"width": 440, "height": 700}).new_page()
        submitted: list[str] = []
        page.route("https://motif-hosted.fly.dev/v1/jobs",
                   lambda route: (submitted.append(route.request.url), route.abort()))
        _setup_critique_mode(page, base, VERDICT_MD)

        assert page.is_disabled("#run-btn"), "the run button must be disabled for a pasted verdict report"
        assert not page.eval_on_selector("#run-why", "el => el.hidden")
        assert "Motif critique report" in page.inner_text("#run-why")

        # A genuinely disabled button refuses a real click; this is the actual proof no submission
        # can happen through normal interaction, not just that the disabled attribute is present.
        with pytest.raises(PlaywrightTimeoutError):
            page.click("#run-btn", timeout=1000)

        assert submitted == [], f"a job was submitted for a pasted verdict report: {submitted}"
        browser.close()


def test_legitimate_synthesis_paste_is_not_refused(server) -> None:
    """Regression check for the guard itself: it must not fire on real, checkable input."""
    base = f"http://127.0.0.1:{server.server_address[1]}{UI}"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_context(viewport={"width": 440, "height": 700}).new_page()
        _setup_critique_mode(page, base, SYNTHESIS_MD)

        assert not page.is_disabled("#run-btn")
        assert page.eval_on_selector("#run-why", "el => el.hidden")
        browser.close()
