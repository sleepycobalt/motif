# Motif, part 3 — the plugin as product

*Draft copy for the ETOT chassis page (`motif-build-part3.py`), written 2026-09-06 from `docs/part3-notes.md`. Every number and quote below is copied from a dated line in that file; the line's own file paths are carried through so the build session can re-read them. Figures are named by exhibit path only — the build session places them.*

---

## Brackets left open in this draft

1. `[not in notes: Community review outcome and date]` — the listing was submitted 2026-09-06 00:31 CDT; the notes record no decision.
2. `[not in notes: first 10 installs — count, dates, source]`
3. `[not in notes: first 3 pieces of feedback]`
4. `[not in notes: first Fly.io invoice — amount, period, date]` — the 2026-09-05 line says the cost line comes "once the first invoice arrives".
5. `[not in notes: LLC — entity name, state, filing and formation dates]` — the notes record only that filing has started (single-member).
6. `[not in notes: exhibit path for the privacy-test failure]` — the failing `test_synthesize_job_end_to_end` output and the `fly ssh console` volume read are recorded in the notes as text, with no exhibit file. The hero is therefore drafted as a terminal block, not an image; if the build session wants an image, the output has to be re-captured and saved under `docs/figures/` per the new screenshot rule.
7. `[not in notes: total part-3 API spend]` — part 1 closed with a project total ($30.84, `docs/case-study-notes.md` 2026-09-03); no equivalent sum for part 3 exists in `docs/part3-notes.md`, and adding the individual run costs would be reconstruction.
8. `[not in notes: part 2 case-study URL on etot.design / ericfrye.info]` — the notes record `/tools/motif/` and `/tools/motif/case-study/` for the tool and part 1, not a part-2 path.
9. `[not in notes: Blossom pricing]` — recorded as unverifiable from outside (2026-09-06): no dollar amount anywhere on the site, calls to action are "Start free trial" and "Request a demo".

---

## Spec card

```
ETOT
TOOL · RESEARCH SYNTHESIS · PART 3

Motif

type      Figma / FigJam plugin
version   0.3
surface   FigJam · Figma Design
author    Eric Frye
date      09.2026
license   MIT
part 1    the loop            → /tools/motif/case-study/ · /ui/ux/motif
part 2    the critic anywhere → [not in notes: part 2 case-study URL]

Launch listing ↗   https://www.figma.com/community/plugin/1678295978273812914
```

*Listing link and plugin id: notes 2026-09-06 ("Listing link"); the id is the one Figma assigned at first publish, in `surfaces/figma/manifest.json`, commit `7cd99fd`.*

---

## Nav (section dots)

`01 · The service` `02 · The privacy test` `03 · The tiers` `04 · Three gates` `05 · The board` `06 · The round trip` `07 · The listing` `08 · What it costs` `09 · Still open`

---

## Hero

### H1

**A privacy property is a test, not a sentence.**

### Dek

Part 1 built the loop. Part 2 gave it a server. Part 3 makes it something a designer can install: a hosted engine that runs on the user's own key, a Figma and FigJam plugin that draws the result on the board, and a Community listing. Along the way the plan's privacy line turned out to be false — the redacted logs were keeping the model's answers, and the answers quote the transcripts — and it stayed false until a test said so.

### Hero exhibit — the privacy test

*Terminal block. Source: notes 2026-09-04, "Surprise, and the most important finding of the session"; and notes 2026-09-05, "Privacy check on the volume itself".*

```
tests/test_hosted.py::test_synthesize_job_end_to_end            FAILED
  AssertionError: transcript text leaked into 003_synthesis.json

the claim in the plan:  "redacted logs contain no transcript text"
what redact=True did:   prompts  → digest
                        response → verbatim
what a response is:     the synthesis, receipts included

fix (core/logger.py):   response text → digest
                        `data` dropped from the record
                        usage · timing · stop reason kept

live, on the volume (fly ssh console):
  /data/runs/20260905-054758-C-hosted        556 KB
  corpus/ under /data/runs                   none
  calls/003_synthesis.json
    system · user · text → {chars, sha256}
    user prompt  90,569 chars
    response     16,447 chars
```

**Caption.** The plan said the logs were clean. The test said they weren't. Everything since — the retention sweep, the listing's FAQ, the privacy page — rests on the assertion, not on the sentence.

---

## Stats (four)

