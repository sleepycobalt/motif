// Renderer test with a fake Figma API: every sticky placed, rows and sizes computed, connectors wired,
// run card above the grid, both editors. Bundles src/board.ts the same way the plugin does.
import { build } from "esbuild";
import { readFileSync } from "node:fs";

await build({ entryPoints: ["src/board.ts"], bundle: true, format: "esm", outfile: "test/.board.mjs", logLevel: "silent" });
const B = await import("./.board.mjs");

function fakeFigma(editorType, pageChildren = []) {
  let n = 0;
  const id = () => `${++n}:${n}`;
  const node = (type, extra = {}) => ({ id: id(), type, x: 0, y: 0, width: 0, height: 0, children: [], removed: false,
    appendChild(c) { this.children.push(c); c.parent = this; },
    resizeWithoutConstraints(w, h) { this.width = w; this.height = h; },
    resize(w, h) { this.width = w; this.height = h; }, remove() { this.removed = true; }, ...extra });
  const textHeight = (s, wide) => 24 + 18 * Math.ceil((s || "").length / (wide ? 60 : 28)) + 18 * ((s || "").split("\n").length - 1);
  const figma = {
    editorType,
    currentPage: { children: pageChildren },
    viewport: { scrollAndZoomIntoView() {} },
    loadFontAsync: async () => {},
    getNodeById: () => null,
    createSection: () => node("SECTION"),
    createSticky: () => { const s = node("STICKY", { text: { fontName: { family: "Inter", style: "Medium" }, _c: "" }, _wide: false, fills: [], authorVisible: true });
      Object.defineProperty(s.text, "characters", { set(v) { this._c = v; s.height = textHeight(v, s._wide); }, get() { return this._c; } });
      Object.defineProperty(s, "isWideWidth", { set(v) { s._wide = v; s.width = v ? 480 : 240; s.height = textHeight(s.text._c, v); }, get() { return s._wide; } });
      s.width = 240; return s; },
    createConnector: () => node("CONNECTOR", { text: {}, strokes: [] }),
    createFrame: () => { const f = node("FRAME", { fills: [] }); f.resize = (w, h) => { f.width = w; f.height = h; }; return f; },
    createText: () => { const t = node("TEXT", { fontName: null, fontSize: 12 });
      Object.defineProperty(t, "characters", { set(v) { t._c = v; const p = t.parent; if (p) p.height = textHeight(v, p.width > 300) + 32; }, get() { return t._c; } }); return t; },
  };
  return figma;
}

const fixtures = ["layout-synthesis.json", "layout-verdict.json"].map((f) => JSON.parse(readFileSync(`test/fixtures/${f}`, "utf8")));
let failures = 0;
const check = (cond, msg) => { if (!cond) { failures++; console.log("FAIL:", msg); } };

for (const lay of fixtures) {
  for (const editor of ["figjam", "figma"]) {
    globalThis.figma = fakeFigma(editor, [{ x: 0, y: 0, width: 1000, height: 500 }]);
    const res = await B.renderBoard(lay);
    const expectStickies = lay.sections.reduce((n, s) => n + s.stickies.length, 0) + 1;
    const expectConn = editor === "figjam" ? lay.sections.reduce((n, s) => n + s.connectors.length, 0) : 0;
    check(res.counts.sections === lay.n_sections, `${lay.kind}/${editor}: sections ${res.counts.sections} != ${lay.n_sections}`);
    check(res.counts.stickies === expectStickies, `${lay.kind}/${editor}: stickies ${res.counts.stickies} != ${expectStickies}`);
    check(res.counts.connectors === expectConn, `${lay.kind}/${editor}: connectors ${res.counts.connectors} != ${expectConn}`);
    check(res.cardId !== null, `${lay.kind}/${editor}: no run card`);
    check(res.bounds.x >= 1400, `${lay.kind}/${editor}: origin not clear of existing content (x=${res.bounds.x})`);
    check(res.editor === editor, "editor echo");
    console.log(`${lay.kind}/${editor}: ${res.counts.sections} sections, ${res.counts.stickies} stickies, ${res.counts.connectors} connectors, bounds ${Math.round(res.bounds.width)}x${Math.round(res.bounds.height)} at (${res.bounds.x}, ${res.bounds.y})`);
  }
}
// Failure semantics: a section whose stickies collapse onto one key (so one is missing) must throw, not return.
globalThis.figma = fakeFigma("figjam");
let threw = false;
try {
  const sec = fixtures[0].sections[0];
  await B.renderBoard({ ...fixtures[0], sections: [{ ...sec, stickies: [...sec.stickies, { ...sec.stickies[0] }] }] });
} catch (e) { threw = /stickies created/.test(e.message); if (!threw) console.log("unexpected:", e.message); }
check(threw, "duplicate sticky key did not throw");
let empty = false;
try { await B.renderBoard({ ...fixtures[0], sections: [] }); } catch (e) { empty = /no sections/.test(e.message); }
check(empty, "empty layout did not throw");
const card = B.cardText(fixtures[0]);
check(card.startsWith(`MOTIF SYNTHESIS · run ${fixtures[0].card.run_id}`) && card.includes("15 insights, 3 contested: I-02, I-05, I-08") && card.includes("2 transcripts (david, michelle), 11,482 words"), "card text: " + card.split("\n").slice(0, 4).join(" | "));
console.log(failures ? `${failures} FAILURE(S)` : "RENDER OK");
process.exitCode = failures ? 1 : 0;
