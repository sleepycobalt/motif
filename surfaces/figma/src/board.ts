/**
 * Board writer: a Motif layout (synth/board.py::layout or ::verdict_layout, fetched from the
 * hosted engine) onto the current page. Runs on the plugin main thread; the same function is
 * bundled standalone (test/board_script.mjs) and executed through Figma's MCP `use_figma`, so the
 * renderer that ships is the renderer that was tested on a real board.
 *
 * FigJam: one section per insight, stickies in two rows (claim + receipts; counters + opportunity +
 * contested), "contested by" connectors from the claim to each counter-evidence sticky, and a run
 * card above the grid. Mirrors the `use_figma` script Motif's MCP `motif_board` tool emits.
 * Figma Design: the same sections and positions; a sticky becomes an auto-layout frame with a
 * text child (no sticky node in Design), and connectors are dropped (no connector node in Design),
 * so counter frames keep their "COUNTER" caption as the link.
 *
 * Every sticky must exist when the function returns; a missing one is a thrown error, never a
 * partial success. Layout coordinates are absolute from the layout's origin; `origin` re-bases them.
 */

export interface Sticky { key: string; role: string; wide: boolean; color: string; text: string; row?: number }
export interface Connector { from: string; to: string; label: string }
export interface Section {
  insight_id: string; name: string; x: number; y: number; width: number; fill: string;
  stickies: Sticky[]; connectors: Connector[];
}
export interface Card {
  run_id?: string | null; question?: string | null; transcripts?: string[]; words?: number | null;
  condition?: string | null; iterations?: number | null; stop_reason?: string | null; cost?: number | null;
  wall_seconds?: number | null; started?: string | null;
  insights?: number; contested?: string[]; claims?: number; pass?: boolean; fails?: number; warns?: number;
  skipped_rules?: string[];
}
export interface Layout {
  title: string; kind?: "synthesis" | "verdict"; run_id?: string | null; columns: number;
  origin: [number, number]; n_sections: number; sections: Section[]; card?: Card;
}
export interface BoardResult {
  sectionIds: string[]; stickyIds: string[]; connectorIds: string[]; cardId: string | null; nodeIds: string[];
  counts: { sections: number; stickies: number; connectors: number };
  bounds: { x: number; y: number; width: number; height: number };
  editor: string;
}

export const PAD = 48;
export const SPACING = 40;
export const CONNECTOR = "F849C1";
export const CARD_GAP = 120;
export const CARD_COLORS = { ok: "B3EFBD", attention: "D3BDFF" };

const hex = (h: string): RGB => ({
  r: parseInt(h.slice(0, 2), 16) / 255, g: parseInt(h.slice(2, 4), 16) / 255, b: parseInt(h.slice(4, 6), 16) / 255,
});