| | |
|---|---|
| **1.9 s** | hosting overhead on a 12-minute run (client wall 721.4 s against engine wall 719.5 s) |
| **8 m 20 s** | install to run-start in Figma, first time, key lookup included |
| **6 → 0** | mechanical failures when Motif's own report is checked by Motif's critic |
| **16 sections · 71 stickies · 4 connectors** | one run drawn on a FigJam board by the plugin |

*Sources: notes 2026-09-05 "Hosting overhead"; 2026-09-05 "Stage 2 QA gate, the user's Figma run"; 2026-09-05 "Stage 3 QA" and `docs/exhibits/stage3-board/critique-roundtrip-after-fix.json`; 2026-09-05 "Build board on the first file (05–08)".*

## Meta

| | |
|---|---|
| role | Designer and builder — service design, tier design, plugin UI, board renderer, QA gates, listing |
| team | Solo; Claude Code as build partner, Claude as hub for assets and copy |
| timeline | 4–6 September 2026 |
| surface | Figma Community plugin (FigJam + Figma Design) on a hosted engine; MCP server and CLI unchanged |
| tools | Python · FastAPI · Fly.io · TypeScript · esbuild · Figma Plugin API · Playwright |

## At a glance

**The problem.** The engine ran in a terminal, on one key, in one process. A designer who will never open a terminal can't reach it, and a plugin can't run Python.

**The solution.** One hosted service wrapping `synth/engine.py` unchanged, with the user's Anthropic key forwarded per job and never logged; a plugin that uploads transcripts, streams the loop's own progress, and draws the board itself from the same layout the MCP tool returns. Free on your own key. ETOT's key runs prepaid credits or nothing.

---

## 01 · The service — three constraints wrote the architecture

**Context.** Part 2 left an importable engine and five MCP tools. Neither could serve a plugin: `core/llm.py` built one module-level `Anthropic()` client from the environment, so every run used the machine's key.

**What was built.** A `contextvars` client (`using_key`) so a hosted job runs on its caller's key, with the environment still the default so the CLI and MCP local mode don't change; `surfaces/hosted/` (job API, job registry with caps and TTL, credits ledger, Dockerfile, fly.toml); `surfaces/mcp/remote.py` rewritten as a client of the job API, with the server's five remote branches wired to it. Eleven new tests in `tests/test_hosted.py`; suite 30 passed in 4.19 s.

**Findings**

- **A job API, not a request.** From `docs/part2-notes.md`: the refactor regression took 440.9 s, the recorded 15-transcript run 2,064.6 s and $4.88. A single HTTP request that long dies at a proxy. Submit, stream, fetch — and a plugin window that closes mid-run picks the job up by id.
- **The key travels in a header.** The plugin UI runs in a sandboxed iframe whose origin is `null`, so every call is a CORS preflight. `CORSMiddleware` allows any origin for GET and POST with `Content-Type`, `X-Motif-Key`, `Authorization`, `Last-Event-ID`; the key is never a cookie, so an open origin policy exposes nothing the caller didn't already hold. Verified live: `OPTIONS /v1/jobs` from `Origin: null` returns `access-control-allow-origin: *`.
- **A second bug the tests caught.** The remote client merged the engine's result over the job id, so `run_id` came back as the guessable run-directory name instead of the random job id later calls need. Fixed in `_as_tool_result`.
- **Deploying is its own list.** `fly auth login` refuses to run under Claude Code's `!` prefix; `fly apps create` refused until a card was on the account; `[build] dockerfile` in fly.toml resolves relative to the toml, not the repo root; the build context was 250 MB across 9,920 files until a root `.dockerignore` allow-listed six paths. Final image 62 MB.

**Live.** App `motif-hosted`, region `ord`, one shared-CPU machine, 1 GB memory, a 1 GB volume, `https://motif-hosted.fly.dev`; `/healthz` returns `{"ok":true,"paid_tier":false,"jobs":0}`.

**Stage 1 QA gate.** The MCP server in remote mode synthesised michelle + david through the deployed service: job `5GfWRXE3yUt43vfGyPhNSmzb`, hosted run `20260905-054758-C-hosted`, 11,482 words, 15 insights, contested I-02, I-05, I-08, 3 iterations, $1.1409, engine wall 719.5 s, client wall 721.4 s, 21 progress notifications, run record `redacted=true` with 8 calls and 224,535 → 73,279 tokens.

*Figure: `docs/exhibits/stage1-remote-qa/synthesize-result.json` (and `report.md`).*
*Sources: notes 2026-09-04 "Engine constraint for BYOK", "Why a job API", "Stage 1 built offline", "Second bug caught by the tests"; 2026-09-05 "Service change for the plugin", "Deploy gotchas", "Live", "Stage 1 QA gate PASSED".*

