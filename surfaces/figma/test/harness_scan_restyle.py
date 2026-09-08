"""Stage-4 restyle QA gate (docs/specs/plugin-restyle.md §8): the same width scan as
harness_scan.py, plus a theme dimension and a second assertion, over the eleven §8.1
screens (ten scenarios below: "collapsed" and "expanded" are two states of one screen).

Opens dist/ui.html directly, outside Figma and outside test/harness.html (theme is set
"by hand" per §8.1's second option, toggling the .figma-dark class with page.evaluate,
since harness.html has no Figma parent to set it for real and is not touched here).

Two checks, not one:
  1. The original overflow scan: no page-level horizontal scroll, document scrollWidth
     within clientWidth, no element box crossing the viewport's right edge.
  2. A minimum-average-line-length assertion. Found necessary after two restyle bugs
     that (1) passed check 1 clean and (2) were only visible in a screenshot: the
     .insight summary grid at 320px and the .tiers radio at 440px both squeezed a label
     down to a sliver and word- or letter-wrapped it, without any box crossing an edge
     -- wrapping *inward* leaves no overflow to catch. For every leaf text element with
     at least MIN_TEXT_LEN characters, this measures its rendered line count via
     Range.getClientRects() (one rect per visual line) and flags it if the average
     characters-per-line falls under MIN_AVG_LINE_LEN while its container had room to
     spare -- the signature of a flex/grid track collapsing instead of the text
     legitimately wrapping at a narrow width.

  python3 surfaces/figma/test/harness_scan_restyle.py [out_dir]

Requires the playwright Python package with Chromium installed, and Pillow.
"""
from __future__ import annotations

import http.server
import json
import socketserver
import sys
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
PORT = 8850
WIDTHS = [(440, 900), (375, 900), (320, 900)]
UI = "/surfaces/figma/dist/ui.html"
VERDICT_FIX = "/surfaces/figma/test/fixtures/verdict-result.json"
VERDICT_LAY = "/surfaces/figma/test/fixtures/layout-verdict.json"

MIN_TEXT_LEN = 12
MIN_AVG_LINE_LEN = 8

OVERFLOW_SCAN_JS = """
() => {
  const de = document.documentElement;
  const vw = de.clientWidth;
  const over = [];
  for (const el of document.querySelectorAll('body *')) {
    if (el.hidden || el.closest('[hidden]')) continue;
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) continue;
    if (r.right > vw + 0.5) over.push({tag: el.tagName, id: el.id, cls: el.className, right: Math.round(r.right)});
  }
  return {vw, scrollWidth: de.scrollWidth, clientWidth: de.clientWidth,
          pageScrollX: window.scrollX, bodyScrollWidth: document.body.scrollWidth, over};
}
"""

LINE_COLLAPSE_SCAN_JS = f"""
() => {{
  const MIN_TEXT_LEN = {MIN_TEXT_LEN};
  const MIN_AVG_LINE_LEN = {MIN_AVG_LINE_LEN};
  const collapsed = [];
  for (const el of document.querySelectorAll('body *')) {{
    if (el.hidden || el.closest('[hidden]')) continue;
    if (el.children.length) continue;  // leaf text nodes only -- a wrapping child reports itself
    const text = el.textContent.trim();
    if (text.length < MIN_TEXT_LEN) continue;
    const r = document.createRange();
    r.selectNodeContents(el);
    const rects = [...r.getClientRects()].filter(x => x.width > 0.5 && x.height > 0.5);
    // A truncated text-overflow:ellipsis node reports two rects at the SAME top (the visible
    // fragment and the clipped remainder) -- that is one line, not two. Count distinct tops.
    const tops = new Set(rects.map(x => Math.round(x.top)));
    const lines = tops.size;
    if (lines <= 1) continue;
    const avg = text.length / lines;
    if (avg < MIN_AVG_LINE_LEN) {{
      collapsed.push({{tag: el.tagName, id: el.id, cls: el.className, text: text.slice(0, 48), lines, avg: Math.round(avg * 10) / 10}});
    }}
  }}
  return collapsed;
}}
"""


