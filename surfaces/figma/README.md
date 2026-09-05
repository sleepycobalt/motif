# Motif for Figma

A Figma Community plugin (FigJam and Figma Design) that turns interview
transcripts into a Motif synthesis without a terminal, and draws it on the
board. Free tier: your own Anthropic key. Paid credits: designed, not switched
on.

Two modes. **Synthesise transcripts** runs the full loop and returns insights
with receipts, confidence, counter-evidence, and any objection the critic still
holds. **Check a synthesis** runs the critic alone over a pasted report or
summary against the transcripts and returns its verdict, claim by claim.
Either result can be copied as Markdown or built on the board: in FigJam, one
section per insight with colour-coded stickies (claim by confidence, white
receipts, pink counter-evidence wired to the claim by "contested by"
connectors, blue opportunity, violet open objections) and a run card above the
grid; in Figma Design, the same sections with frames instead of stickies and
no connectors. The last result stays on the device, so the board can be built
later even after the run has expired on the engine.

The plugin is a thin client of the hosted engine (`surfaces/hosted/`): it
extracts paragraphs from `.docx` files in the browser (no library; see
`src/docx.ts`), uploads text, follows the run's progress, and shows the result.
The key lives in Figma's client storage on your device and travels only in the
request header of a run.

## Layout

```
manifest.json          Figma manifest (editor types, network allow-list)
src/code.ts            main thread: client storage, notifications, window size
src/ui.ts              the UI iframe: screens, files, the run
src/api.ts             hosted-engine client: submit, follow events, fetch result and board layout
src/board.ts           the board writer (FigJam stickies and connectors; Design frames), run card
src/docx.ts            .docx -> paragraphs, in the browser
src/ui.html, ui.css    the UI
build.mjs              esbuild -> dist/code.js and a single-file dist/ui.html
test/docx_parity.mjs   plugin extraction vs python-docx through the engine's ingest
test/board_render.mjs  the board writer against a fake Figma API, both editors, failure paths
test/board_script.mjs  bundles the board writer for Figma's MCP use_figma (real-board check)
test/harness.html      the UI framed at 440, 375, and 320 px
```

## Build

```bash
cd /path/to/motif/surfaces/figma
npm install
npm run typecheck
npm run build          # writes dist/code.js and dist/ui.html
npm test               # docx parity against python-docx on the sample corpus (needs ../../.venv)
node test/board_render.mjs   # board writer with a fake Figma API
```

## Run it in Figma (development build)

1. Build, as above.
2. Open the Figma desktop app. Create a new FigJam file (or open a Design file).
3. Menu → Plugins → Development → **Import plugin from manifest…** and choose
   `surfaces/figma/manifest.json`.
4. Menu → Plugins → Development → **Motif**.
5. Paste your Anthropic key once (it is stored by Figma on this device).
6. Drop transcripts (.docx, .txt, .md; one speaker turn per paragraph,
   `Name: text`), type the research question, click **Synthesise**.
7. Follow the progress; the result screen lists every insight with its
   confidence (and how many of the transcripts back it), first receipts,
   counter-evidence, and any critic objection still open. **Build board**
   draws it on the current page and zooms to it; **Copy report** puts the
   Markdown on the clipboard.
8. To check someone else's synthesis instead, switch to **Check a synthesis**,
   paste the text, add the transcripts it should rest on, and run.

Closing the window does not stop the run; the plugin offers to follow it again
next time it opens (results stay on the engine for an hour after they finish).

## Check the UI outside Figma

`dist/ui.html` also runs in a plain browser tab, with `localStorage` standing
in for Figma's client storage. From the repository root:

```bash
python3 -m http.server 8788 --bind 127.0.0.1
# key screen
open "http://127.0.0.1:8788/surfaces/figma/dist/ui.html"
# setup screen with two sample transcripts loaded
open "http://127.0.0.1:8788/surfaces/figma/dist/ui.html?files=/data/raw/Dataset-2/Michelle.docx,/data/raw/Dataset-2/David.docx"
# result screen from a recorded run
open "http://127.0.0.1:8788/surfaces/figma/dist/ui.html?demo=/docs/exhibits/stage1-remote-qa/synthesize-result.json"
```

The hooks after `?` only work outside Figma. `test/harness.html?u=<one of the URLs above>` frames
the same page at 440, 375, and 320 px for the width check.

## QA gate (from the spec)

Install to run-start in a fresh FigJam file in under ten minutes on the free
tier (a run itself takes about twelve minutes on two transcripts); every screen
checked for clipped or overflowing elements at desktop and phone widths.
First measured run, 2026-09-05: 8 m 20 s to run-start, 12 m 33 s run, copy to
clipboard works inside Figma. Results are logged in `docs/part3-notes.md`.
