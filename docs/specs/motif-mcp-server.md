# Spec — Motif MCP server (v2, first surface)

*Supersedes the v1 MCP spec and reorders the FigJam plugin behind it. Based on `research/etot-research-pain-points-and-platforms.md` (2026-09-04).*

## Why this is first
One MCP server reaches every surface that matters: Claude Code, Cursor, Claude Desktop, ChatGPT (direct); FigJam, via Figma's own MCP server which writes stickies, sections and connectors; Figma Make's connector slot; Lovable's custom MCP connectors; Notion custom agents; Miro's bidirectional MCP (100M users). A FigJam plugin reaches FigJam. Sources in the research report, Deliverable 3 and 4.

## Step zero — verify the FigJam write path (before any build)
Figma's MCP write-to-canvas is beta and will become usage-priced. In Claude Code with `figma@claude-plugins-official` installed: create a real FigJam board, ask Claude to place three stickies in a section with connectors, and confirm it works reliably three times. Record the result in `docs/part2-notes.md`. If it is flaky or gated, the thin FigJam plugin moves back up and this spec's FigJam handoff becomes "export a board-ready JSON" instead.

## Tools to expose
1. `motif_synthesize(transcripts, question, condition="C", max_iterations=3)` — transcripts as file paths or pasted text; returns insights JSON, report markdown, run id.
2. `motif_critique(insights_or_text, transcripts)` — **the headline tool.** Runs only the check + critic half of the loop against *anyone's* synthesis: a Dovetail Magic summary, a FigJam AI summary, a ChatGPT paste. Accepts loose text (the tool structures it into claims first, then checks). Returns a verdict: which claims are supported by which spans, which are unsupported, which participant dissents, confidence calibration. This is the "second reader" and the differentiator the research found nobody else ships.
3. `motif_receipts(turn_ids)` — verbatim turn text for any cited id, so a host can show evidence inline.
4. `motif_board(run_id or insights)` — returns a board layout description (frames, stickies, colours, connectors) in the shape Figma's MCP and Miro's MCP accept, so the host agent can lay it out. Motif never talks to Figma directly; it hands the host a plan.
5. `motif_runs_get(run_id)` — the full log, iterations, verdicts.

## Modes
- **Local** (default): engine runs in-process with the user's own Anthropic key from `.env` or an env var. Nothing leaves the machine except model calls.
- **Remote** (later): the hosted engine service, for hosts that can't run Python. Not in v1 of this surface.

## Key policy
Bring your own key. No ETOT-paid runs. Documented once in the README with a link to console.anthropic.com.

## Distribution
- `pip install etot-motif` gives `motif` (CLI) and `motif-mcp` (server).
- Install snippets for Claude Code, Cursor, Claude Desktop.
- Listed on whatever MCP registries and marketplaces are live at ship time.
- A **SKILL.md wrapper** (`motif` skill) that invokes the CLI, published where designer skill packs live. One day of work; not a surface with measurable outcomes on its own.

## What "done" looks like
- A recorded Claude Code session: transcripts → `motif_synthesize` → `motif_board` → Figma MCP lays it out → a FigJam board with receipts on stickies and red "contested" stickies. Same for Miro if the write path works.
- A second recording: a FigJam AI summary pasted into `motif_critique`, with the verdict showing which of its claims the transcripts don't support.
- Ten installs and three pieces of written feedback captured for the part-2 case study.
- Time-to-first-board under fifteen minutes for someone who already uses Claude Code.

## Build order
1. Step zero (verify FigJam write).
2. `motif_critique` on pasted text — smallest, highest-leverage, and testable against Eval 2's blind packs (feed it R1–R6; it should flag what the scoring sheet flagged).
3. `motif_synthesize` + `motif_receipts` + `motif_runs_get` (thin wrappers over existing functions).
4. `motif_board` + the Claude Code → FigJam demo.
5. SKILL.md wrapper, README, install snippets, listing.

## Out of scope for this surface
Hosted service, web UI, storage, the FigJam plugin (separate, later, thin), Figma Make credit interception (no hook exists).

## Working discipline (applies to every ETOT chat)
- **Notes as you go.** Append to `docs/part2-notes.md` after every session: one dated line per decision, surprise, failure, or number. Create it in the first session. The part-2 case study is written from this file.
- **Log as you go.** `docs/log.md`: dated, three lines per session — tried / happened / next.
- **Record, don't reconstruct.** Any number or quote destined for a write-up is copied from a file with its path.
- **Full commands.** Complete terminal and file sequences every time — open, paste, save, exit, commit, push — never "like before."
- **Silence is never approval.** A missing verdict, an empty result, or a parse failure is a hard failure.
- Re-run the Eval 2 blind packs through `motif_critique` and record agreement with the human scoring before calling the tool done.
