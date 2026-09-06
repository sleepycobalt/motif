# Motif — Figma Community listing (submitted 2026-09-06, awaiting review)

Copy for the Figma Community page as submitted on 2026-09-06 00:31 CDT under
the ETOT team profile @etot, plugin id 1678295978273812914 (manifest, commit
7cd99fd). Free tier only: the plugin runs on the user's own Anthropic key.
Numbers are the plugin's own words or come from the files named in
`docs/part3-notes.md`. Listing link: pending (to be recorded on approval).

## Name

**Motif** — by ETOT

## Tagline (one line)

Research synthesis that shows what survived.

## Category

Design tools › Content generation. The spec's "Research / Whiteboarding" does
not exist in Figma's plugin taxonomy (the Whiteboarding entries are
templates); this is the nearest category offered.

## Editor types

FigJam · Figma Design

## Description

Drop your interview transcripts on the board. Motif reads them, writes the
findings, then tries to knock them down — and shows you what survived.

Every insight comes with its receipts: the exact turns it rests on, quoted
verbatim, with the participant's name and turn number. Every insight carries
a confidence level defined by numbers, not adjectives. Every insight lists
the counter-evidence against it. And when Motif's critic still disagrees with
a finding after three rounds, the finding is marked contested instead of
being quietly dropped. Silence is never agreement.

**Three ways to use it**

1. **Synthesise transcripts.** Add `.docx`, `.txt`, or `.md` files (one
   speaker turn per paragraph, `Name: what they said`), type the research
   question, run. About twelve minutes for two transcripts. You get 8 to 16
   insights, each with claim, receipts, confidence, counter-evidence, and a
   design opportunity a team can act on.
2. **Check a synthesis.** Paste a report or summary — yours, a colleague's, or
   one an AI wrote — with the transcripts it claims to rest on. Motif's critic
   checks every claim: do the cited turns exist, do the quotes match, is the
   interviewer being cited as evidence, is there dissent the claim ignores,
   does the confidence overreach. You get a verdict, claim by claim.
3. **Build the board.** One click draws the result on the page: a section per
   insight, the claim coloured by confidence, white receipt stickies, pink
   counter-evidence wired to the claim by a "contested by" connector, a blue
   opportunity, and a violet sticky for any objection the critic still holds.
   A run card above the grid records the question, the corpus, the cost, and
   the time. In Figma Design the same board is drawn with frames.

**Receipts and contested, in one paragraph**

A receipt is a verbatim quote from a numbered turn, `michelle:0042`, that you
can check against the transcript in seconds. Motif's critic does that check
in code before the model ever weighs in: a quote that is not in the cited
turn fails; a turn that belongs to the interviewer fails; a claim with no
citation fails. The model-judged checks come after: unsupported claims,
missing dissent, overconfidence, merged findings. What the critic still
objects to when the loop stops is shown as contested, on the result screen
and on the board, so you read those findings with the objection in view.

**What it is not**

Motif does not decide what is true. It shows you what each finding rests on
and what argues against it, and it refuses to hide a disagreement. The
reading is still yours.

## FAQ

**Do I need an API key?**
Yes, your own Anthropic key. Paste it once; Figma stores it on your device
(`figma.clientStorage`). It travels only with a run, in a request header to
Motif's hosted engine, which uses it for that run's model calls and then
drops it. ETOT never sees, stores, or logs your key. Get one at
console.anthropic.com.

**What happens to my transcripts?**
They are processed for the run and then discarded. The hosted engine keeps
the processed transcripts only while the run is in progress and for one hour
afterwards so the plugin can fetch receipts and the board layout, then deletes
them. What remains on the engine is a redacted run record: token counts,
timings, cost, and the critic's verdicts, with prompt and response bodies
stored as lengths and hashes, never as text, and that record is deleted 30
days after the run. This was checked on the live server, not just in code:
see `docs/part3-notes.md`, 2026-09-05, "Privacy check on the volume itself"
and the retention sweep entry. Your last result and its board layout stay on
your device so you can build the board later.

**What does a run cost?**
Runs are billed to your Anthropic key, not to ETOT. In the plugin's own
words: about $1 for two transcripts, about $5 for fifteen. The result screen
shows the exact API cost of every run.

