# Stage 5 — the plugin's flow

*Opened 2026-09-08 from the stage-4 hand check. Not a patch to stage 4; v3 ships the
restyle and the two fixes as they are.*

## Bar

A researcher who has never seen Motif installs it and reaches a board without reading
anything.

This is the stage-2 gate's spirit, never actually tested on a stranger — the builder was
the first user and already knew the tool.

## Problem statement

The evidence is that the flow is confusing to an operator with the source open. Over one
session Claude, working from `ui.ts`, mis-instructed the user three times: named a
control absent from the screen he was on, assumed a stored synthesis that a critique had
already overwritten, and proposed a round-trip test whose input was degenerate.

Five root causes, to be confirmed against `docs/plugin-flow.md`:

1. Two different jobs share one form via a mode switch. The card numbering, the meaning
   of the transcripts field, and the run button all change under the user.
2. The result screen offers four peer actions with no indication of what normally comes
   next.
3. Nothing on any screen indicates position in the process.
4. `last_result` is a single slot, so running a critique destroys the synthesis it was
   checking, with no way back.
5. The normal path to check a synthesis is to copy its report to the clipboard and paste
   it back into the same plugin — an implementation detail leaking into the flow.
   "Check this synthesis" exists to fix that and is memory-only, so it dies on reopen.

## Sequence

`docs/plugin-flow.md` first, derived from the code. Then a flaw list against it. Then a
redesign proposal, judged against the bar above. Nothing is designed from memory of using
the tool.
