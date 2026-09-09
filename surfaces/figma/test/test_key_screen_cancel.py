"""Key-screen cancel (surfaces/figma/src/ui.ts, key-change/key-cancel handlers, code.ts's
clear-key handler unchanged). Root cause of the bug this guards, found live by the user and not
by any test: "change" navigated to the key screen by first posting clear-key, deleting the stored
key from figma.clientStorage on entry -- before the user had entered or accepted anything new --
and the key screen had no way back. Abandoning the screen (there was nothing to abandon to)
stranded the user with no key and no route to the setup screen. Every earlier test entered the
key screen from the empty state (no key ever stored), so this path was never exercised.

Fix: key-change no longer sends clear-key; only a successful save-key (which overwrites the
stored value directly) ever changes storage. The key screen gets a Cancel button, shown only
when a key is already on file, that returns to setup with the stored key untouched.

Requires the playwright Python package with Chromium installed; serves the repository root over
HTTP so dist/ui.html resolves.
"""
from __future__ import annotations

import http.server
import socketserver
import threading
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
UI = "/surfaces/figma/dist/ui.html"
FAKE_KEY = "sk-ant-harness-0000000000000000"


@pytest.fixture(scope="module")
def server():
    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=str(ROOT), **k)  # noqa: E731
    srv = socketserver.TCPServer(("127.0.0.1", 0), handler)
    srv.allow_reuse_address = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv
    srv.shutdown()
    srv.server_close()


def test_cancelling_the_key_screen_leaves_the_stored_key_unchanged(server) -> None:
    base = f"http://127.0.0.1:{server.server_address[1]}{UI}"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_context(viewport={"width": 440, "height": 700}).new_page()
        page.goto(base + "?harness=1")
        page.evaluate(f"localStorage.setItem('anthropic_key', '{FAKE_KEY}')")
        # Second navigation, key already in localStorage: init lands on the setup screen, not
        # the key screen, same two-step pattern the verdict-report-guard test uses.
        page.goto(base + "?harness=1")
        page.wait_for_selector("#screen-setup:not([hidden])")

        page.click("#key-change")
        page.wait_for_selector("#screen-key:not([hidden])")
        assert not page.eval_on_selector("#key-cancel", "el => el.hidden"), \
            "cancel must be visible when a key is already stored"

        page.click("#key-cancel")
        page.wait_for_selector("#screen-setup:not([hidden])")

        assert page.evaluate("localStorage.getItem('anthropic_key')") == FAKE_KEY, \
            "the stored key must survive entering and cancelling the key screen"
        browser.close()


def test_key_screen_has_no_cancel_on_first_run(server) -> None:
    """Regression check: with no key ever stored, the key screen is the legitimate first screen
    and offers no cancel (there is nowhere to go back to)."""
    base = f"http://127.0.0.1:{server.server_address[1]}{UI}"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_context(viewport={"width": 440, "height": 700}).new_page()
        page.goto(base + "?harness=1")
        page.wait_for_selector("#screen-key:not([hidden])")
        assert page.eval_on_selector("#key-cancel", "el => el.hidden")
        browser.close()
