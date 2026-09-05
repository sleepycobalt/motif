"""
FigJam board output. Turns a run's insights into (a) a layout: one section per
insight holding a claim sticky, receipt stickies, counter-evidence stickies,
and an opportunity sticky, with connectors from claim to counter-evidence;
and (b) one `use_figma` script per section that a host holding Figma
credentials can execute against a board. Motif never talks to Figma itself.

Colours are FigJam sticky palette values in hex/255 notation (step zero showed
that rounded decimals and some palette entries round-trip as CUSTOM).
"""

from __future__ import annotations

import json

from synth.agents import turn_ids

# Sticky palette (from Figma's figma-use-figjam reference). Roles -> hex.
STICKY = {
    "claim_high": "B3EFBD",    # green
    "claim_medium": "FFE299",  # yellow
    "claim_low": "FFD3A8",     # orange
    "receipt": "FFFFFF",       # white
    "counter": "FFA8DB",       # pink
    "opportunity": "A8DAFF",   # blue
    "contested": "D3BDFF",     # violet
}
SECTION_FILL = "F5FBFF"        # light blue
CONNECTOR = "F849C1"           # pink stroke

SECTION_W = 1600
SLOT_H = 1200          # tallest section seen on the R5 board was 984px
GAP = 120
PAD = 48
SPACING = 40


def _q(item) -> tuple[str, str]:
    if isinstance(item, dict):
        return item.get("turn", ""), item.get("quote", "") or ""
    return str(item), ""


