# Motif — Figma Community listing (draft, not submitted)

Copy for the Figma Community page. Free tier only: the plugin runs on the
user's own Anthropic key. Numbers are the plugin's own words or come from the
files named in `docs/part3-notes.md`. Review before submission; submission is
a separate session.

## Name

**Motif** — by ETOT

## Tagline (one line)

Research synthesis that shows what survived.

## Category

Research (primary) · Whiteboarding

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
stored as lengths and hashes, never as text. This was checked on the live
server, not just in code: see `docs/part3-notes.md`, 2026-09-05, "Privacy
check on the volume itself". Your last result and its board layout stay on
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
- Privacy policy: [privacy URL]

## Tags

research, ux research, user interviews, synthesis, transcripts, qualitative,
citations, evidence, affinity mapping, whiteboard

## Assets

- Icon: `surfaces/figma/listing/icon.png`, 128 × 128, in place. Per ETOT's
  per-tool identity rule each tool's icon is its own generated field, one
  colour, no letterform; the monogram is reserved for the studio. Generated by
  `etot-site/scripts/icons.py` (commit 23c596d) from `etot-site/assets/icons/motif-128.png`;
  the system is `etot-internal/brand/icon-system-spec.md` (a272fd2+).
- Cover: the recorded run's I-09 section, `docs/exhibits/recorded-run/board-I-09-contested.png`
  (the spec's choice; from the 2026-09-04 recorded run, drawn through the MCP
  `motif_board` scripts, same layout as the plugin draws).
- Screenshots, in order:
  1. Board overview: `docs/exhibits/stage3-plugin/11-fresh-file-board-overview.png`
     (the synthesis board alone on a fresh file; 06 also shows the verdict
     board beside it if two boards are wanted in one frame).
  2. Contested section: `docs/exhibits/stage3-plugin/08-board-I-01-contested-zoom.png`.
  3. Plugin UI: `docs/exhibits/stage3-plugin/04-synthesis-result-before-board.png`.
  4. Critique verdict: `docs/exhibits/stage3-plugin/21-critique-verdict-board-built.png`
     (post-fix Check-a-synthesis on the live plugin path, 2026-09-05: FAIL,
     16 claims, 2 fails, 0 warnings, board built beside the synthesis board).
     `01-critique-verdict-prefix-panel-and-board.png` is the pre-fix run (six
     `quote_mismatch` fails that no longer occur) and must not be used.
  Optional fifth: `docs/exhibits/stage3-plugin/14-design-board-built-overview.png`
  for Figma Design.

## Version notes (first release)

Motif 0.3: synthesise transcripts, check a synthesis, build the board.
FigJam and Figma Design. Bring your own Anthropic key. The Credits control is
hidden in this build; a paid tier with ETOT-provided credits follows in a
later release (the code path stays behind the server's `MOTIF_PAID_ENABLED`
flag).

## Blockers before submission

1. Real plugin `id` in `manifest.json`, assigned by Figma at first publish.
2. A 1920 × 960 cover (the icon is in place).
3. Privacy policy page on etot.design; replace `[privacy URL]` above. Last
   blocker: the page is an etot-site session.