**Pull quote.** *The engine didn't need rewriting. It needed a place to put the key.*

---

## 02 · The privacy test — the claim that was false until it was asserted

**Context.** The spec's privacy line is one sentence: transcripts processed for the run and discarded, nothing stored. In the plan that mapped onto something the logger already had — `redact=True` writes prompt bodies as digests and skips the corpus snapshot — and the processed corpus lives in the job's memory for the run plus a short TTL, so remote `motif_receipts` only works inside that window and the plugin gets its receipts inline instead.

**What happened.** `test_synthesize_job_end_to_end` failed with *transcript text leaked into 003_synthesis.json*. `redact=True` had digested the prompts and kept the model's response verbatim — and a synthesis response quotes the transcripts, because the receipts are the point. Fixed in `core/logger.py`: response text is a digest too, `data` is dropped from the record, usage, timing and stop reason stay.

**Then it was checked on the machine, not in the code.** `fly ssh console` on the live volume: the run directory is 556 KB; there is no `corpus/` directory anywhere under `/data/runs`; `calls/003_synthesis.json` holds `system`, `user` and `text` as `{chars, sha256}`. A five-word phrase from a cited turn appears only in `output.md`, the run's own report, and in the job's scratch directory — both deleted by the expiry sweep an hour after the job finishes, covered by `test_expiry_drops_corpus_and_run_content` and not re-observed live in that session.

**And then it was given a deadline.** So the privacy page could say "deleted 30 days after the run" before it went up, `JobStore.sweep_records()` deletes any run record whose `meta.json` `started` is older than `retention_days` (default 30, `MOTIF_RETENTION_DAYS`), with directory mtime as the fallback; it runs at startup and at most hourly, and `/healthz` reports `retention_days` and `records_swept_at`. Tested (`test_retention_sweep_removes_old_records_and_keeps_young`; 36 tests pass) and then verified live: a synthetic 67-day-old record planted beside the 11 real ones was gone after the startup sweep, the 11 remained, `/healthz` returned `retention_days: 30.0`.

**Findings**

- **Redaction is a property of the record, not of the prompt.** Half a redaction is a leak with a clean name.
- **A privacy sentence you can't fail is marketing.** The FAQ now points at a check that ran on the volume, and cites the notes entries by date.
- **Retention needs a sweeper, not a policy.** The page could not say thirty days until something deleted at thirty days.

*Sources: notes 2026-09-04 "Privacy line in the spec", "Surprise, and the most important finding"; 2026-09-05 "Privacy check on the volume itself", "Retention sweep for redacted run records".*

**Pull quote.** *A privacy property is a test, **not a sentence.***

---

## 03 · The tiers — what ETOT's key is for

**Context.** The plugin ships free, on the user's own Anthropic key: pasted once, stored in `figma.clientStorage`, sent only in a request header with a run, used for that run's model calls, then dropped. The paid tier is prepaid credits through ETOT's hosted engine on ETOT's key. The rule underneath both is one sentence: ETOT's key runs prepaid credits or it doesn't run.

**What that ruled out.** Figma's payments API sells one-time purchases or subscriptions, not a depleting balance, so credits need a ledger ETOT owns, topped up by Stripe Checkout through a webhook. Designed in stage 1, built when the prerequisites are dated. In this release the `Credits · not yet` control is hidden entirely rather than shown disabled — a disabled control in a public listing draws questions and reviewers read it as unfinished — and the code path stays behind the server's `MOTIF_PAID_ENABLED` flag, which refuses any job without a BYOK key.

**Where the entity stands.** LLC filing has started, single-member. Stripe and the credits ledger stay unbuilt until there are first users. `[not in notes: LLC — entity name, state, filing and formation dates]`

**Findings**

- **No free run on ETOT's key, ever.** Not a trial, not an allowance. If a trial is needed later it is a coupon for credits.
- **A hidden control is a decision, not a gap.** The listing's version notes say a paid tier follows in a later release; the flag is the truth of it.
- **The paid tier is not a feature list.** It sells not managing a key, an invoice, a licence, and a support address — which is why the prerequisites are entity, rails, support, terms, and not code.

*Sources: notes 2026-09-04 "Payments constraint"; 2026-09-05 ruling (1), ruling (5), ruling (3).*

---

## 04 · Three gates — run in the user's own Figma files

**Context.** Every stage of the plugin ends in a gate that cannot be run by the machine that built it: development plugins load only in the Figma desktop app, so install timing, the clipboard, and the drawn board are the user's run, logged in the notes before anything is called done.

