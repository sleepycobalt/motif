# CUT — 2026-09-08

**This spec was written and never built. Nothing below this header is modified; it is
kept as the record of a design that was made and not shipped.**

The target flow and the four rulings were written in a design session on 2026-09-08 and
pushed at `bdaa5d5`. No build session followed. The build was cut on the judgment that the
research-tool category is video-first, that Motif is not competing with Dovetail,
Looppanel, or the video-first tools, and that perfecting a flow for users who are not
arriving is time better spent on the next tool. The plugin as it stands is usable,
accurately labeled, and professional. The agentic loop shipped, with three case studies
behind it. That was the goal.

**Of the twelve defects in the ledger below, one shipped as a fix: the panel height
(defect 12), released as v4.** The other eleven stand unfixed, by decision, not by
oversight.

**Correction to the height table below.** It caps every screen at 660 px on the assumption
that Figma clamps a panel to the window. It does not — commit `417f8aa` records the panel
clipping the FigJam toolbar when it is taller than the viewport. The ceiling is per
session, not a constant, and v4 measures it rather than assuming it. Read the height table
below as superseded on that point.

There is no Session B, no stranger gate, and no part 4.

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

---

# The target flow (step 2, ruled 2026-09-08)

*Written against `docs/plugin-flow.md`, `surfaces/figma/src/ui.ts` and
`surfaces/figma/src/code.ts`. Nothing here is described from memory of using the plugin.
Present behaviour cites a line; target behaviour cites the defect it closes.
`docs/plugin-flow.md` numbers eleven traps plus an unnumbered editor note; defect twelve
is the panel height, per this brief.*

## The spine

Four steps, named by destination, on every screen but the key screen:

**1 What you have · 2 Add it · 3 Run · 4 Board**

The stranger learns where this ends on the first screen. A completed chip is clickable
only when its screen is legal at that moment; step 4 is clickable whenever the work record
holds a result, which is the structural fix for trap 6 (`#last-card`'s visibility is read
once inside `init`, `ui.ts:598`, and never again).

## Opening precedence

1. A job in flight -> Running, following it (as today, `ui.ts:604`).
2. Else stored work -> Result, the newer half of the pair.
3. Else -> Start.

Ruling 1 governs the entry to a run, not the recovery of finished work.

## S0 — Key (no indicator)

Shown only when no key exists (`ui.ts:600`). Carries its own instruction: runs happen on
your own Anthropic key; about $1 for two transcripts, about $5 for fifteen (`ui.ts:209`);
the key is stored on this device and sent only to Motif's engine, for your runs (today
only a toast after saving, `code.ts:70`); a "Get a key" link. Save enables at 20
characters (`ui.ts:140`). Panel 440 x 420, no scroll region.

## S1 — Start: "What do you have?"

One line of what Motif is, then the question with two answers on one screen:

- **Transcripts** — visually primary, default focus. "Interviews or session notes. Motif
  writes the findings and checks every claim against the quote it came from."
- **Someone's findings** — secondary, smaller, below. "A summary from Dovetail, FigJam,
  ChatGPT, or a colleague. Motif checks it against the transcripts it came from."

The mode is the consequence of the answer. There is no toggle to return to, which makes
trap 1 unreachable rather than mitigated: `setMode()` (`ui.ts:201`) stops existing.

Quiet footer: masked key and "change" (off the setup screen, `ui.ts:143`) and the Figma
Design editor note (`ui.ts:599`). Panel 440 x 440.

## S2 — Add it: transcripts

1. Drop zone. Exactly one control opens the picker: the label wrapping the input.
   `drop.onclick` (`ui.ts:250`) is removed — that handler plus the label's native
   activation fires the picker twice and discards the first selection (trap 11).
   Drag-and-drop untouched (`ui.ts:253-255`).
2. File rows: name, then paragraphs and words, or the reason the file cannot be used
   (`ui.ts:161-166`). This list is the screen's scroll region.
3. Question, labelled as a question a stranger can answer: "What are you trying to find
   out?", with an example placeholder.
4. Transcripts carried from S3 are labelled as carried, with "Remove all". Never silent.
5. If work is stored: one line saying this run replaces the last result (kind, count, age)
   and does not touch boards already drawn.

Pinned footer: **Run and draw the board**, the cost and time line (`ui.ts:209`), and the
reason it is off when it is off (`ui.ts:241-247`). Panel 440 x 620.

## S3 — Add it: someone's findings

