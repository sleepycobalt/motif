# Motif for Figma

A Figma Community plugin (FigJam and Figma Design) that turns interview
transcripts into a Motif synthesis without a terminal. Free tier: your own
Anthropic key. Paid credits: designed, not switched on. The board writer
arrives in the next release; this release returns the synthesis in the plugin
and as Markdown.

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
src/api.ts             hosted-engine client: submit, follow events, fetch
src/docx.ts            .docx -> paragraphs, in the browser
src/ui.html, ui.css    the UI
build.mjs              esbuild -> dist/code.js and a single-file dist/ui.html
test/docx_parity.mjs   plugin extraction vs python-docx through the engine's ingest
```

## Build

```bash
cd /path/to/motif/surfaces/figma
npm install
npm run typecheck
npm run build          # writes dist/code.js and dist/ui.html
npm test               # docx parity against python-docx on the sample corpus (needs ../../.venv)
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
   confidence, sources, first receipts, counter-evidence, and any critic
   objection still open. **Copy report** puts the Markdown on the clipboard.

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

Install to result in a fresh FigJam file in under ten minutes on the free
tier; every screen checked for clipped or overflowing elements at desktop and
phone widths. Results are logged in `docs/part3-notes.md`.
