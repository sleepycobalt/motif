# Motif plugin — ETOT chassis restyle spec

*For a Claude Code session in the Motif repo, run on **Claude Sonnet 5**. This is
presentation only: no behavior changes, no copy changes, no DOM restructuring beyond
the two additions named in §7. The four Version 2 UI fixes stay exactly as they are.*

**Files this session touches:** `surfaces/figma/src/ui.html` (the `<style>` block, and
the two markup additions in §7), `surfaces/figma/src/ui.ts` (nothing but the two lines
in §7), `surfaces/figma/src/code.ts` (one option, §2), and the build step for the fonts
(§3). Nothing else.

**Source of truth for every value below:** `etot-site/tokens.json`, version 0.1.0,
updated 2026-09-04. Hex values are copied from it. Where this spec sets a number that
is *not* in `tokens.json` — the panel type scale, spacing, radii — it says so and gives
the reason.

---

## 1. What "on the chassis" means here, and one deviation

The chassis is the ETOT site's CSS: ETOT blue as the only accent, Instrument Serif for
display, Space Grotesk for body, IBM Plex Mono for ids and receipts, hairline rules,
light and dark.

**The deviation, stated up front:** the chassis type scale in `tokens.json` (`body:
17px`, `h1: clamp(56px,9.4vw,124px)`) is written for an 1180 px shell. The plugin panel
is 440 px at its default and 320 px at its narrowest. Those sizes would break the layout
at every width. So the panel takes the chassis's **typefaces, colors, hairlines, and
rules** and uses **its own scale**, defined in §4. This is the only place the panel
departs from `tokens.json`, and it should be recorded in the notes as such.

---

## 2. Theme: follow Figma, not the OS

Figma exposes its own theme to a plugin iframe only when the UI is opened with theme
colors on. In `code.ts`, wherever `figma.showUI` is called, add `themeColors: true` to
the options object. Figma then puts a `figma-dark` class on the iframe's `<html>` when
the editor is in dark mode.

Do not use `prefers-color-scheme` as the primary switch — that follows the OS, and
Figma's theme is set independently of it. Use it only as the harness fallback, since
`test/harness.html` has no Figma parent:

```css
:root { /* light values, §3 */ }
html.figma-dark { /* dark values */ }
@media (prefers-color-scheme: dark) {
  html:not(.figma-light) { /* dark values — harness only */ }
}
```

If `figma.showUI` cannot take the option in the current call shape, stop and report it
rather than working around it; the whole dark theme rests on that class.

---

## 3. Tokens

Declare these once at the top of the `<style>` block. Names match `tokens.json` so the
mapping is checkable by eye.

```css
:root {
  --bg:#ECECEC; --ink:#111111; --ink2:#3A3A3A; --mute:#6E6E6E;
  --hair:#111111; --panel:#F6F6F6; --panel2:#FFFFFF;
  --acc:#0022FF; --accink:#FFFFFF; --red:#E5261F;
  --strip:rgba(17,17,17,.10); --code:#F0F0F0;
}
html.figma-dark {
  --bg:#0A0A0A; --ink:#F2F2F2; --ink2:#C9C9C9; --mute:#8A8A8A;
  --hair:#F2F2F2; --panel:#141414; --panel2:#1B1B1B;
  --acc:#5C79FF; --accink:#0A0A0A; --red:#FF5A4E;
  --strip:rgba(242,242,242,.10); --code:#101010;
}
```

**Never `#0022FF` on the dark panel.** It measures 1.78 : 1 on Figma's dark chrome; that
is why `tokens.json` carries a separate dark accent. `--acc` handles this as long as
nothing hardcodes blue.

**Hairlines carry the identity.** `--hair` is full ink, used at 1 px. Cards, the mode
switch, the drop zone, and the tiles get a 1 px `--hair` border, not a shadow and not a
gray. This is the single change that makes the panel stop reading as a default Figma
plugin.