**How long does it take?**
About twelve minutes for two transcripts on the full loop (intake, synthesis,
critic, revise, up to three rounds). A critique-only check of a pasted
synthesis takes a few minutes. You can close the plugin; the run continues,
and the plugin offers to pick it up next time.

**What format do transcripts need?**
One speaker turn per paragraph, each starting with the speaker's name and a
colon. Label the interviewer `Interviewer`, `Researcher`, or `Moderator` so
their turns are never cited as evidence. Word files are read in the plugin;
only the text is uploaded.

**Can I change the rules the critic uses?**
Not in the plugin. The rules are plain-language and live in the open-source
engine's config; teams that run Motif from the repo can edit them.

**Is there a paid version?**
Not yet. Everything here runs on your own key. A paid tier with ETOT-provided
credits follows in a later release.

## Links

- Motif: https://etot.design/tools/motif/
- Case study: https://etot.design/tools/motif/case-study/ and https://ericfrye.info/ui/ux/motif
- Source and method: https://github.com/sleepycobalt/motif (MIT)
- Support: hello@etot.design (we reply within two working days)
- Privacy policy: https://etot.design/privacy/

## Tags (Figma caps at five)

ux research, research synthesis, user interviews, transcripts, affinity mapping

## Assets

- Icon: `surfaces/figma/listing/icon.png`, 128 × 128, in place. Per ETOT's
  per-tool identity rule each tool's icon is its own generated field, one
  colour, no letterform; the monogram is reserved for the studio. Generated by
  `etot-site/scripts/icons.py` (commit 23c596d) from `etot-site/assets/icons/motif-128.png`;
  the system is `etot-internal/brand/icon-system-spec.md` (a272fd2+).
- Cover: `surfaces/figma/listing/cover.png`, 1920 × 960, in place. Composited
  by the hub from `docs/exhibits/stage3-plugin/08-board-I-01-contested-zoom.png`
  (the I-01 section of run `20260905-221749-C-hosted`, drawn by the plugin),
  cropped to the section and letterboxed on the FigJam canvas grey `#F5F5F5`.
  A screenshot-derived cover, not a canvas export: the boards were deleted
  before a canvas export was made. This replaces the spec's I-09 choice, whose
  only exhibit is the part-2 MCP-drawn board.
- Thumbnail: `surfaces/figma/listing/cover.png` (above).
- Carousel: `surfaces/figma/listing/carousel/01-board-overview.png`,
  `02-sections.png`, `03-result-screen.png`, `04-verdict.png`,
  `05-design-editor.png`, 1920 × 960 each, prepared by the hub from exhibits
  `docs/exhibits/stage3-plugin/` 11, 12, 04, 21, and 14 by cropping to the
  plugin panel and canvas and letterboxing on the canvas colour. The raw
  exhibits carry the menu bar, browser tabs, clock, and avatar and are never
  published as they are.

## Version notes (first release)

Motif 0.3: synthesise transcripts, check a synthesis, build the board.
FigJam and Figma Design. Bring your own Anthropic key. The Credits control is
hidden in this build; a paid tier with ETOT-provided credits follows in a
later release (the code path stays behind the server's `MOTIF_PAID_ENABLED`
flag).

## Data security (as answered in the publish form, 2026-09-06)

- Backend: a hosted backend that receives no plugin-API data (document
  contents never leave Figma; the plugin sends only the user's uploaded
  transcripts, question, and pasted text).
- Network requests: only to `motif-hosted.fly.dev`.
- User authentication: none.
- Plugin-API data stored: none.
- Team: solo developer.
- Vulnerability process: no formal process yet; reports via GitHub issues or
  hello@etot.design.
- Accreditation: none.

## Settings as submitted

Comments on. Support contact hello@etot.design. Privacy policy
https://etot.design/privacy/. Two-factor authentication required by Figma for
publishing; the Figma session had to be restarted after enabling it.

## Status

Submitted 2026-09-06 00:31 CDT, awaiting review. The plugin id in
`manifest.json` is the one Figma assigned at first publish (a first generated
id was superseded; the second is in commit 7cd99fd).

The privacy policy page is live at https://etot.design/privacy/ (etot-site
698104c, 2026-09-06) and linked above; it is no longer a blocker.