Pasted document first, transcripts second, question third and optional (`ui.ts:206`).

Ruling 2 is already implemented here and stays: a pasted Motif critique report is refused
at paste time, before the button is live (`isVerdictReportPaste`, `ui.ts:222-238`) —
written after a live run structured one, spent, and failed every claim on
`confidence_threshold` before the engine's own guard was deployed. The refusal moves to a
band on the paste box, so it reads as the tool knowing what this is, not as validation.

Pinned footer: **Check it and draw the board**, with the critique cost line (`ui.ts:208`).
Panel 440 x 660; the paste box is the scroll region.

## S4 — Run

One screen for both jobs; this is where they rejoin. Title "Synthesizing" or "Checking"
(`ui.ts:337`), elapsed (`ui.ts:306-314`), job id (`ui.ts:324`), engine log lines as the
scroll region (`ui.ts:342`). New: a line under the title promising step 4 — "then Motif
draws the board on this page" — and a plain statement that closing the panel does not stop
the run. Footer: "Stop watching — the run keeps going" (`ui.ts:374`). Panel 440 x 560.

## Where the board sits

The board is drawn as the last step of the run, not offered as a button afterwards. On
success the plugin fetches the layout (`ui.ts:362`) and posts `build-board` (`code.ts:94`)
while the running screen is still up, then shows the result. Install to board requires no
decision after Run; a board reachable only as one of four peer buttons fails the bar.

- Placement: `board.ts` picks a free origin right of existing content (part3-notes,
  2026-09-05); the main thread zooms to it (`code.ts:100-102`); the result screen's first
  line reports what was drawn, from the `board-done` counts (`code.ts:104`).
- Editor difference stated, not implied: FigJam gets sections, stickies, connectors; Figma
  Design gets sections and frames, no connectors (`ui.ts:574`; part3-notes, 2026-09-05).
- Failure: the result screen still appears, the failure is a band, and **Draw the board**
  becomes the primary action, re-fetching the layout by job id. Today a `getBoard` failure
  inside `finish()` is logged only to a screen the user is about to leave, and
  `#build-board` is disabled with no re-fetch path (trap 9).

## S5 — Result (step 4)

Header: kind and question (`ui.ts:383-384`), then the board line above everything else.

1. **Show me the board** — pinned primary, zooms to the drawn nodes. `code.ts` already
   returns `bounds` with `board-done` (`code.ts:31-32`); `ui.ts`'s copy of the message type
   omits it (`ui.ts:39`), so the data exists and is unused.
2. Tiles and the contested note, content unchanged (`ui.ts:387-421`).
3. The insight or claim list — this screen's scroll region (`ui.ts:435-438`).
4. **Check these findings** (synthesis only; hidden for a critique, `ui.ts:430`), with one
   line: one critic pass over what you just got, against the same transcripts, about $0.35.
   Always enabled, because the transcripts live in the work record now (traps 5 and 7).
   For a critique result this slot holds **Open the synthesis this checked**.
5. **Copy the report**, with the existing clipboard fallback (`ui.ts:538-557`).
6. **Draw the board again** — a plain link once the board is drawn.
7. **Start another** — a plain link at the bottom, carrying the replacement warning.

One primary, one named next step, then quieter things: the fix for four peer actions at
equal strength with no default (trap 2). Panel 440 x 660.

## State: what persists, and what a second run does

| Key | Change |
|---|---|
| `anthropic_key` | unchanged (`code.ts:37`) |
| `last_job` -> `job_in_flight` | same content, new rule below |
| `last_result` -> `work` | single slot becomes a pair |

    work = {
      synthesis:   Run | null,
      critique:    Run | null,      // the check OF that synthesis
      transcripts: [{ name, text }] | null,
      document:    string | null,   // the pasted findings, when work started from findings
      when:        number
    }
    Run = { kind, question, nTranscripts, result, layout, jobId, when,
            board: { drawn, counts, bounds } | null }

- A synthesis run creates a new record. A check launched from a synthesis result attaches
  as `critique`; the synthesis is untouched (ruling 3). Today `finish()` persists to the
  one slot on every successful run of either kind (`ui.ts:366`), so checking destroys what
  it checked (trap 4).
- A findings run from S3 creates a new record with `synthesis: null`, keeping the pasted
  document so what was checked is reopenable.