### Stage 1 — the service, verified from a laptop

Covered in section 01. Gate: the MCP server in remote mode synthesises the sample corpus against the deployed service, and the run directory on the volume holds a redacted record and no transcript text. Passed 2026-09-05.

### Stage 2 — the plugin, free tier, no board

Built in `surfaces/figma/`: TypeScript, esbuild, no framework. `code.ts` holds client storage, notifications and resize; `ui.ts` the screens; `api.ts` submit, SSE with resume, fetch; `docx.ts` reads Word files in the plugin with a zip walk, `DecompressionStream("deflate-raw")` and `word/document.xml` paragraphs, no library. `dist/ui.html` 33 KB, `dist/code.js` 2 KB. The manifest allow-lists one domain.

**Parity before trust.** The plugin's own docx extraction, run under Node against all 16 sample files (29.8 MB → 587 KB of text), ingests to the same manifest as python-docx: 15 transcripts, 101,042 words, one empty file skipped on both paths; 1,868 turns compared, 1,867 byte-identical, one differing only by a line break inside a paragraph, 0 mismatches. The first run of that test found the reason: `<w:br/>` inside paragraphs in Lisa (two) and Peter (one), which would have split a turn in two on the text path.

**A harness, because the window won't shrink.** `dist/ui.html` runs in a browser tab with `localStorage` standing in for Figma's client storage; `test/harness.html` frames it at 440, 375 and 320 px. Chrome's window would not shrink below 1440 px on this machine, so real iframes at those widths were the honest test. It immediately caught a bug that would have shown on every first open in Figma: the "A run is still going from last time" card displayed with no run, because `.card { display: flex }` outranks the browser's `[hidden]` rule. Fix: `[hidden] { display: none !important; }`.

**The browser-path live run.** Job `ngqJoYXl17yhFKHVFdosoV84`, hosted run `20260905-171330-C-hosted`, 11,482 words, 12 insights, contested I-05 and I-11, 3 rounds, $1.0328, engine wall 660.1 s, 20 progress events shown live; zero layout issues at 440 px.

**The gate, in Figma.** Install to run-start 8 m 20 s including looking up the key and reading the instructions — "call it 5–6 minutes for a repeat user"; the run 12 m 33 s against the plugin's own reported 12.4 minutes; install to result about 21 minutes. The report copied to the clipboard inside Figma as full Markdown with receipts, no fallback box. Nothing clipped or broken on any screen. **Ruling: the ten-minute target applies to install-to-run-start, not install-to-result, because a run alone takes twelve minutes.** The gate is redefined that way in the plan and the plugin README.

### Stage 3 — the board writer

Gate in section 05. Two observations came out of the stage-2 run and went into stage 3: with two transcripts every insight reads "low", because high needs four participants, so the chip now says why — `low · 1 of 2`; and the UI still uses Figma's default blue and Inter, so the restyle onto the ETOT chassis waits for the design-system session's tokens.

**Findings**

- **The clipboard is not guaranteed.** In the harness both `navigator.clipboard.writeText` and `execCommand("copy")` failed on a synthetic click, which is also what a sandboxed iframe that denies clipboard access would do. The copy button falls back to revealing the report in a selected read-only box — 58,847 characters, no overflow at 440 and 375 px. In Figma, the real click worked and the fallback never appeared.
- **The error screen relays the engine verbatim.** Anthropic's 401 `API key is invalid.` arrives as written, under a plain hint for the three cases a user can act on, and `last_job` is cleared on failure so a failed run never offers itself for resumption.
- **The gate that the builder cannot run is the gate that matters.** Everything up to the desktop app is a claim.

*Figures: `docs/exhibits/stage2-plugin/browser-run.json`; `docs/exhibits/stage2-plugin/` screens at 440 / 375 / 320.*
*Sources: notes 2026-09-05 "Stage 2 opened", "Plugin built", "docx parity", "Harness for the QA gate", "Bug caught by the harness", "Every screen scanned", "The error screen", "Browser-path live run PASSED", "Clipboard finding", "Not done in this session, by construction", "Stage 2 QA gate", "Two observations from the user for stage 3".*

**Pull quote.** *Development plugins load only in the desktop app. Which means the last gate is **always someone else's hands.***

---

## 05 · The board — one layout, two editors

**Context.** `synth/board.py::layout` is the single source of truth for what a Motif board looks like; part 2's MCP tool handed that layout to a host, which ran the scripts. The plugin draws it itself, and had to grow a second renderer: stickies and connectors are FigJam nodes, and Figma Design has sections but no stickies.