def serve() -> socketserver.TCPServer:
    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=str(ROOT), **k)  # noqa: E731
    srv = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    srv.allow_reuse_address = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def mock_job(page, job_id: str) -> None:
    created = time.time()
    page.route(f"https://motif-hosted.fly.dev/v1/jobs/{job_id}", lambda route: route.fulfill(
        status=200, content_type="application/json",
        body=json.dumps({"job_id": job_id, "kind": "synthesize", "state": "running", "created": created,
                          "finished": None, "run_id": None, "words": None, "n_events": 0, "error": None})))
    page.route(f"https://motif-hosted.fly.dev/v1/jobs/{job_id}/events**", lambda route: route.fulfill(
        status=200, content_type="text/event-stream",
        body="id: 1\nevent: message\ndata: {\"message\": \"Reading transcripts\\u2026\"}\n\n"
             "id: 2\nevent: message\ndata: {\"message\": \"Splitting into turns\\u2026\"}\n\n"
             "id: 3\nevent: message\ndata: {\"message\": \"Drafting insights\\u2026\"}\n\n"))


def screens():
    base = f"http://127.0.0.1:{PORT}{UI}"

    def key(page):
        page.evaluate("localStorage.clear()")

    def with_key(page):
        page.evaluate("localStorage.setItem('anthropic_key', 'sk-ant-harness-0000000000000000')")
        page.evaluate("localStorage.removeItem('last_result'); localStorage.removeItem('last_job')")

    def setup_two_transcripts(page):
        with_key(page)
        page.goto(base + "?harness=1&files=/data/raw/Dataset-2/Michelle.docx,/data/raw/Dataset-2/David.docx")
        page.wait_for_selector("#screen-setup:not([hidden])")
        page.wait_for_function("document.querySelectorAll('#file-list li').length === 2")

    def setup_critique_report_pasted(page):
        with_key(page); page.goto(base + "?harness=1"); page.wait_for_selector("#screen-setup:not([hidden])")
        page.click("#mode-critique")
        page.fill("#document", "# Synthesis report\n\nI-01: David treats respecting participant anonymity as "
                                "his primary barrier (david:0022, david:0010).\n\nI-02: Interpretive multiplicity "
                                "undermines quantitative-style claims (michelle:0031).\n")
        page.wait_for_timeout(100)

    def setup_run_disabled_why(page):
        with_key(page); page.goto(base + "?harness=1"); page.wait_for_selector("#screen-setup:not([hidden])")
        page.fill("#question", "What frustrates users about onboarding?")
        page.wait_for_selector("#run-why:not([hidden])")

    def running_ingest_log(page):
        with_key(page)
        page.evaluate("() => localStorage.setItem('last_job', JSON.stringify({jobId: 'qa-job', question: 'What frustrates users about onboarding?', kind: 'synthesize'}))")
        page.goto(base + "?harness=1")
        page.wait_for_selector("#resume-card:not([hidden])")
        mock_job(page, "qa-job")
        page.click("#resume-btn")
        page.wait_for_selector("#screen-running:not([hidden])")
        page.wait_for_timeout(400)

    def result_synthesis_collapsed(page):
        with_key(page)
        page.evaluate("async () => { const s = await (await fetch('/surfaces/figma/test/fixtures/stored-result.json')).json(); localStorage.setItem('last_result', JSON.stringify(s)); }")
        page.goto(base + "?harness=1")
        page.wait_for_function("document.querySelectorAll('#tiles .tile').length === 5")

    def result_synthesis_expanded(page):
        result_synthesis_collapsed(page)
        page.click("#insights li:nth-of-type(1) summary")
        page.click("#insights li:nth-of-type(3) summary")  # a contested one (double badge)
        page.wait_for_timeout(150)

    def result_verdict_objections_open(page):
        with_key(page)
        page.goto(base + f"?harness=1&demo={VERDICT_FIX}&layout={VERDICT_LAY}&n=2")
        page.wait_for_selector("#screen-result:not([hidden])")
        page.wait_for_function("document.querySelectorAll('#tiles .tile').length === 6")

    def copy_fallback_revealed(page):
        with_key(page)
        page.add_init_script("navigator.clipboard.writeText = () => Promise.reject(new Error('denied')); document.execCommand = () => false;")
        page.evaluate("async () => { const s = await (await fetch('/surfaces/figma/test/fixtures/stored-result.json')).json(); localStorage.setItem('last_result', JSON.stringify(s)); }")
        page.goto(base + "?harness=1")
        page.wait_for_function("document.querySelectorAll('#tiles .tile').length === 5")
        page.click("#copy-report")
        page.wait_for_selector("#clip:not([hidden])")

    def error_with_hint(page):
        with_key(page)
        page.route("https://motif-hosted.fly.dev/v1/jobs", lambda route: route.fulfill(
            status=401, content_type="application/json",
            body=json.dumps({"detail": "authentication_error: API key is invalid"})))
        page.goto(base + "?harness=1")
        page.wait_for_selector("#screen-setup:not([hidden])")
        page.fill("#question", "What frustrates users about onboarding?")
        page.set_input_files("#file-input", {"name": "t.txt", "mimeType": "text/plain",
                                              "buffer": b"Michelle: hello there, this is a turn of dialogue."})
        page.wait_for_timeout(150)
        page.click("#run-btn")
        page.wait_for_selector("#screen-error:not([hidden])")

    return {
        "key": (base + "?harness=1", key),
        "setup-two-transcripts": (base + "?harness=1", setup_two_transcripts),
        "setup-critique-report-pasted": (base + "?harness=1", setup_critique_report_pasted),
        "setup-run-disabled-why": (base + "?harness=1", setup_run_disabled_why),
        "running-ingest-log": (base + "?harness=1", running_ingest_log),
        "result-synthesis-collapsed": (base + "?harness=1", result_synthesis_collapsed),
        "result-synthesis-expanded": (base + "?harness=1", result_synthesis_expanded),
        "result-verdict-objections-open": (base + "?harness=1", result_verdict_objections_open),
        "copy-fallback-revealed": (base + "?harness=1", copy_fallback_revealed),
        "error-with-hint": (base + "?harness=1", error_with_hint),
    }


