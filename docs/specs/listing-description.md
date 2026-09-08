# Motif — Figma Community description (rewrite, 2026-09-08)

*Register: html.to.design's how-to listing — a headline, arrow links up top, question
headings with numbered steps, an FAQ, links again at the end. Every factual claim is
carried over from `surfaces/figma/listing.md` unchanged. American English. Written
against Version 2 (published 2026-09-08), so "Start another" and the one-click
"Check this synthesis" are live.*

---

## Tagline (one line, unchanged)

Research synthesis that shows what survived.

---

## Description

**Motif reads your interview transcripts, writes the findings, then tries to knock
them down — and shows you what survived.**

Every insight comes with its receipts: the exact turns it rests on, quoted verbatim,
with the participant's name and turn number. Every insight carries a confidence level
defined by numbers, not adjectives. Every insight lists the counter-evidence against
it. And when Motif's critic still disagrees with a finding after three rounds, the
finding is marked contested instead of being quietly dropped. Silence is never
agreement.

→ **Motif** — https://etot.design/tools/motif/
📖 **Case study** — https://etot.design/tools/motif/case-study/
⌨️ **Source and method** — https://github.com/sleepycobalt/motif (MIT)
✉️ **Support** — hello@etot.design

### How do I synthesize a set of transcripts?

1. Open Motif in a FigJam board or a Figma Design file.
2. Paste your Anthropic API key the first time. Figma keeps it on your device.
3. Add your transcripts — `.docx`, `.txt`, or `.md`, one speaker turn per paragraph,
   written as `Name: what they said`.
4. Type your research question and run. About twelve minutes for two transcripts.

You get 8 to 16 insights. Each one has a claim, its receipts, a confidence level, the
counter-evidence against it, and a design opportunity a team can act on.

### How do I check a synthesis?

1. Paste a report or summary — yours, a colleague's, or one an AI wrote.
2. Add the transcripts it claims to rest on.
3. Run the check. You get a verdict, claim by claim.

Motif's critic asks of every claim: do the cited turns exist, do the quotes match, is
the interviewer being cited as evidence, is there dissent the claim ignores, does the
confidence overreach.

On a synthesis Motif just produced, **Check this synthesis** reuses that run's
transcripts, so there is nothing to add again.

### How do I build the board?

One click draws the result on the page:

- a section per insight
- the claim colored by confidence
- white receipt stickies, each with its turn ID
- pink counter-evidence, wired to the claim by a "contested by" connector
- a blue opportunity
- a violet sticky for any objection the critic still holds

A run card above the grid records the question, the corpus, the cost, and the time. In
Figma Design the same board is drawn with frames.

### What is a receipt?

A receipt is a verbatim quote from a numbered turn, `michelle:0042`, that you can check
against the transcript in seconds. Motif's critic does that check in code before the
model ever weighs in: a quote that is not in the cited turn fails; a turn that belongs
to the interviewer fails; a claim with no citation fails. The model-judged checks come
after: unsupported claims, missing dissent, overconfidence, merged findings. What the
critic still objects to when the loop stops is shown as contested, on the result screen
and on the board, so you read those findings with the objection in view.

### What Motif does not do

Motif does not decide what is true. It shows you what each finding rests on and what
argues against it, and it refuses to hide a disagreement. The reading is still yours.

---

## FAQ

**Do I need an API key?**
Yes, your own Anthropic key. Paste it once; Figma stores it on your device
(`figma.clientStorage`). It travels only with a run, in a request header to Motif's
hosted engine, which uses it for that run's model calls and then drops it. ETOT never
sees, stores, or logs your key. Get one at console.anthropic.com.

**What does a run cost?**
Runs are billed to your Anthropic key, not to ETOT. About $1 for two transcripts, about
$5 for fifteen. The result screen shows the exact API cost of every run.

**How long does it take?**
About twelve minutes for two transcripts on the full loop — intake, synthesis, critic,
revise, up to three rounds. A critique-only check of a pasted synthesis takes a few
minutes. You can close the plugin; the run continues, and the plugin offers to pick it
up next time.

**What happens to my transcripts?**
They are processed for the run and then discarded. The hosted engine keeps the
processed transcripts only while the run is in progress and for one hour afterwards, so
the plugin can fetch receipts and the board layout, then deletes them. What remains on
the engine is a redacted run record: token counts, timings, cost, and the critic's
verdicts, with prompt and response bodies stored as lengths and hashes, never as text.
That record is deleted 30 days after the run. This was checked on the live server, not
just in code. Your last result and its board layout stay on your device so you can
build the board later.

**What format do transcripts need?**
One speaker turn per paragraph, each starting with the speaker's name and a colon.
Label the interviewer `Interviewer`, `Researcher`, or `Moderator` so their turns are
never cited as evidence. Word files are read in the plugin; only the text is uploaded.

**Can I change the rules the critic uses?**
Not in the plugin. The rules are plain language and live in the open-source engine's
config; teams that run Motif from the repo can edit them.

**Is there a paid version?**
Not yet. Everything here runs on your own key. A paid tier with ETOT-provided credits
follows in a later release.

---

## Links

- Motif — https://etot.design/tools/motif/
- Case study — https://etot.design/tools/motif/case-study/ and
  https://ericfrye.info/ui/ux/motif
- Source and method — https://github.com/sleepycobalt/motif (MIT)
- Support — hello@etot.design (we reply within two working days)
- Privacy policy — https://etot.design/privacy/

---

## Notes on what changed from the live text

- Restructured into question headings with numbered steps, which is the html.to.design
  shape. The three modes are now three "How do I…" sections rather than a numbered list
  inside one block.
- Links moved to the top as well as the bottom. html.to.design puts them directly under
  the headline, and they are the first thing a reader acts on.
- "Three ways to use it" as a label is gone; the three headings do that work.
- Added the one-click **Check this synthesis** step, live since Version 2.
- The receipts paragraph, the "what it is not" paragraph, and every FAQ answer carry
  over unchanged except for splitting the cost and time answers out ahead of privacy,
  since those are the two questions a reader has before they install.
- No claim here is new. Anything that reads as new is a sentence from `listing.md` that
  moved.
