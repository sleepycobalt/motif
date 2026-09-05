## 2026-09-02 — Corpus and brief
Tried: Downloaded Sheffield Dataset 2 and 3; verified 15 transcripts, ~105k words, CC-BY-NC.
Happened: Promised XML codebook was never deposited; using the final project report as insight-level ground truth instead.
Next: Manual synthesis on 5 transcripts, then transcript conversion script.

## 2026-09-02 — Setup
Tried: Console account, API key, venv, git, smoke test.
Happened: Git identity, pasted-line, and curly-quote snags; API worked first try (17 in / 15 out).
Next: R&D brief, pull Sheffield corpus.

## 2026-09-03 — Manual synthesis and ground truth
Tried: Hand-synthesised 5 transcripts (Michelle, David, Bruce, Stephen, Penni) — 2h05 reading, 45m clustering, 74 evidence items, 11 insights.
Happened: 9 of 11 insights matched the researchers' report; 5 report themes live in transcripts I didn't read. Built theme checklist (16) and trap list (12).
Next: Intake pipeline — convert docx to text with line refs.

## 2026-09-04 — MCP server, step zero
Tried: Verify Figma's MCP write path to FigJam before writing Motif code; read the engine for an architecture proposal.
Happened: Write path exists (`use_figma` + `figma-use-figjam` skill, remote server only, OAuth). Registered the server; blocked on the OAuth click. Found stdout-printing logger and subprocess CLI as the two engine changes the server needs first.
Next: User authenticates Figma in `/mcp` and gives a board URL; run the write test; then extract `synth/engine.py` and build `motif.synthesize`.

## 2026-09-04 — Step zero run
Tried: OAuth to Figma's remote MCP, create a throwaway FigJam board, write a section + 3 stickies + connector via `use_figma`, read back, screenshot.
Happened: Passed first time. Five nodes created and read back; screenshot in `docs/exhibits/step-zero/`. One sticky colour round-tripped as CUSTOM. Five tools confirmed (board is the fifth); architecture approved; critique must be validated against `eval2/blind/` R1–R6 vs `eval2/scoring.md`.
Next: Build step 1 — extract `synth/engine.py`, logger emit hook, corpus snapshot; offline tests with a stubbed model; one regression run.

## 2026-09-04 — MCP server build
Tried: Engine extraction, logger emit/redact/snapshot, MCP server with five tools on the 2.x SDK, offline tests, live regression, board tool executed on the real FigJam board, critique acceptance vs eval2 through the server.
Happened: 19 offline tests pass; ingest byte-identical; regression run $0.55/441 s/13 insights with corpus snapshot; R5 board (15 sections, 78 stickies, 12 connectors) built and read back. Venv had lost its packages; SDK 2.x renamed FastMCP; plain exceptions hide tool error text.
Happened (cont.): Acceptance recorded — structuring passes (deterministic and model identical); verdict agreement partial: unsupported 25/32, P-03 5/8, P-05 2/8. Client needed log_level for log notifications; progress now sent on every emit. `motif` registered in Claude Code and connected.
Ruling: accept the measured gap, no instrument changes; recorded. Step 5 done: host install snippets (Claude Code, Cursor, Claude Desktop), SKILL.md wrapper, listing copy, registry server.json (validated; description cap 100 chars).
Next: User records the sample-corpus Claude Code session; publish `etot-motif` to PyPI, then the registry entry.

## 2026-09-04 — PyPI publish (entry added retroactively in the part-3 session)
Tried: Build and publish `etot-motif` 0.2.0, verify from PyPI in a fresh venv, submit the registry manifest.
Happened: The wheel would have shipped without `synth.yaml`; fixed first (config moved into the package, `config/synth.yaml` symlinked). Published; fresh-venv install gives working `motif` and `motif-mcp` (five tools over stdio). Registry entry `io.github.sleepycobalt/motif` 0.2.0 active. Notes in `docs/part2-notes.md`.
Next: Part 3 — hosted engine, plugin, board writer, listing.

## 2026-09-04 — Part 3 planning
Tried: Read the plugin spec, the MCP spec, and CONTRIBUTING; propose architecture and build order before code.
Happened: Proposal in `docs/specs/part3-build-plan.md`: one hosted job API over the unchanged engine, plugin free tier as its client with the user's key forwarded per job, board writer from the existing layout data, paid tier designed behind a flag. Found: per-request key needs a context-var client in `core/llm.py`; stickies are FigJam-only; credits need a Stripe-fed ledger.
Next: Ruling on hosting, Design-editor timing, and payment rails; then stage 1 (hosted service, remote mode, offline tests, deploy).