def main(out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    srv = serve()
    report = {}
    issues = 0
    from PIL import Image
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, (url, setup) in screens().items():
            report[name] = {}
            for theme in ("light", "dark"):
                shots = []
                for w, h in WIDTHS:
                    ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=1)
                    page = ctx.new_page()
                    page.goto(url)
                    page.wait_for_selector("#app")
                    setup(page)
                    if theme == "dark":
                        page.evaluate("document.documentElement.classList.add('figma-dark')")
                    page.wait_for_timeout(200)
                    scan = page.evaluate(OVERFLOW_SCAN_JS)
                    collapsed = page.evaluate(LINE_COLLAPSE_SCAN_JS)
                    ok = (scan["scrollWidth"] <= scan["clientWidth"] and scan["pageScrollX"] == 0
                          and not scan["over"] and not collapsed)
                    issues += 0 if ok else 1
                    report[name][f"{theme}-{w}"] = {"ok": ok, **scan, "collapsed_lines": collapsed}
                    panel_h = page.evaluate("document.getElementById('app').scrollHeight")
                    shot_h = min(max(panel_h + 4, 200), 1200)
                    ctx2 = browser.new_context(viewport={"width": w, "height": shot_h}, device_scale_factor=1)
                    page2 = ctx2.new_page()
                    page2.goto(url)
                    page2.wait_for_selector("#app")
                    setup(page2)
                    if theme == "dark":
                        page2.evaluate("document.documentElement.classList.add('figma-dark')")
                    page2.wait_for_timeout(200)
                    shot = out_dir / f"_{name}-{theme}-{w}.png"
                    page2.screenshot(path=str(shot), full_page=False)
                    shots.append(shot)
                    ctx.close(); ctx2.close()
                ims = [Image.open(s) for s in shots]
                gap = 24
                W = sum(i.width for i in ims) + gap * (len(ims) - 1)
                H = max(i.height for i in ims)
                bgcolor = (10, 10, 10) if theme == "dark" else (221, 221, 221)
                comp = Image.new("RGB", (W, H), bgcolor)
                x = 0
                for im in ims:
                    comp.paste(im, (x, 0)); x += im.width + gap
                comp.save(out_dir / f"ui-{name}-{theme}-440-375-320.jpg", quality=90)
                for s in shots: s.unlink()
        browser.close()
    srv.shutdown()
    (out_dir / "harness-scan-restyle.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    for name, r in report.items():
        line = "  ".join(f"{k}: {'ok' if v['ok'] else 'ISSUE'}" for k, v in r.items())
        print(f"{name:34s} {line}")
        for k, v in r.items():
            if v["over"]:
                print(f"    {k}: overflow {v['over']}")
            if v["collapsed_lines"]:
                print(f"    {k}: collapsed {v['collapsed_lines']}")
    print(f"{issues} layout issue(s) across {len(report)} screens x 2 themes x 3 widths")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else "docs/exhibits/stage4-restyle")))
