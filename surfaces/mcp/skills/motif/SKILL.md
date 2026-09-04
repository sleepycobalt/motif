---
name: motif
description: Use the Motif MCP server (motif_synthesize, motif_critique, motif_receipts, motif_board, motif_runs_get) to turn interview transcripts into a cited, critic-checked research synthesis, to check any synthesis against its transcripts, to verify citations, and to push a run onto a FigJam board. Load before calling any motif_* tool.
---

# Motif — research synthesis with receipts

Motif reads a folder of interview transcripts and produces 8–14 insights.
Each insight carries a claim, cited turns with verbatim receipts, a confidence
level defined numerically (high = 4+ participants and no counter-evidence),
counter-evidence, and a design opportunity. A critic checks every insight
against the transcripts and the synthesis is revised until the critic passes
or the round limit is hit. Citations are turn ids like `michelle:0042`.

## Before you start

- Transcripts: one speaker turn per line or paragraph, `Name: text`. Label
  the interviewer `Interviewer`, `Researcher`, or `Moderator`; their turns are
  never evidence. `.docx`, `.txt`, `.md` all work.
- A full run spends API budget and time. Fifteen 45-minute transcripts take
  about 20 minutes and about $2.50. Say so before starting one; do not start
  a run the user has not asked for.
- The server must be installed and connected (`/mcp` in Claude Code). If a
  tool is missing, stop and say so rather than improvising a synthesis
  yourself: Motif's value is the receipts and the critic, and a synthesis
  written without them must not be presented as a Motif result.

## Workflow

1. **Synthesise**: `motif_synthesize(transcripts_dir=..., question=...)`.
   Relay the progress notifications as they arrive (intake per transcript,
   synthesis, critic rounds). The result has `run_id`, `insights`,
   `report_markdown`, and `contested`.
2. **Read `contested` first.** Those insights still carried a critic
   objection when the loop stopped. Show them with their `critic_flags`;
   never present a contested insight as settled.
3. **Verify before you quote.** Before repeating a claim to the user as
   established, call `motif_receipts(turn_ids=[...], run_id=...)` for the
   cited turns and check the quote against the text. If `missing` is not
   empty, say which citations could not be verified.
4. **Report**: write `report_markdown` to the file the user asked for, or
   summarise it. Keep turn ids in any summary so the user can trace it.
5. **Board (optional)**: `motif_board(run_id=...)` returns a layout and one
   `use_figma` script per insight. Run each script through Figma's MCP server
   with skills `figma-use,figma-use-figjam` against the user's FigJam board
   URL, then read the board back with `get_figjam`. A script that returns no
   node ids has failed; say so.

## Checking a synthesis that is not Motif's

`motif_critique(document=<markdown or prose>, transcripts_dir=...)`
structures the document into claims (copying its citations, never inventing
them) and runs the critic. Report the verdict as it is: `pass`, the failures
by insight and rule, and `skipped_rules` (the missing-theme rule needs intake
notes, which only a Motif run has). A document with no turn citations fails
every insight on `bad_citation`; that is the honest answer, not an error to
work around.

## Rules

- A tool error is a failure to report, not a reason to retry blindly. An
  empty result never happens; if you see one, something is wrong.
- Do not paraphrase a receipt. Quote it or cite the turn id.
- Confidence levels are defined in `config/synth.yaml`; do not upgrade one.
- Run logs live under `runs/<run_id>/`; `motif_runs_get` returns the critic's
  verdict at each round if the user wants to see what changed and why.