**What was built.** `verdict_layout` in `synth/board.py` (a section per checked claim, coloured by outcome, one sticky per objection, a final section for corpus-level objections) and a run card on both layouts; `engine.board` serving critique runs; the hosted `/board` endpoint accepting any finished job. In the plugin, `src/board.ts` renders on the current page — FigJam with sections, stickies in two rows, "contested by" connectors and a card above the grid; Figma Design with the same sections as auto-layout frames and text, no connectors — picking a free origin to the right of existing content and throwing rather than returning a partial board.

**Tested three ways.** A fake Figma API first: 15 sections, 70 stickies, 7 connectors on FigJam and 0 on Design; the verdict layout 9 sections and 33 stickies; a duplicated sticky key and an empty layout both throw. Then the plugin's own renderer bundled and run on a throwaway FigJam board through Figma's MCP: 4 sections, 20 stickies, 1 connector, run card at y = −568, every colour read back as a palette value and none as CUSTOM, section heights 656 / 792 / 680 / 696 px inside the 1200 px slot. The same script on a throwaway Design file: 4 sections, 20 frames, frames hugging their text — first section 1600 × 421 px, claim 168 px, receipts 134 and 100 px, opportunity 117 px.

**The gate, in Figma.** From the user's FigJam run of run `20260905-221749-C-hosted` (16 insights, 2 contested, 3 rounds, $1.14, 12.1 min): the board drew 16 sections, 71 stickies and 4 connectors — 16 claims, 32 receipts, 4 counters, 16 opportunities, 2 contested, 1 card — to the right of an existing verdict board, so the free-origin rule held on a page that wasn't empty. Yellow medium, orange low, white receipts, pink counter, blue opportunity, violet contested and card. Then the same result in Figma Design: 16 sections, 71 stickies, no connectors, on the dark page, with Figma's own frame labels reading as an accidental legend. At a glance against part 2's board the shape is the same, with two differences by design: the run card above the grid, and the verdict board's `I-nn · fail` / `I-nn · pass` sections, which did not exist in part 2.

**Findings**

- **The sandbox has no `toLocaleString`.** The run card read "11482 words" on the first real board; `Number.toLocaleString` returns bare digits in Figma's plugin sandbox, so `thousands()` formats by hand. Confirmed on a real board: "11,482 words".
- **`documentAccess: dynamic-page` forbids the synchronous lookup.** The board drew in full and the step *after* drawing threw *Cannot call with documentAccess: dynamic-page*. The MCP runtime allowed both forms, so the earlier verification never saw it. `code.ts` now resolves ids with `getNodeByIdAsync`.
- **Opening the plugin should show what you have.** A fresh file opened on the empty form instead of the stored last result. Now, with a key, a stored result and no run in flight, it opens on the result screen with Build board ready.
- **Titles truncate at the section edge**, because the title is the whole claim. FigJam hard-cuts, Design ellipsises. Rendering, not a defect — but an ellipsis at a fixed length is on the ledger.

*Figures: `docs/exhibits/stage3-board/figjam-readback-summary.json`, `figjam-section-I-02.png`, `figjam-run-card.png`, `design-section-I-02.png`; `docs/exhibits/stage3-plugin/` 05–08 (FigJam), 13–15 (Design), `06-board-overview-verdict-and-synthesis.png` against `docs/exhibits/recorded-run/board-overview.png`.*
*Sources: notes 2026-09-05 "Stage 3 built", "Renderer tests", "Real-board check", "Surprise on the real board", "Stage 3 QA gate PASSED", "Synthesis from the plugin, txt path", "Build board on the first file", "Stored result on open", "Clipping", "At-a-glance read", "Side-by-side as seen by Claude", "Figma Design, user's run".*

---

## 06 · The round trip — six failures Motif dealt itself

**Trace exhibit.** *Source: notes 2026-09-05 "Stage 3 QA", "Re-verified live after the deploy" (`docs/exhibits/stage3-board/critique-roundtrip-after-fix.json`), and "Post-fix Check-a-synthesis on the live plugin path".*