### Fonts — embed, do not fetch

`manifest.json` allow-lists `https://motif-hosted.fly.dev` and nothing else, and the
published listing's data-security answer says network requests go only there. Loading
Google Fonts would change both, and would add a third-party request to every user's
session.

So: subset the three families to Latin, convert to `woff2`, base64 them into `dist/ui.html`
as `@font-face` `src: url(data:font/woff2;base64,…)` at build time in the esbuild step.
Weights needed: Instrument Serif 400; Space Grotesk 400 and 500; IBM Plex Mono 400 and
500. Keep the fallback stacks from `tokens.json` on every `font-family` declaration.

```css
--serif:'Instrument Serif','Times New Roman',Times,serif;
--sans:'Space Grotesk','Helvetica Neue',Arial,sans-serif;
--mono:'IBM Plex Mono','SFMono-Regular',Consolas,monospace;
```

Report the resulting `dist/ui.html` size. It is 33 KB today; if the embed takes it past
about 400 KB, subset harder (drop unused weights) rather than accepting it silently.

---

## 4. Panel type scale

Panel-specific, not from `tokens.json`. `rem` is avoided — Figma's iframe root size is
not ours to assume.

| Role | Selector | Size / line | Family | Weight | Color |
|---|---|---|---|---|---|
| Screen title | `.top h1` | 26px / 1.15 | serif | 400 | `--ink` |
| Screen title, compact | `.top.compact h1` | 22px / 1.15 | serif | 400 | `--ink` |
| Lede | `.lede` | 14px / 1.45 | sans | 400 | `--ink2` |
| Keyline | `.keyline` | 12px / 1.4 | mono | 400 | `--mute` |
| Card heading | `.card h2` | 13px / 1.3, `letter-spacing:.06em`, uppercase | mono | 500 | `--ink` |
| Body | `p`, `li`, `label` | 13px / 1.5 | sans | 400 | `--ink2` |
| Fine | `.fine` | 12px / 1.45 | sans | 400 | `--mute` |
| Mono inline | `.mono` | 12px / 1.4 | mono | 400 | inherit |
| Insight title | `summary .title` | 13px / 1.35 | sans | 500 | `--ink` |
| Insight id | `summary .id` | 12px | mono | 400 | `--mute` |
| Tile number | `.tile .num` | 22px / 1 | serif | 400 | `--ink` |
| Tile label | `.tile .lbl` | 10px, `letter-spacing:.08em`, uppercase | mono | 400 | `--mute` |
| Log | `.log` | 11.5px / 1.55 | mono | 400 | `--ink2` |
| Quote | `.quote` | 12px / 1.5 | mono | 400 | `--ink2` |

At 320 px, body drops to 12.5px and `.top h1` to 22px; nothing else changes. One media
query at `max-width:360px`.

The card headings are numbered in the markup ("1. Transcripts", "2. Question", "3. Run").
Set them in mono uppercase and the numbering reads as a sequence rather than as headings
that happen to start with digits. Do not change the strings.

---

## 5. Components, one by one

Every selector below already exists in `ui.html` or is generated by `ui.ts`. Nothing new
is invented except where §7 says so.

**`body` / `.app`** — background `--bg`, color `--ink`, font `--sans`, 16px padding
(12px at 320). `-webkit-font-smoothing: antialiased`.

**`.screen`** — flex column, 14px gap.

**`.top`** — `h1` and a lede or keyline. `.top.compact` adds a 1 px `--strip` rule
beneath it with 10px clearance, which is the chassis's header strip at panel scale.

**`.card h2`** — mono 12px, `--ink`, `letter-spacing:.02em`, with an accent section dot
in front: `h2::before{content:"\\25CF  ";color:var(--acc)}`. That is the chassis
`.sechead .n` device. The strings ("1. Transcripts") do not change; the dot is CSS only.

