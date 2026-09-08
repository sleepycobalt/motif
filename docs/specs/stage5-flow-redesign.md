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

## Ruled 2026-09-08

**Open on "what do you have," not a mode toggle.** The first screen asks a question a
stranger can answer without knowing what Motif is: do you have transcripts, or someone's
findings? Transcripts is the visually primary answer and takes default focus; findings is
reachable on the same screen but secondary. The mode becomes a consequence of the answer
rather than a choice about the tool.

**Illegal states unreachable rather than validated.** Today the wrong input is accepted
and refused later — on 2026-09-08 that refusal ran after a $0.20 job had already
completed. A critique report should not be submittable at all, because the tool knows
what it is.

**`last_result` stops being a single slot.** A synthesis and the critique of it are kept
together, so checking never destroys what it checked. Three of the ten known defects
descend from the single-slot, memory-only state model.

## The gate

One person who has never seen Motif. Install to board. No instructions, no explanation,
no one answering questions. Timed and observed.

The stage-2 gate was written in this spirit and never run on a stranger — the builder was
the first user and already knew the tool. This one is run for real, and what the observer
writes down is the result.

## Sequence, ruled

1. `docs/plugin-flow.md` — the description of the present, from the code. Sonnet 5 in the
   Motif repo. In progress.
2. The target flow, written against that description, not against a memory of the code.
   Opus 5. Added to this brief.
3. Build, then the gate above.

v3 ships before any of this: the restyle, the button row, and the verdict guard. The flow
is no worse than the live build, and the restyle is a real improvement.