def layout(insights: list[dict], meta: dict | None = None, columns: int = 2,
           origin: tuple[float, float] = (0, 0)) -> dict:
    """Pure data: what goes on the board and where each section sits."""
    meta = meta or {}
    sections = []
    for n, ins in enumerate(insights):
        conf = (ins.get("confidence") or "low").lower()
        stickies = [{"key": "claim", "role": "claim", "wide": True,
                     "color": STICKY.get(f"claim_{conf}", STICKY["claim_low"]),
                     "text": f"{ins.get('id', '?')} · {conf.upper()}\n{ins.get('title', '')}\n\n{ins.get('claim', '')}"}]
        for i, item in enumerate(ins.get("evidence") or []):
            turn, quote = _q(item)
            stickies.append({"key": f"receipt{i}", "role": "receipt", "wide": False, "color": STICKY["receipt"],
                             "text": f"{turn}\n“{quote}”" if quote else f"{turn}\n(no receipt)"})
        counters = []
        for i, item in enumerate(ins.get("counter_evidence") or []):
            turn, quote = _q(item)
            key = f"counter{i}"
            counters.append(key)
            note = f"\n{ins.get('counter_note')}" if i == 0 and ins.get("counter_note") else ""
            stickies.append({"key": key, "role": "counter", "wide": False, "color": STICKY["counter"],
                             "text": f"COUNTER {turn}\n“{quote}”{note}" if quote else f"COUNTER {turn}{note}"})
        if ins.get("opportunity"):
            stickies.append({"key": "opportunity", "role": "opportunity", "wide": True,
                             "color": STICKY["opportunity"], "text": f"OPPORTUNITY\n{ins['opportunity']}"})
        if ins.get("critic_flags"):
            stickies.append({"key": "contested", "role": "contested", "wide": True, "color": STICKY["contested"],
                             "text": "CONTESTED — critic's unresolved objections:\n" + "\n".join(ins["critic_flags"])})
        sections.append({
            "insight_id": ins.get("id", f"I-{n + 1:02d}"),
            "name": f"{ins.get('id', '?')} · {ins.get('title', '')}"[:80],
            "x": origin[0] + (n % columns) * (SECTION_W + GAP),
            "y": origin[1] + (n // columns) * (SLOT_H + GAP),
            "width": SECTION_W,
            "fill": SECTION_FILL,
            "stickies": stickies,
            "connectors": [{"from": "claim", "to": c, "label": "contested by"} for c in counters],
            "sources": ins.get("sources", []),
            "turns": turn_ids(ins.get("evidence")) + turn_ids(ins.get("counter_evidence")),
        })
    return {
        "title": f"Motif synthesis — run {meta.get('run_id', '')}".strip(" —"),
        "kind": "synthesis",
        "run_id": meta.get("run_id"),
        "columns": columns,
        "origin": list(origin),
        "n_sections": len(sections),
        "sections": sections,
        "card": _card(meta, {
            "insights": len(insights),
            "contested": [i.get("id") for i in insights if i.get("critic_flags")],
        }),
    }


def _card(meta: dict, counts: dict) -> dict:
    """What a board's run card says: the run, the question, the numbers, and any open objections."""
    cfg = meta.get("config") or {}
    corpus = meta.get("corpus") or {}
    return {
        "run_id": meta.get("run_id"),
        "question": cfg.get("question"),
        "transcripts": corpus.get("transcripts") or cfg.get("transcripts") or [],
        "words": corpus.get("words"),
        "condition": meta.get("condition"),
        "iterations": meta.get("iterations"),
        "stop_reason": meta.get("stop_reason"),
        "cost": meta.get("cost"),
        "wall_seconds": meta.get("wall_seconds"),
        "started": meta.get("started"),
        **counts,
    }


VERDICT_STICKY = {"claim_pass": STICKY["claim_high"], "claim_fail": STICKY["counter"],
                  "claim_warn": STICKY["claim_medium"], "fail": STICKY["counter"],
                  "warn": STICKY["claim_medium"], "theme": STICKY["contested"]}


def verdict_layout(insights: list[dict], verdict: dict, meta: dict | None = None, columns: int = 2,
                   origin: tuple[float, float] = (0, 0)) -> dict:
    """A critic verdict as a board: one section per checked claim, coloured by outcome, with one
    sticky per objection; a final section for corpus-level objections (insight_id '*')."""
    meta = meta or {}
    failures = verdict.get("failures") or []
    by_id: dict = {}
    for f in failures:
        by_id.setdefault(f.get("insight_id") or "*", []).append(f)
    sections = []

    def place(n: int) -> tuple[float, float]:
        return origin[0] + (n % columns) * (SECTION_W + GAP), origin[1] + (n // columns) * (SLOT_H + GAP)

    for n, ins in enumerate(insights):
        objections = by_id.pop(ins.get("id"), [])
        worst = "fail" if any(f.get("severity", "fail") == "fail" for f in objections) else \
                "warn" if objections else "pass"
        stickies = [{"key": "claim", "role": "claim", "wide": True, "row": 1,
                     "color": VERDICT_STICKY[f"claim_{worst}"],
                     "text": f"{ins.get('id', '?')} · {worst.upper()}\n{ins.get('title', '')}\n\n{ins.get('claim', '')}"}]
        for i, f in enumerate(objections):
            sev = f.get("severity", "fail")
            turns = ", ".join(f.get("turns") or [])
            stickies.append({"key": f"objection{i}", "role": sev, "wide": True, "row": 2,
                             "color": VERDICT_STICKY[sev],
                             "text": f"{sev.upper()} · {f.get('rule')}\n{f.get('detail', '')}" + (f"\n\nturns: {turns}" if turns else "")})
        x, y = place(n)
        sections.append({"insight_id": ins.get("id", f"I-{n + 1:02d}"),
                         "name": f"{ins.get('id', '?')} · {worst} · {ins.get('title', '')}"[:80],
                         "x": x, "y": y, "width": SECTION_W, "fill": SECTION_FILL,
                         "stickies": stickies, "connectors": [], "sources": ins.get("sources", []),
                         "turns": turn_ids(ins.get("evidence")) + turn_ids(ins.get("counter_evidence"))})
    rest = [f for fs in by_id.values() for f in fs]
    if rest:
        stickies = [{"key": f"corpus{i}", "role": "theme", "wide": True, "row": 1, "color": VERDICT_STICKY["theme"],
                     "text": f"{f.get('rule', '').upper()} (whole corpus)\n{f.get('detail', '')}"
                             + (f"\n\nturns: {', '.join(f.get('turns') or [])}" if f.get("turns") else "")}
                    for i, f in enumerate(rest)]
        x, y = place(len(sections))
        sections.append({"insight_id": "*", "name": "Objections about the whole corpus", "x": x, "y": y,
                         "width": SECTION_W, "fill": SECTION_FILL, "stickies": stickies, "connectors": [],
                         "sources": [], "turns": []})
    n_fail = sum(1 for f in failures if f.get("severity", "fail") == "fail")
    n_warn = sum(1 for f in failures if f.get("severity") == "warn")
    return {
        "title": f"Motif critique — run {meta.get('run_id', '')}".strip(" —"),
        "kind": "verdict",
        "run_id": meta.get("run_id"),
        "columns": columns,
        "origin": list(origin),
        "n_sections": len(sections),
        "sections": sections,
        "card": _card(meta, {"claims": len(insights), "pass": bool(verdict.get("pass")), "fails": n_fail,
                             "warns": n_warn, "skipped_rules": verdict.get("skipped_rules") or []}),
    }


SCRIPT_TEMPLATE = """\
// Motif board section {insight_id} — generated; run with use_figma (skills: figma-use, figma-use-figjam)
const S = {spec};
const h = (hex) => ({{ r: parseInt(hex.slice(0, 2), 16) / 255, g: parseInt(hex.slice(2, 4), 16) / 255, b: parseInt(hex.slice(4, 6), 16) / 255 }});
const section = figma.createSection();
section.name = S.name;
section.fills = [{{ type: 'SOLID', color: h(S.fill) }}];
section.x = S.x; section.y = S.y;
const probe = figma.createSticky();
await figma.loadFontAsync(probe.text.fontName);
probe.remove();
const made = {{}};
for (const st of S.stickies) {{
  const s = figma.createSticky();
  s.text.characters = st.text;
  s.isWideWidth = !!st.wide;
  s.fills = [{{ type: 'SOLID', color: h(st.color) }}];
  s.authorVisible = false;
  section.appendChild(s);
  made[st.key] = s;
}}
// Row 1: claim then receipts; row 2: counters then opportunity/contested. Two-pass: measure, then place.
const rowOf = (s) => s.row || ((s.role === 'claim' || s.role === 'receipt') ? 1 : 2);
const row1 = S.stickies.filter(s => rowOf(s) === 1).map(s => made[s.key]);
const row2 = S.stickies.filter(s => rowOf(s) === 2).map(s => made[s.key]);
let y = {pad}, maxRight = 0;
for (const row of [row1, row2]) {{
  if (!row.length) continue;
  let x = {pad};
  for (const s of row) {{ s.x = x; s.y = y; x += s.width + {spacing}; }}
  maxRight = Math.max(maxRight, x - {spacing});
  y += Math.max(...row.map(s => s.height)) + {spacing};
}}
section.resize(Math.max(S.width, maxRight + {pad}), y - {spacing} + {pad});
const font = {{ family: 'Inter', style: 'Medium' }};
await figma.loadFontAsync(font);
const connectors = [];
for (const c of S.connectors) {{
  const conn = figma.createConnector();
  conn.connectorStart = {{ endpointNodeId: made[c.from].id, magnet: 'AUTO' }};
  conn.connectorEnd = {{ endpointNodeId: made[c.to].id, magnet: 'AUTO' }};
  conn.connectorStartStrokeCap = 'NONE';
  conn.connectorEndStrokeCap = 'ARROW_LINES';
  conn.strokes = [{{ type: 'SOLID', color: h('{connector}') }}];
  conn.text.fontName = font;
  conn.text.characters = c.label;
  connectors.push(conn.id);
}}
return {{
  insightId: S.insight_id,
  sectionId: section.id,
  stickyIds: Object.fromEntries(Object.entries(made).map(([k, s]) => [k, s.id])),
  connectorIds: connectors,
  createdNodeIds: [section.id, ...Object.values(made).map(s => s.id), ...connectors],
  sectionSize: [section.width, section.height],
}};
"""


def scripts(board: dict) -> list[dict]:
    """One use_figma script per section. Each is self-contained and returns the node ids it made."""
    out = []
    for sec in board["sections"]:
        spec = {k: sec[k] for k in ("insight_id", "name", "x", "y", "width", "fill", "stickies", "connectors")}
        code = SCRIPT_TEMPLATE.format(insight_id=sec["insight_id"], spec=json.dumps(spec, ensure_ascii=False),
                                      pad=PAD, spacing=SPACING, connector=CONNECTOR)
        out.append({"insight_id": sec["insight_id"], "code": code, "chars": len(code)})
    return out


HOST_INSTRUCTIONS = (
    "Run each script in order with Figma's `use_figma` tool against a FigJam board (URL "
    "figma.com/board/<fileKey>/...), passing skillNames 'figma-use,figma-use-figjam' "
    "(prefix 'resource:' if loaded as MCP resources). Each script creates one section and "
    "returns the node ids it made; every script must return ids, and a script that returns "
    "no ids has failed. Read the board back with `get_figjam` afterwards to confirm."
)