**`.mono`** — the inline code chip, chassis `code` rule: mono `.88em`, background
`--code`, 1 px `--hair` border, padding 0 4px. This covers `Interviewer`, `Researcher`,
`michelle:0042`, and the masked key in the keyline.

**`.card`** — background `--panel`, 1 px `--hair` border, radius 4px, padding 12px, 8px
internal gap. **Keep `display:flex; flex-direction:column`, and keep
`[hidden]{display:none!important}`.** That rule is load-bearing: without it the resume
card shows on every first open. It is the stage-2 harness bug; do not lose it in a
rewrite of the block.
- `.card.notice` — left border 3px `--acc`, otherwise the same.
- `.card.error` — background `--panel2`, left border 3px `--red`; `#error-text` in
  `--mono` 12px, `--ink2`, `overflow-wrap:anywhere`. The engine's message must stay
  legible and unstyled beyond that; it is quoted verbatim by design.
- `.card.grow` — `flex:1 1 auto; min-height:0` so the log can scroll inside it.

**`.field`** — label `span` in mono 11px uppercase `--mute`, 4px above the control.
`input`, `textarea`: background `--panel2`, 1 px `--hair` border, radius 3px, padding
8px 10px, font `--sans` 13px, color `--ink`. `::placeholder` `--mute`. `textarea`
`resize:vertical`. `#key-input` and `#document` take `--mono` instead, since both hold
machine text.

**Focus** — one rule for every interactive element: `outline:2px solid var(--acc);
outline-offset:2px`, on `:focus-visible` only. Remove any default Figma-blue focus ring.

**`.primary`** — background `--acc`, color `--accink`, no border, radius 3px, padding
9px 14px, font `--sans` 13px/500. `:hover` 92% opacity. `:disabled` background `--acc`
at 35% opacity with `--accink` text, `cursor:not-allowed`. `.primary.wide` is full width.

**`.ghost`** — transparent background, 1 px `--hair` border, `--ink` text, same metrics
as `.primary`.

**`.link`, `.textbtn`, `.filebtn`** — `--acc` text, underline with `text-underline-offset:2px`,
no background. `.filebtn` keeps its hidden file input.

**`.modes`** — a two-up switch, 1 px `--hair` border, radius 3px, no gap between the two
buttons, a 1 px `--hair` divider between them. `.mode` transparent, `--ink2`, mono 12px.
`.mode.on` background `--acc`, color `--accink`. This replaces the purple pill.

**`.drop`** — background `--panel2`, 1 px dashed `--hair` at 45% opacity, radius 3px,
padding 18px, centered, `--mute` text. `.drop.over` — border solid `--acc`, background
`--panel2`, and that is all: no scale or shadow.

**`.files`** — list, no bullets. Each `li` is a 3-column grid (`1fr auto auto`), 8px gap,
9px vertical padding, 1 px `--hair` bottom border at 20% opacity, last child none.
`.name` sans 13px `--ink`, `text-overflow:ellipsis`. `.meta` mono 11px `--mute`,
`font-variant-numeric:tabular-nums`. `.meta.bad` color `--red`. `.rm` is a 20px square
ghost button, `--mute`, `--red` on hover.

**`.tiers`** — `fieldset`, no border, no padding, row with 16px gap. `.tier` label row,
sans 13px. Set `accent-color: var(--acc)` on the radios so the dot is ETOT blue, not
Figma blue. `.tier.disabled` stays hidden as it is; do not unhide it.

**`.log`** — the chassis `.term` rule: mono 12px/1.55, background `--code`, padding
14px 16px, color `--ink2`, and **no border** — the code background is the whole device.
Two panel deviations, both stated: `white-space:pre-wrap` with `overflow-wrap:anywhere`
instead of the site's `pre` plus horizontal scroll, because a 320 px panel cannot scroll
sideways usefully; and `overflow-y:auto` with `max-height:260px`. At 320 the chassis
already drops to 11px with 12px padding — match that. Nothing animated. The log is the
one place the panel should look like a machine talking.

