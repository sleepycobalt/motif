# Spec — Motif MCP server

*For a build chat. Depends on the FigJam plugin's engine service (they share it). This is the "VST" surface: one server, usable from Claude Code, Cursor, and any MCP host.*

## Purpose
Make Motif callable from agent environments without a UI, so a designer or researcher working in Claude Code, Cursor, or an MCP-enabled tool can say "synthesise these transcripts" and get the same cited, critic-checked result.

## Tools to expose
- `motif.synthesize(transcripts_dir | files, question, condition="C", max_iterations=3)` → insights JSON + report markdown + run id.
- `motif.critique(insights_json, transcripts)` → verdict JSON. Lets other tools use the critic alone — useful for checking a synthesis written by someone else.
- `motif.receipts(turn_ids)` → verbatim turn text. Lets a host verify citations.
- `motif.runs.get(run_id)` → the run's log, iterations, and verdicts.

## Requirements
- Same engine, same config; no prompt duplication.
- Streams progress via MCP notifications where the host supports it.
- Local mode (runs the engine in-process with the user's key) and remote mode (calls the hosted service).
- Never logs transcript content in remote mode.

## Success criteria
- Installable with one command; documented for Claude Code and Cursor.
- A recorded example: a Claude Code session that synthesises the sample corpus and opens the report.

## Deliverables
1. `surfaces/mcp/` in the Motif repo with README and install snippets for two hosts.
2. Listed wherever MCP servers are indexed at the time of shipping.

## Working discipline (applies to every ETOT chat)
- **Notes as you go.** Append to the notes file after every session, not at the end: one dated line per moment worth writing up — a decision, a surprise, a failure, a number. File: `docs/part2-notes.md (in the Motif repo)`. If it doesn't exist, create it in the first session. The case study is written from this file; anything not in it is lost.
- **Log as you go.** `docs/log.md`: dated, three lines per session — tried / happened / next.
- **Record, don't reconstruct.** Any number or quote that will appear in a write-up is copied from a file (run log, output, source) with its path, never recalled.
- **Full commands.** When giving terminal or file steps, give the complete sequence every time — the exact command to open the file, what to paste, how to save and exit, and the git commands to commit and push — never "like before."
- **Silence is never approval.** In any loop or check you build, a missing verdict, an empty result, or a parse failure is a hard failure.