```
1  the user's run — Check a synthesis, on Motif's own stage-2 report
   verdict FAIL   16 claims   6 fails   0 warnings
   every fail: quote_mismatch on a counter-evidence turn
               with an empty quote   e.g.  david:0012: ""

2  root cause — predicted the day before, in part 2's notes
   synth/report.py printed receipts for evidence only
   → parse_motif_markdown made counters with empty quotes
   → the deterministic check read absence as mismatch

3  ruling
   Motif's own report must round-trip through Motif's critic
   with zero mechanical failures.

4  fix, two parts
   report.py       prints counter receipts too
   quote_mismatch  counter with no quote → "no receipt in
                   the source", skipped
                   evidence with no quote → still fails
   two tests · 35 pass

5  re-verified live   job lmIPSVZ36Q0pAf8xM4Sd5lcS   241.6 s
   the pre-fix-format report, 12 claims, 4 empty counters
   mechanical failures                    0
   remaining, model-judged   I-11 unsupported   (correct:
     selective quotation)   I-01 merged_insights (warn)
```

**What it means.** The critic was right and the report was wrong. A deterministic rule counted a missing receipt as a mismatched one, and the only reason it surfaced is that Motif was pointed at its own output — the one document whose correctness nobody had checked mechanically. The fix touched one deterministic rule's handling of one input shape and left the model-judged rules alone, so the instrument measured in parts 1 and 2 is unchanged.

**Check a synthesis, live.** The post-fix pass on the plugin path: job `PDt5IyygwZLrUc1Vni5o2L7V`, "structured 16 insight(s) from Motif-format markdown (deterministic)", "deterministic checks: 0 failure(s)", verdict FAIL with 16 claims, 2 fails, 0 warnings, and the honest line "Not checked: missing_theme (no intake notes for a pasted document)". The fails: I-01 `missing_counterexample`, which matches the original run's own contested flag, and I-13 `unsupported`, which is new. I-10, contested in the original run, passed here — critic variance, recorded and not tuned. The verdict drew as a board: 16 sections, 19 stickies. Cost, read from the volume at `/data/runs/20260906-000123-critique-doc/meta.json`: $0.1793, 116.6 s, 37,509 → 10,428 tokens, one call, stop `critique_fail`.

**Findings**

- **A predicted failure left unfixed is a failure you scheduled.** The root cause was written down on 2026-09-04 and left; it arrived on 2026-09-05 as six red stickies in the user's own file.
- **Verdicts need their own numbers.** The verdict screen carried no cost or time until `_critique` returned `cost_usd` and `wall_seconds`; until the deploy ran, the live tiles showed "–". After the deploy, one live pass: job `6R0hYQM-Rccnlk6Yj0STOHCq`, 15 claims, 3 fails, $0.1546, 88.4 s.
- **A dollar sign nearly didn't survive the build.** The cost tile rendered "0.49": `build.mjs` inlined the script with a string `String.replace`, and `$$` in a replacement string collapses to one `$`, so `$${cost}` reached `dist/ui.html` as `${cost}`. Every build to date had shipped the tile without the sign. Fixed with function replacers; verified on the rendered tiles as "$0.49".

*Figures: `docs/exhibits/stage3-board/critique-roundtrip-after-fix.json`; `docs/exhibits/stage3-plugin/` 16–21; `docs/exhibits/stage4-polish/live-verdict-cost-time.json`, `harness-scan-rerun.json`, `harness-scan-tiles-rewrap.json`.*
*Sources: notes 2026-09-05 "Stage 3 QA", "Re-verified live after the deploy", "Post-fix Check-a-synthesis", "Polish (b)", "Bug found by the harness while checking (b)", "Verdict screen at 440 px", 2026-09-05 second session (cost re-read from the volume), "The blocked step from that session".*

**Pull quote.** *Motif failed its own report six times. **The report was wrong.***

---

## 07 · The listing — everything that isn't code

**Context.** Submitted to Figma Community review on 2026-09-06 at 00:31 CDT under the ETOT team profile @etot, free tier only. Plugin id `1678295978273812914` — the first generated id was superseded, and the second is the one in the manifest at commit `7cd99fd`. `[not in notes: Community review outcome and date]`

**The icon is a rule, not a picture.** Per ETOT's per-tool identity rule, each tool's icon is its own generated field: one colour, no letterform, with the monogram reserved for the studio. `surfaces/figma/listing/icon.png`, 128 × 128, 2,165 bytes, generated by `etot-site/scripts/icons.py` at commit `23c596d` from `etot-site/assets/icons/motif-128.png`; the system is `etot-internal/brand/icon-system-spec.md`.

