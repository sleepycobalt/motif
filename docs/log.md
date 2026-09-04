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