**`.tiles`** — built exactly like the chassis `.stats` grid: a 1 px `--hair` border
around the whole block, background `--panel2`, children carrying right and bottom
`--hair` borders with `margin:0 -1px -1px 0` so the rules collapse, and `overflow:hidden`
on the container. No gap. Column count from the existing `data-n`: 5 tiles at 440 is
`repeat(5,1fr)`; at 375 and 320 use `repeat(3,1fr)` and let it wrap. Verdict results
render 6 tiles — handle `data-n="6"` as `repeat(3,1fr)` at every width. Do not change how
`ui.ts` sets `data-n`.

**`.tile`** — padding 10px 8px, centered, `.num` above `.lbl`. The number is serif in
`--acc`, which is what `.stats b` does on the site. `.tile.warn .num` is `--red`.
That follows the chassis ledger convention — `.ledger b` is red for an open item and
`.ledger b.ok` is accent for a closed one — so a contested count and a FAIL verdict read
as open, not as an amber alarm.

**`.insight`** (`details`) — background `--panel`, 1 px `--hair` border, radius 3px.
`summary` is a grid (`auto 1fr auto`), 8px gap, 10px 12px padding,
`cursor:pointer`, `list-style:none` plus `::-webkit-details-marker{display:none}`, and a
chevron drawn with a CSS triangle in `--mute` that rotates on `[open]`. `.body` padding
0 12px 12px, 6px gap, 1 px `--strip` top rule.

**`.badge`** — the confidence chip. This is the chassis `.conf` rule, unchanged:
`display:inline-block`, 1 px `--hair` border, mono 11px, padding 1px 7px, no radius.
The chassis has two states, not four, so the panel has two:
- `.badge.high` — background `--acc`, color `--accink`, border-color `--acc`. This is
  `.conf.hi` exactly.
- `.badge.medium`, `.badge.low` — the default outline. Text color `--ink` for medium,
  `--mute` for low. That one-token difference is the only extension, and it is needed
  because the panel shows both states side by side in a list where the site shows one
  at a time.
- `.badge.contested` — the chassis `.flag` colors on the chip shape: 1 px `--red`
  border, `--red` text, transparent background. Lowercase, as `ui.ts` writes it.

Do not invent an accent-outlined middle state; the chassis does not have one.

Keep the chip's `title` attribute and its `low · 1 of 2` text exactly as `ui.ts`
generates them. That wording came from Eric's stage-2 Figma run and is not up for
restyling.

**`.quote`** — the receipt, and this is the chassis `.rcpt` rule: mono 12.5px/1.5,
background `--code`, `border-left:2px solid var(--acc)`, padding 6px 10px, margin 6px 0,
`overflow-wrap:anywhere`. Note the background is `--code`, not `--panel2`. On the site
the turn id is set in `--acc` (`.rcpt .id`); here the id and the quote arrive from
`ui.ts` as one string, so the whole line takes `--ink2` and the accent stays on the left
rule. Do not split the string to color the id.

Counter-evidence on the site is `.rcpt.ctr`, the same block with
`border-left-color:var(--mute)`. `ui.ts` currently renders `counter_note` as a `.fine`
paragraph, not as a receipt, so there is nothing to restyle — leave it as `.fine` and do
not reach into `ui.ts` to change it.

**`.opp`** — the chassis has no opportunity component. Panel-only, and marked as such:
sans 12px, `--ink2`, `border-left:2px solid var(--hair)`, padding-left 10px. Full ink
rather than accent or mute, so it sits clear of the receipt (accent) and the counter
(mute).

**`.flags`** — the chassis `.flag` rule: `display:block`, 1 px `--red` border, `--red`
text, mono 11px/1.5, padding 6px 9px, margin-top 8px, `overflow-wrap:anywhere`. A
bordered block, not a line of red text.