/** 11482 -> "11,482" without relying on the sandbox's locale (Figma's main thread formats bare). */
export function thousands(n: number): string {
  return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function rowOf(s: Sticky): number {
  return s.row ?? (s.role === "claim" || s.role === "receipt" ? 1 : 2);
}

/** A free spot to the right of everything on the page, or the page origin when it is empty. */
export function chooseOrigin(page: PageNode): [number, number] {
  const kids = page.children;
  if (!kids.length) return [0, 0];
  let maxX = -Infinity, minY = Infinity;
  for (const n of kids) {
    if (!("x" in n) || !("width" in n)) continue;
    maxX = Math.max(maxX, n.x + n.width);
    minY = Math.min(minY, n.y);
  }
  if (!isFinite(maxX)) return [0, 0];
  return [Math.ceil((maxX + 400) / 100) * 100, Math.floor(minY / 100) * 100];
}

export function cardText(layout: Layout): string {
  const c = layout.card ?? {};
  const mins = c.wall_seconds != null ? `${(c.wall_seconds / 60).toFixed(1)} min` : "";
  const cost = c.cost != null ? `$${c.cost.toFixed(2)}` : "";
  const corpus = `${(c.transcripts ?? []).length} transcript${(c.transcripts ?? []).length === 1 ? "" : "s"}`
    + ((c.transcripts ?? []).length ? ` (${(c.transcripts ?? []).join(", ")})` : "")
    + (c.words != null ? `, ${thousands(c.words)} words` : "");
  const lines = [layout.kind === "verdict" ? `MOTIF CRITIQUE · run ${c.run_id ?? layout.run_id ?? "?"}` : `MOTIF SYNTHESIS · run ${c.run_id ?? layout.run_id ?? "?"}`];
  if (c.question) lines.push(`Question: ${c.question}`);
  lines.push(corpus);
  if (layout.kind === "verdict") {
    lines.push(`${c.pass ? "PASS" : "FAIL"}: ${c.fails ?? 0} fail(s), ${c.warns ?? 0} warning(s) on ${c.claims ?? layout.n_sections} claim(s)`);
    if (c.skipped_rules?.length) lines.push(`Not checked: ${c.skipped_rules.join(", ")}`);
  } else {
    lines.push(`${c.insights ?? layout.n_sections} insights` + (c.contested?.length ? `, ${c.contested.length} contested: ${c.contested.join(", ")}` : ", none contested"));
    lines.push([c.condition ? `Condition ${c.condition}` : "", c.iterations != null ? `${c.iterations} round(s)` : "",
      c.stop_reason ? `stop=${c.stop_reason}` : "", cost, mins].filter(Boolean).join(", "));
  }
  lines.push("Silence is never agreement: read contested items with the objection in view. Every receipt is verbatim; check any citation against the transcript.");
  if (c.started) lines.push(String(c.started).slice(0, 19).replace("T", " "));
  return lines.join("\n");
}

function cardColor(layout: Layout): string {
  const c = layout.card ?? {};
  const attention = layout.kind === "verdict" ? !c.pass : (c.contested?.length ?? 0) > 0;
  return attention ? CARD_COLORS.attention : CARD_COLORS.ok;
}

// ----------------------------------------------------------------- FigJam

async function renderFigJam(layout: Layout, dx: number, dy: number): Promise<BoardResult> {
  const probe = figma.createSticky();
  await figma.loadFontAsync(probe.text.fontName as FontName);
  probe.remove();
  const labelFont: FontName = { family: "Inter", style: "Medium" };
  await figma.loadFontAsync(labelFont);

  const sectionIds: string[] = [], stickyIds: string[] = [], connectorIds: string[] = [];
  const all: SceneNode[] = [];

  const makeSection = (name: string, fill: string, x: number, y: number): SectionNode => {
    const section = figma.createSection();
    section.name = name;
    section.fills = [{ type: "SOLID", color: hex(fill) }];
    section.x = x; section.y = y;
    return section;
  };
  const makeSticky = (section: SectionNode, st: Sticky): StickyNode => {
    const s = figma.createSticky();
    s.text.characters = st.text;
    s.isWideWidth = !!st.wide;
    s.fills = [{ type: "SOLID", color: hex(st.color) }];
    s.authorVisible = false;
    section.appendChild(s);
    return s;
  };

  for (const sec of layout.sections) {
    const section = makeSection(sec.name, sec.fill, sec.x + dx, sec.y + dy);
    const made: Record<string, StickyNode> = {};
    for (const st of sec.stickies) made[st.key] = makeSticky(section, st);
    if (Object.keys(made).length !== sec.stickies.length) {
      throw new Error(`section ${sec.insight_id}: ${Object.keys(made).length} of ${sec.stickies.length} stickies created`);
    }
    const rows = [1, 2].map((r) => sec.stickies.filter((s) => rowOf(s) === r).map((s) => made[s.key]));
    let y = PAD, maxRight = 0;
    for (const row of rows) {
      if (!row.length) continue;
      let x = PAD;
      for (const s of row) { s.x = x; s.y = y; x += s.width + SPACING; }
      maxRight = Math.max(maxRight, x - SPACING);
      y += Math.max(...row.map((s) => s.height)) + SPACING;
    }
    section.resizeWithoutConstraints(Math.max(sec.width, maxRight + PAD), y - SPACING + PAD);
    for (const c of sec.connectors) {
      const conn = figma.createConnector();
      conn.connectorStart = { endpointNodeId: made[c.from].id, magnet: "AUTO" };
      conn.connectorEnd = { endpointNodeId: made[c.to].id, magnet: "AUTO" };
      conn.connectorStartStrokeCap = "NONE";
      conn.connectorEndStrokeCap = "ARROW_LINES";
      conn.strokes = [{ type: "SOLID", color: hex(CONNECTOR) }];
      conn.text.fontName = labelFont;
      conn.text.characters = c.label;
      connectorIds.push(conn.id);
      all.push(conn);
    }
    sectionIds.push(section.id);
    for (const s of Object.values(made)) stickyIds.push(s.id);
    all.push(section);
  }

  // Run card above the grid.
  let cardId: string | null = null;
  if (layout.sections.length) {
    const x0 = Math.min(...layout.sections.map((s) => s.x)) + dx;
    const y0 = Math.min(...layout.sections.map((s) => s.y)) + dy;
    const section = makeSection(`Motif · ${layout.card?.run_id ?? layout.run_id ?? "run"}`, "FFFFFF", x0, y0);
    const s = makeSticky(section, { key: "card", role: "card", wide: true, color: cardColor(layout), text: cardText(layout) });
    s.x = PAD; s.y = PAD;
    section.resizeWithoutConstraints(Math.max(layout.sections[0].width, s.width + 2 * PAD), s.height + 2 * PAD);
    section.y = y0 - section.height - CARD_GAP;
    cardId = section.id;
    stickyIds.push(s.id);
    all.push(section);
  }

  return finish(all, sectionIds, stickyIds, connectorIds, cardId, "figjam");
}

// ------------------------------------------------------------ Figma Design

async function renderDesign(layout: Layout, dx: number, dy: number): Promise<BoardResult> {
  const font: FontName = { family: "Inter", style: "Regular" };
  await figma.loadFontAsync(font);
  const sectionIds: string[] = [], stickyIds: string[] = [];
  const all: SceneNode[] = [];

  const makeSection = (name: string, fill: string, x: number, y: number): SectionNode => {
    const section = figma.createSection();
    section.name = name;
    section.fills = [{ type: "SOLID", color: hex(fill) }];
    section.x = x; section.y = y;
    return section;
  };
  const makeNote = (section: SectionNode, st: Sticky): FrameNode => {
    const f = figma.createFrame();
    f.name = st.key;
    f.layoutMode = "VERTICAL";
    f.paddingTop = f.paddingBottom = f.paddingLeft = f.paddingRight = 16;
    f.cornerRadius = 4;
    f.fills = [{ type: "SOLID", color: hex(st.color) }];
    section.appendChild(f);
    f.resize(st.wide ? 480 : 240, 100);
    f.primaryAxisSizingMode = "AUTO";
    f.counterAxisSizingMode = "FIXED";
    const t = figma.createText();
    t.fontName = font;
    t.fontSize = 14;
    t.characters = st.text;
    f.appendChild(t);
    t.layoutSizingHorizontal = "FILL";
    t.textAutoResize = "HEIGHT";
    return f;
  };

  for (const sec of layout.sections) {
    const section = makeSection(sec.name, sec.fill, sec.x + dx, sec.y + dy);
    const made: Record<string, FrameNode> = {};
    for (const st of sec.stickies) made[st.key] = makeNote(section, st);
    if (Object.keys(made).length !== sec.stickies.length) {
      throw new Error(`section ${sec.insight_id}: ${Object.keys(made).length} of ${sec.stickies.length} notes created`);
    }
    const rows = [1, 2].map((r) => sec.stickies.filter((s) => rowOf(s) === r).map((s) => made[s.key]));
    let y = PAD, maxRight = 0;
    for (const row of rows) {
      if (!row.length) continue;
      let x = PAD;
      for (const f of row) { f.x = x; f.y = y; x += f.width + SPACING; }
      maxRight = Math.max(maxRight, x - SPACING);
      y += Math.max(...row.map((f) => f.height)) + SPACING;
    }
    section.resizeWithoutConstraints(Math.max(sec.width, maxRight + PAD), y - SPACING + PAD);
    sectionIds.push(section.id);
    for (const f of Object.values(made)) stickyIds.push(f.id);
    all.push(section);
  }

  let cardId: string | null = null;
  if (layout.sections.length) {
    const x0 = Math.min(...layout.sections.map((s) => s.x)) + dx;
    const y0 = Math.min(...layout.sections.map((s) => s.y)) + dy;
    const section = makeSection(`Motif · ${layout.card?.run_id ?? layout.run_id ?? "run"}`, "FFFFFF", x0, y0);
    const f = makeNote(section, { key: "card", role: "card", wide: true, color: cardColor(layout), text: cardText(layout) });
    f.x = PAD; f.y = PAD;
    section.resizeWithoutConstraints(Math.max(layout.sections[0].width, f.width + 2 * PAD), f.height + 2 * PAD);
    section.y = y0 - section.height - CARD_GAP;
    cardId = section.id;
    stickyIds.push(f.id);
    all.push(section);
  }
  return finish(all, sectionIds, stickyIds, [], cardId, "figma");
}

function finish(all: SceneNode[], sectionIds: string[], stickyIds: string[], connectorIds: string[],
                cardId: string | null, editor: string): BoardResult {
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const n of all) {
    if (!("x" in n) || n.type === "CONNECTOR") continue;  // connectors sit between their endpoints; sections bound the board
    x0 = Math.min(x0, n.x); y0 = Math.min(y0, n.y); x1 = Math.max(x1, n.x + n.width); y1 = Math.max(y1, n.y + n.height);
  }
  return {
    sectionIds, stickyIds, connectorIds, cardId,
    nodeIds: [...sectionIds, ...stickyIds, ...connectorIds, ...(cardId ? [cardId] : [])],
    counts: { sections: sectionIds.length, stickies: stickyIds.length, connectors: connectorIds.length },
    bounds: { x: x0, y: y0, width: x1 - x0, height: y1 - y0 }, editor,
  };
}

/** Render a layout on the current page. Chooses a free origin unless one is given. */
export async function renderBoard(layout: Layout, opts: { origin?: [number, number]; editor?: string } = {}): Promise<BoardResult> {
  if (!layout?.sections?.length) throw new Error("the layout has no sections; nothing to put on the board");
  const expected = layout.sections.reduce((n, s) => n + s.stickies.length, 0);
  if (!expected) throw new Error("the layout has no stickies; nothing to put on the board");
  const origin = opts.origin ?? chooseOrigin(figma.currentPage);
  const dx = origin[0] - layout.origin[0], dy = origin[1] - layout.origin[1];
  const editor = opts.editor ?? figma.editorType;
  const res = editor === "figjam" ? await renderFigJam(layout, dx, dy) : await renderDesign(layout, dx, dy);
  const got = res.counts.stickies - (res.cardId ? 1 : 0);
  if (got !== expected) throw new Error(`board incomplete: ${got} of ${expected} stickies were created`);
  return res;
}
