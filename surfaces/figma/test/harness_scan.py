"""Width scan of the plugin UI at 440, 375, and 320 px, outside Figma.

Serves the repository root, opens dist/ui.html in a real Chromium viewport at each width
(the same three the harness.html frames use), drives the screen under test, and checks:
no page-level horizontal scroll, document scrollWidth within clientWidth, and no element
whose box crosses the right edge of the viewport. Writes one composite JPEG per screen.

  python3 surfaces/figma/test/harness_scan.py <out_dir>

Requires the playwright Python package with Chromium installed.
"""
from __future__ import annotations

import http.server
import json
import socketserver
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
PORT = 8791
WIDTHS = [(440, 660), (375, 667), (320, 568)]
UI = "/surfaces/figma/dist/ui.html"
FIX = "/surfaces/figma/test/fixtures/verdict-result.json"
LAY = "/surfaces/figma/test/fixtures/layout-verdict.json"

SCAN_JS = """
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


def serve() -> socketserver.TCPServer:
    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=str(ROOT), **k)  # noqa: E731
    srv = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    srv.allow_reuse_address = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def screens():
    """name -> (url, setup(page))."""
    base = f"http://127.0.0.1:{PORT}{UI}"
    txt = ("# Synthesis — C run 20260905-221749-C-hosted\n\nTranscripts: david, michelle (11,482 words)\n"
           "Iterations: 3  Stop: max_iterations\n\n## I-01 — Anonymity and consent scope are named as concrete barriers\n")

    def key(page):
        page.evaluate("localStorage.setItem('anthropic_key', 'sk-ant-harness-0000000000000000')")
        page.evaluate("localStorage.removeItem('last_result'); localStorage.removeItem('last_job')")

    def critique_no_files(page):
        key(page); page.reload(); page.wait_for_selector("#screen-setup:not([hidden])")
        page.click("#mode-critique")
        page.fill("#document", txt)
        page.wait_for_selector("#run-why:not([hidden])")

    def critique_files_no_text(page):
        key(page)
        page.goto(base + "?harness=1&mode=critique&files=/data/raw/Dataset-2/Michelle.docx,/data/raw/Dataset-2/David.docx")
        page.wait_for_selector("#screen-setup:not([hidden])")
        page.wait_for_function("document.querySelectorAll('#file-list li').length === 2")
        page.wait_for_selector("#run-why:not([hidden])")

    def synth_no_files(page):
        key(page); page.reload(); page.wait_for_selector("#screen-setup:not([hidden])")
        page.fill("#question", "What frustrates users about onboarding?")
        page.wait_for_selector("#run-why:not([hidden])")

    def synthesis(page):
        """The stored-result fixture (a synthesis result with five tiles) opened from client storage."""
        key(page)
        page.evaluate("async () => { const s = await (await fetch('/surfaces/figma/test/fixtures/stored-result.json')).json(); localStorage.setItem('last_result', JSON.stringify(s)); }")
        page.reload()
        page.wait_for_function("document.querySelectorAll('#tiles .tile').length === 5")

    def verdict(page):
        key(page)
        page.goto(base + f"?harness=1&demo={FIX}&layout={LAY}&n=2")
        page.wait_for_selector("#screen-result:not([hidden])")
        page.wait_for_function("document.querySelectorAll('#tiles .tile').length === 6")

    return {
        "critique-form-no-transcripts-reason": (base + "?harness=1", critique_no_files),
        "critique-form-no-text-reason": (base + "?harness=1", critique_files_no_text),
        "synth-form-no-transcripts-reason": (base + "?harness=1", synth_no_files),
        "verdict-cost-time-tiles": (base + "?harness=1", verdict),
        "synthesis-result-tiles": (base + "?harness=1", synthesis),
    }


def main(out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    srv = serve()
    report = {}
    issues = 0
    try:
        from PIL import Image  # composite
    except ImportError:
        Image = None
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, (url, setup) in screens().items():
            shots = []
            report[name] = {}
            for w, h in WIDTHS:
                ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=2)
                page = ctx.new_page()
                page.goto(url)
                page.wait_for_selector("#app")
                setup(page)
                # Frame the element under test for the exhibit (the scan itself covers the whole page).
                page.evaluate("() => { const e = document.getElementById('run-why'); if (e && !e.hidden) e.scrollIntoView({block: 'end'}); }")
                page.wait_for_timeout(300)
                scan = page.evaluate(SCAN_JS)
                why = page.evaluate("() => { const e = document.getElementById('run-why'); return e && !e.hidden ? e.textContent : null; }")
                tiles = page.evaluate("() => [...document.querySelectorAll('#tiles .tile')].map(t => t.textContent.trim().replace(/\\s+/g,' '))")
                # tiles per row, by top edge; a row holding a single tile while others hold more is an orphan
                rows = page.evaluate("() => { const ys = {}; for (const t of document.querySelectorAll('#tiles .tile')) { const y = Math.round(t.getBoundingClientRect().top); ys[y] = (ys[y] || 0) + 1; } return Object.keys(ys).sort((a, b) => a - b).map(k => ys[k]); }")
                orphan = len(rows) > 1 and min(rows) == 1
                if orphan:
                    ok = False
                ok = scan["scrollWidth"] <= scan["clientWidth"] and scan["pageScrollX"] == 0 and not scan["over"]
                issues += 0 if ok else 1
                report[name][str(w)] = {"ok": ok, **scan, "run_why": why, "tiles": tiles, "tile_rows": rows, "orphan": orphan}
                shot = out_dir / f"_{name}-{w}.png"
                page.screenshot(path=str(shot), full_page=False)
                shots.append(shot)
                ctx.close()
            if Image is not None:
                ims = [Image.open(s) for s in shots]
                gap = 24
                W = sum(i.width for i in ims) + gap * (len(ims) - 1)
                H = max(i.height for i in ims)
                comp = Image.new("RGB", (W, H), (221, 221, 221))
                x = 0
                for im in ims:
                    comp.paste(im, (x, 0)); x += im.width + gap
                comp.save(out_dir / f"ui-{name}-440-375-320.jpg", quality=88)
                for s in shots: s.unlink()
        browser.close()
    srv.shutdown()
    (out_dir / "harness-scan.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    for name, r in report.items():
        line = "  ".join(f"{w}: {'ok' if v['ok'] else 'ISSUE'}" for w, v in r.items())
        print(f"{name:40s} {line}")
        for w, v in r.items():
            if v["run_why"]: print(f"    {w}: run-why = {v['run_why']}")
            if v["tiles"]: print(f"    {w}: tiles = {v['tiles']}  rows = {v['tile_rows']}{'  ORPHAN' if v['orphan'] else ''}")
            if v["over"]: print(f"    {w}: overflow {v['over']}")
    print(f"{issues} layout issue(s)")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else "docs/exhibits/stage4-polish")))