**`.clip`** — the copy-fallback textarea. Background `--code`, 1 px `--hair` border, mono
11.5px, `--ink2`, full width, `resize:vertical`.

**`#critic-notes`** — reuses `.insight`; no separate rule.

**`.visually-hidden`** — keep whatever clip-rect implementation is there. Do not
replace it with `display:none`.

---

## 6. Motion

`transition: background-color .12s, border-color .12s, opacity .12s` on buttons and the
mode switch. Nothing else animates. Wrap the lot in
`@media (prefers-reduced-motion: reduce) { *{transition:none!important} }`.

---

## 7. The only two markup/script additions

Both are presentational and neither changes a code path.

1. **A theme class hook.** If `code.ts` cannot supply `themeColors`, add nothing and
   report; do not invent a toggle. The panel has no theme control of its own — it
   follows Figma, per the brief.
2. **`summary` chevron.** Pure CSS on `summary::after`. No element added, no listener.

If applying this spec seems to need any other markup change, stop and report it instead.

---

## 8. QA gate

Nothing is reported as done until all of this has run and its counts are in the notes.

1. `test/harness.html` at **440, 375, and 320 px**, in **both themes** (add
   `?harness&theme=dark` or set the class by hand in the harness page — harness-only,
   not shipped), across **every screen**: key; setup with two transcripts added; setup
   in critique mode with a report pasted; setup with the run button disabled and the
   `#run-why` line showing; running with ingest lines in the log; result from a stored
   synthesis, collapsed and with insights expanded; result from a stored verdict with
   objections open; the copy-fallback box revealed; error with the hint.
2. For each: element rectangles against the viewport, `scrollWidth` against
   `clientWidth`, and page horizontal scroll. **Zero issues at every width in both
   themes** is the bar, the same one stage 2 and stage 3 met.
3. **The resume-card check.** Open the harness with no run in flight and confirm the
   "A run is still going from last time" card is not visible. This is the bug the
   `[hidden]` rule fixes and the one most likely to come back in a CSS rewrite.
4. **Fonts render offline.** Load the harness with the network disabled and confirm
   Instrument Serif, Space Grotesk, and IBM Plex Mono all render — not the fallbacks.
5. **Contrast**, computed not eyeballed, on both themes: `--ink` on `--panel`, `--ink2`
   on `--panel`, `--mute` on `--panel`, `--accink` on `--acc`, `--acc` on `--panel`,
   `--red` on `--panel`. Report each ratio. Anything under 4.5 : 1 for body text or
   3 : 1 for the chips is a failure, not a note.
6. Screenshots of every screen at every width in both themes into
   `docs/exhibits/stage4-restyle/`, **cropped to the panel**, no menu bar, no tabs, no
   clock, no avatar, no key fragment. Raw captures do not enter the repo.
7. `dist/ui.html` size reported before and after.
8. The Figma run itself is Eric's, not this session's: development plugins load only in
   the desktop app, so the panel in Figma at both themes is a hand check, logged in
   `docs/part3-notes.md` before the restyle is called done.

## 9. Notes and log

Append to `docs/part3-notes.md` as you go — one dated line per decision, surprise,
failure, or number, with the file path for every number — and a dated tried / happened /
next entry to `docs/log.md`. Commit in the Motif repo only.

---

## 10. Reconciliation — done

`etot-site/chassis.py` was read and it wins over `tokens.json` wherever the two differ.
It changed five things above, all now folded in: the receipt background is `--code` not
`--panel2`; the terminal block has no border; the confidence chip has two states rather
than four; the critic's objections are a bordered red block, not red text; and the tile
numbers are serif accent with red for the open ones, on the ledger convention.

Three panel-only extensions remain, each stated where it appears: the `medium`/`low`
text-color split on the chip, the `.opp` rule the chassis has no component for, and the
log's wrapping. Record those three in the notes as deviations, with this reason: the
panel shows in one column, at 320 px, what the site shows across an 1180 px page.