**The cover is a screenshot, and says so.** `surfaces/figma/listing/cover.png`, 1920 × 960, composited from `docs/exhibits/stage3-plugin/08-board-I-01-contested-zoom.png` — the I-01 section of run `20260905-221749-C-hosted` as the plugin drew it — cropped to the section and letterboxed on the FigJam canvas grey `#F5F5F5`. Screenshot-derived rather than a canvas export, because the boards were deleted before an export was taken. It replaces the spec's I-09 choice, whose only exhibit is the part-2 MCP-drawn board.

**The category doesn't exist.** The spec asked for Research / Whiteboarding. Figma's plugin taxonomy has no such category — the Whiteboarding entries are templates — so the listing sits under Design tools › Content generation, with the five tags Figma allows: ux research, research synthesis, user interviews, transcripts, affinity mapping.

**The data-security form is a design surface.** Answered as: a hosted backend that receives no plugin-API data; network requests only to `motif-hosted.fly.dev`; no user authentication; no plugin-API data stored; solo developer; no formal vulnerability process yet, reports via GitHub issues or hello@etot.design; no accreditation. Comments on; support hello@etot.design with a stated two-working-day response; privacy policy at `https://etot.design/privacy/`, live before submission (`etot-site` 698104c, recorded in `surfaces/figma/listing.md`). Two-factor authentication is required by Figma to publish, and the session had to be restarted after enabling it.

**The near-miss.** The carousel was nearly submitted as the raw exhibits — menu bar, browser tabs, clock, avatar all visible. Caught before submission. Worse, the same raw screenshots were already in the repo's history: 22 of them under `docs/exhibits/stage3-plugin/`, showing employer file names in the Figma tab strip on every exhibit and the last four characters of an API key on 02. `git filter-repo --path docs/exhibits/stage3-plugin/ --invert-paths` in a fresh clone removed the folder from every commit — 3 commits had touched it, 0 after; pack 43.47 MiB → 24.22 MiB — with a mirror backup kept, and 22 cropped replacements committed on top under the same filenames, so every notes line that cites an exhibit by number stays valid.

**The rule that came out of it,** now in `CONTRIBUTING.md` § Conventions and the plan's stage-4 QA gate: raw screenshots never leave the repo and never enter it either. Every exhibit and every publication asset is cropped to the product surface and checked for personal information — menu bar, tabs, clock, avatar, file names — before it is saved. Publication assets live under `surfaces/figma/listing/` or `docs/figures/`.

**One comparable the research missed.** Blossom, in FigJam's plugin list under research, marked paid: a video repository for research recordings whose plugin drags playable clips onto the canvas as cards, slides and stickies, and needs a Blossom account. `[not in notes: Blossom pricing]` — the site has no dollar amount anywhere and its Pricing link is a dead anchor, so pricing is sales-led and unverifiable from outside. Adjacent, not overlapping: Blossom brings recorded evidence to the canvas for people to watch and tag; Motif produces claims with verbatim receipts, a critic, and contested markings, on the user's own key with no account.

**Findings**

- **An icon system is cheaper than an icon.** The rule decided the artwork; the artwork took a script.
- **The taxonomy is the market's, not the spec's.** Where the category doesn't exist, say which one you chose and why.
- **Screenshots carry the day job.** A cropping rule is not tidiness; it is the difference between an exhibit and a leak.

*Figures: `surfaces/figma/listing/icon.png`, `surfaces/figma/listing/cover.png`, `surfaces/figma/listing/carousel/01-board-overview.png` … `05-design-editor.png`.*
*Sources: notes 2026-09-05 "Icon delivered", "Cover delivered", ruling (2), ruling (3), ruling (4), "Comparable missed by the research report"; 2026-09-06 "Motif submitted", "Category", "Tags", "Images", "Data-security answers", "Settings", "New rule", "Listing link", "Blossom", "History scrub", "History scrubbed"; `surfaces/figma/listing.md` for the privacy-page commit.*

**Pull quote.** *The tab strip is part of the screenshot. **So is the day job.***

---

## 08 · What it costs

**Hosting overhead: about two seconds.** On the stage-1 QA run, client wall 721.4 s against engine wall 719.5 s — the event stream kept pace and no proxy cut it. On the shorter PyPI-installed run, 339.2 s against 338.3 s. The stage-1 run cost twice the part-2 local regression ($0.5529, 1 iteration, 440.9 s) because it ran all three iterations, not because it was hosted.

**Per run, on the user's key.**

