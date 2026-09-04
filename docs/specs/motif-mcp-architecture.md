# Proposal — Motif MCP server architecture and build order

*Status: approved and built 2026-09-04. Companion to `motif-mcp-server.md`. Step zero passed the same day (`docs/exhibits/step-zero/`); the board tool was verified on the same board with run R5 (`docs/exhibits/board-r5/`). What shipped differs from the proposal in the ways marked "as built" below.*

## Shape

```
synth/engine.py          NEW  the shared engine service. Pure functions, no argparse, no print:
                              ingest(), synthesize(), critique(), critique_document(), receipts(),
                              corpus_for_run(), load_run(), board()
synth/ingest.py          NEW  ingest moved out of scripts/ (which is now a shim)
synth/board.py           NEW  FigJam layout + use_figma script generation (as built)
synth/run.py             becomes argparse + one call into engine (CLI keeps working)
synth/cli.py             calls engine directly; no subprocesses, no stdout parsing
core/logger.py           gains an `emit` hook (default stderr) and a `redact` flag
synth/corpus.py          raises ValueError instead of SystemExit

surfaces/mcp/
  server.py              MCPServer (mcp SDK 2.x); tool definitions only, each a thin call into synth.engine;
                         engine emit -> MCP log + progress notifications (as built: no separate progress.py)
  remote.py              HTTP client for the hosted service (contract defined; service not live)
  README.md              install for Claude Code and Cursor
tests/                   offline engine tests (stubbed model) + server round-trip over stdio
scripts/critique_acceptance.py   critic vs eval2 human scoring, through the server
pyproject.toml           optional extra `[mcp]`; console script `motif-mcp`
```

Rule: the server never touches `core.llm`, `synth.prompts`, or the loop. If a tool needs something the engine can't do, the engine grows, not the server. The FigJam plugin's service will call the same `synth.engine`.

## Why the engine has to move first

- `synth/cli.py` runs ingest and `synth.run` as subprocesses and finds the run dir by parsing stdout. A server can't do that.
- `RunLogger` prints to stdout. On stdio transport stdout *is* the MCP wire; one print corrupts the session. Every print becomes `self.emit(msg)`; the server's logger turns emits into `notifications/progress` and `notifications/message`.
- The loop wiring in `synth/run.py::main` is the engine. Moving it into `synth/engine.py` is what "same engine, same config; no prompt duplication" means in practice.

## Tool contracts (spec order)

Names exposed with underscores (`motif_synthesize`, `motif_runs_get`); dotted names stay in docs. Every tool: a missing verdict, empty result, or parse failure returns an MCP tool error, never a success with empty content.

1. **motif_synthesize**(transcripts_dir | files, question?, condition="C", max_iterations=3) → `{run_id, run_dir, insights, report_markdown, iterations, stop_reason, cost}`. Streams: ingest n/N, intake n/N, synthesis, critic i/max, revise i. Errors: no transcripts parsed; `stop_reason == synthesis_failed`.
2. **motif_critique**(insights | document, run_id | transcripts_dir, transcripts?, question?, structure_with_model?) → verdict JSON (`pass`, `failures`, `notes`, `skipped_rules`), summary by rule/insight, the structured insights, its own run id. As built: also accepts a markdown/prose `document`; Motif's own report format is parsed in code, anything else is structured by the model under a copy-only prompt (`synth/prompts.py::STRUCTURE_*`). With `run_id`, the run's intake notes are reused so `missing_theme` is checked; otherwise it is skipped and the verdict says so.
3. **motif_receipts**(turn_ids, run_id | transcripts_dir) → `[{turn, transcript, speaker, text, found}]` plus `missing`. Requires the run to have snapshotted its corpus (`runs/<id>/corpus/`), a change to the logger. Any missing id is reported; all missing is an error.
4. **motif_runs_get**(run_id, include=["meta","notes","iterations","verdicts"]) → the run's `meta.json`, notes, per-iteration verdict summaries. `calls` only on request. In remote mode, call bodies are never returned.
5. **motif_board**(run_id, columns, origin_x, origin_y) → a FigJam layout (one section per insight, sticky per claim colour-coded by confidence, receipts as text, connectors to counter-evidence) as JSON plus a ready `use_figma` script. Motif holds no Figma credentials; the host executes the script through Figma's MCP. Confirmed as the fifth tool; step zero verified the write path on 2026-09-04. Palette note: use only sticky colours that round-trip as palette colours (yellow `#FFE299` and green `#B3EFBD` did; red `#FFB8A8` came back `CUSTOM`).

**Acceptance for motif_critique:** before it is called done, run the six blind reports in `eval2/blind/` (R1–R6, insights from `runs/<id>/output.json` via `eval2/key.json`) through it and record agreement with `eval2/scoring.md` (Unsupported counts, P-03 and P-05 marks) in `docs/part2-notes.md`.

## Modes

- **Local**: engine in-process, user's `ANTHROPIC_API_KEY` from `.env` or env. Runs land in `runs/` under the current working directory.
- **Remote**: `MOTIF_REMOTE_URL` set → same tools, `remote.py` forwards to the hosted service. The server logs only run ids and timings; the hosted logger runs with `redact=True` (prompt bodies replaced by length and hash).

## Build order (all done 2026-09-04 except the recorded Claude Code session and remote service)

0. Step zero: FigJam write test on a real board via Figma's MCP — done, passed.
1. Engine extraction + logger emit hook + corpus snapshot. Regression: one condition-C run on five transcripts before and after; same run-dir layout, same rule ids firing. Offline tests stub `core.llm.call`.
2. `surfaces/mcp/server.py` with `motif_synthesize`, local mode, progress notifications. Smoke: MCP Inspector, then `claude mcp add` and a two-transcript run.
3. `motif_critique`, plus the eval2 agreement check above.
4. `motif_receipts`.
5. `motif_runs_get`.
6. README, Claude Code and Cursor snippets, recorded session on the sample corpus.
7. Remote mode client and redaction.
8. `motif_board`.