- Reopening shows the newer half with a labelled route to the other.
- Transcripts persist while their combined text is <= 1 MB. The fifteen-transcript sample
  corpus is 620 KB of processed text (part3-notes, 2026-09-04) and 587 KB through the
  plugin's own extraction (part3-notes, 2026-09-05), so a real corpus fits. Over budget:
  nothing is stored and the Check action says so on its face, not in a `title` attribute
  (`ui.ts:432`). The build session confirms Figma's documented `clientStorage` quota and
  lowers the number if the docs say lower.
- A second submit is impossible while a job is in flight: the run button is disabled with
  "One run at a time — a run is already going", beside Follow it and Forget it. Today
  nothing checks `lastJob` before submitting and `set-last-job` overwrites unconditionally
  (`ui.ts:263`, `ui.ts:277`), orphaning the previous job silently (trap 8).
- A second synthesis replaces the record wholesale, warned on S2 before the run, with the
  note that drawn boards are untouched.

## Failure

The standalone error screen goes. A failure is a band on the screen the attempt was
launched from, carrying the engine's message verbatim (`ui.ts:274`) plus the auth /
billing / unreachable hint when it matches (`ui.ts:124-130`), and a Retry. A failed check
therefore fails on the result screen it was launched from, instead of routing to an error
screen whose Back goes to the form (`ui.ts:570`) and stranding the user with no code path
back (trap 10). The expired-run sentence keeps its wording (`ui.ts:332`); "Silence is never
a result" (`ui.ts:360`) is shown like any other failure.

## Panel height and overflow (defect 12)

Today the panel is fixed at 440 x 660 for every screen (`code.ts:40,50`) and the whole
document scrolls; the `resize` handler (`code.ts:113-114`, floor 320 x 400) has no caller
in `ui.ts`. The harness frames the UI at a height it chooses, so a screen taller than the
panel looks correct there and scrolls silently in Figma.

- Each screen requests its own height by posting `resize`.
- No screen ever requests more than 660, the current default. Screens shrink to content;
  none grows past it.
- No screen scrolls as a whole. Every screen is a fixed frame: header with the step
  indicator, exactly one scroll region, pinned footer holding the primary action. The
  primary action is on screen at every height and every content length.
- Heights: Key 420, Start 440, Add-transcripts 620, Add-findings 660, Run 560, Result 660.
- Scroll regions: file list, paste box, log, insight list. Key and Start have none.

## Widths

Single column throughout. At 440 the indicator shows four numbered chips with labels;
tiles three across; file rows on one line. At 375 the indicator shows numbers with only
the current label; tiles two across; footer buttons stack. At 320 (`code.ts:114`'s floor)
the indicator is numbers only; tiles two across at a smaller numeral; file meta wraps below
the truncated name. The pinned footer never stacks past two rows.

## Defect ledger

| # | Where it closes |
|---|---|
| 1 One form, two jobs, no reset | Two Add screens from Start; `setMode()` gone; carries labelled |
| 2 Four peer actions | One primary, one named next step, then links |
| 3 No position | Four-step indicator on every screen but Key |
| 4 `last_result` one slot | `work` pair; a check attaches, never replaces |
| 5 Check is memory-only | Transcripts persist in `work` |
| 6 `last-card` stale at init | No card; step 4 is the route back, evaluated per render |
| 7 Resume loses transcripts | Check no longer depends on `resultUploads` |
| 8 Silent orphaning | Submit impossible while a job is in flight |
| 9 Board fetch failure, no retry | Draw the board re-fetches by job id from the result screen |
| 10 Failed check strands the user | Failure is a band on the launching screen |
| 11 Picker opens twice | One control opens the picker; `drop.onclick` removed |
| 12 Fixed panel, whole-page scroll | Per-screen height <= 660, one scroll region, pinned footer |

## Open, to be ruled before the build

1. Does the stranger arrive with an Anthropic key and credit? The paid tier is off
   (`/healthz` reports `paid_tier:false`, part3-notes 2026-09-05), so S0 is inside the gate
   unless the observer supplies a key. Changes what the gate measures, not the screens.
2. Does the stranger arrive with transcripts? If not the plugin needs a bundled sample to
   reach a board at all, and the sample corpus is CC-BY-NC (`CONTRIBUTING.md`) — a
   licensing ruling, not a UI one.
3. Drawing the board with no confirming click writes to the user's open file. Designed that
   way because the bar is install-to-board; `board.ts` places it clear of existing content.
   Confirm, or the board becomes one click and the bar becomes install-to-one-click.