| run | corpus | result | cost | wall |
|---|---|---|---|---|
| stage-1 QA, MCP remote (`20260905-054758-C-hosted`) | michelle + david, 11,482 words | 15 insights, 3 contested, 3 iterations | $1.1409 | 719.5 s |
| PyPI 0.3.0 live (`20260905-164234-C-hosted`) | michelle + david, `max_iterations=1` | 13 insights, 2 contested | $0.458 | 338.3 s |
| browser path (`20260905-171330-C-hosted`) | michelle + david | 12 insights, 2 contested, 3 rounds | $1.0328 | 660.1 s |
| the user's Figma run (`20260905-221749-C-hosted`) | David.txt + Michelle.txt | 16 insights, 2 contested, 3 rounds | $1.14 | 12.1 min |
| Check a synthesis (`20260906-000123-critique-doc`) | the stage-2 report + its transcripts | 16 claims, 2 fails | $0.1793 | 116.6 s |
| Check a synthesis, post-deploy (`20260906-010935-critique-doc`) | the stage-1 report + its transcripts | 15 claims, 3 fails | $0.1546 | 88.4 s |
| part 2, full corpus (`20260904-154633-C`) | 15 transcripts | 23 insights, 3 contested | $4.88 | 2,064.6 s |

In the plugin's own words, and in the listing: about $1 for two transcripts, about $5 for fifteen. The result screen shows the exact API cost of every run.

**What ETOT pays.** One shared-CPU machine with 1 GB of memory and a 1 GB volume, kept running, in `ord`. `[not in notes: first Fly.io invoice — amount, period, date]`. `[not in notes: total part-3 API spend]`

**Findings**

- **The hosted path costs what the CLI path costs.** Same corpus, same settings, same shape as part 2's local regression.
- **The engine is the bill.** Hosting is a machine; the model calls are the money, and they are the user's.
- **A critique pass is a fifth of a synthesis.** One call, ninety to a hundred and twenty seconds, under twenty cents — which is what makes "check a synthesis someone else wrote" a reasonable thing to do twice.

*Sources: notes 2026-09-05 "Hosting overhead", "Stage 1 QA gate PASSED", "Live remote synthesis from the PyPI-installed 0.3.0", "Browser-path live run PASSED", "Synthesis from the plugin, txt path", "Post-fix Check-a-synthesis", second session (volume re-read), "The blocked step from that session", "Live" (machine sizing), "Stage 4 opened" (the plugin's own cost words); `docs/part2-notes.md` via notes 2026-09-04 "Why a job API".*

---

## 09 · Honest ledger — still open

| | |
|---|---|
| **OPEN** | Community review. Submitted 2026-09-06 00:31 CDT; `[not in notes: Community review outcome and date]`. Until it clears, the listing page is not public. |
| **OPEN** | No users. `[not in notes: first 10 installs — count, dates, source]` and `[not in notes: first 3 pieces of feedback]`. The success criterion is ten installs and three pieces of written feedback, logged in `docs/part3-notes.md`; both become the next section on this page. |
| **OPEN** | The paid tier. Hidden control, server flag off, ledger and Stripe unbuilt until first users. LLC filing started, single-member: `[not in notes: LLC — entity name, state, filing and formation dates]`. |
| **OPEN** | Section titles truncate on the board, because the title is the whole claim: FigJam hard-cuts, Design ellipsises. An ellipsis at a fixed length in `board.ts` is the fix; deferred. |
| **OPEN** | The plugin still wears Figma's default blue and Inter. It is to be restyled on the ETOT chassis — ETOT blue accent, mono for ids and receipts — once the design-system session hands over its first components. |
| **OPEN** | Confidence with a small corpus. With two transcripts every insight reads low, because high needs four participants. The chip now says why (`low · 1 of 2`); scaling the threshold with corpus size is an instrument change and waits for the v3 eval. |
| **OPEN** | Duplicate receipts: an insight can cite the same turn twice as two evidence entries (I-06, `david:0026`). Candidate `duplicate_receipt` check; instrument change, so it waits for the v3 eval. |
| **OPEN** | Hosting cost. `[not in notes: first Fly.io invoice — amount, period, date]` |
| **PUBLIC** | [github.com/sleepycobalt/motif](https://github.com/sleepycobalt/motif) (MIT) · [pypi.org/project/etot-motif](https://pypi.org/project/etot-motif/) · [the listing](https://www.figma.com/community/plugin/1678295978273812914) · the runs, verdicts, and board read-backs are all in the repo. |

**Closing pull quote.** *The plan said the logs were clean. **The test said they weren't.** Everything published here rests on the second sentence.*

---

## Footer

**Motif** · part 3 · ETOT · research synthesis — Corpus: Hanchard & San Roman Pineda 2023, University of Sheffield, CC-BY-NC — Eric Frye · 2026
