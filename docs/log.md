## 2026-09-02 — Corpus and brief
Tried: Downloaded Sheffield Dataset 2 and 3; verified 15 transcripts, ~105k words, CC-BY-NC.
Happened: Promised XML codebook was never deposited; using the final project report as insight-level ground truth instead.
Next: Manual synthesis on 5 transcripts, then transcript conversion script.

## 2026-09-02 — Setup
Tried: Console account, API key, venv, git, smoke test.
Happened: Git identity, pasted-line, and curly-quote snags; API worked first try (17 in / 15 out).
Next: R&D brief, pull Sheffield corpus.

## 2026-09-03 — Manual synthesis and ground truth
Tried: Hand-synthesised 5 transcripts (Michelle, David, Bruce, Stephen, Penni) — 2h05 reading, 45m clustering, 74 evidence items, 11 insights.
Happened: 9 of 11 insights matched the researchers' report; 5 report themes live in transcripts I didn't read. Built theme checklist (16) and trap list (12).
Next: Intake pipeline — convert docx to text with line refs.

## 2026-09-04 — MCP server, step zero
Tried: Verify Figma's MCP write path to FigJam before writing Motif code; read the engine for an architecture proposal.
Happened: Write path exists (`use_figma` + `figma-use-figjam` skill, remote server only, OAuth). Registered the server; blocked on the OAuth click. Found stdout-printing logger and subprocess CLI as the two engine changes the server needs first.
Next: User authenticates Figma in `/mcp` and gives a board URL; run the write test; then extract `synth/engine.py` and build `motif.synthesize`.

## 2026-09-04 — Step zero run
Tried: OAuth to Figma's remote MCP, create a throwaway FigJam board, write a section + 3 stickies + connector via `use_figma`, read back, screenshot.
Happened: Passed first time. Five nodes created and read back; screenshot in `docs/exhibits/step-zero/`. One sticky colour round-tripped as CUSTOM. Five tools confirmed (board is the fifth); architecture approved; critique must be validated against `eval2/blind/` R1–R6 vs `eval2/scoring.md`.
Next: Build step 1 — extract `synth/engine.py`, logger emit hook, corpus snapshot; offline tests with a stubbed model; one regression run.

## 2026-09-04 — MCP server build
Tried: Engine extraction, logger emit/redact/snapshot, MCP server with five tools on the 2.x SDK, offline tests, live regression, board tool executed on the real FigJam board, critique acceptance vs eval2 through the server.
Happened: 19 offline tests pass; ingest byte-identical; regression run $0.55/441 s/13 insights with corpus snapshot; R5 board (15 sections, 78 stickies, 12 connectors) built and read back. Venv had lost its packages; SDK 2.x renamed FastMCP; plain exceptions hide tool error text.
Happened (cont.): Acceptance recorded — structuring passes (deterministic and model identical); verdict agreement partial: unsupported 25/32, P-03 5/8, P-05 2/8. Client needed log_level for log notifications; progress now sent on every emit. `motif` registered in Claude Code and connected.
Ruling: accept the measured gap, no instrument changes; recorded. Step 5 done: host install snippets (Claude Code, Cursor, Claude Desktop), SKILL.md wrapper, listing copy, registry server.json (validated; description cap 100 chars).
Next: User records the sample-corpus Claude Code session; publish `etot-motif` to PyPI, then the registry entry.

## 2026-09-04 — PyPI publish (entry added retroactively in the part-3 session)
Tried: Build and publish `etot-motif` 0.2.0, verify from PyPI in a fresh venv, submit the registry manifest.
Happened: The wheel would have shipped without `synth.yaml`; fixed first (config moved into the package, `config/synth.yaml` symlinked). Published; fresh-venv install gives working `motif` and `motif-mcp` (five tools over stdio). Registry entry `io.github.sleepycobalt/motif` 0.2.0 active. Notes in `docs/part2-notes.md`.
Next: Part 3 — hosted engine, plugin, board writer, listing.

## 2026-09-04 — Part 3 planning
Tried: Read the plugin spec, the MCP spec, and CONTRIBUTING; propose architecture and build order before code.
Happened: Proposal in `docs/specs/part3-build-plan.md`: one hosted job API over the unchanged engine, plugin free tier as its client with the user's key forwarded per job, board writer from the existing layout data, paid tier designed behind a flag. Found: per-request key needs a context-var client in `core/llm.py`; stickies are FigJam-only; credits need a Stripe-fed ledger.
Next: Ruling on hosting, Design-editor timing, and payment rails; then stage 1 (hosted service, remote mode, offline tests, deploy).

## 2026-09-04 — Part 3 stage 1 build (hosted engine)
Tried: Per-context LLM client for BYOK, hosted job API (submit / SSE events / result / board / receipts / run record) with per-IP and size caps, credit ledger designed behind a flag, remote client and MCP remote mode rewired, offline tests, Fly config.
Happened: 30 tests pass. The tests caught a privacy leak (redact mode kept response text, which quotes transcripts; fixed) and a run-id collision in the remote client. Fly CLI installed but needs the user's login; deploy and the live QA run are pending.
Next: `fly auth login`, create app + volume, deploy, then the QA gate: MCP remote mode against the deployed service on the sample corpus; record numbers; then 0.3.0 to PyPI.

## 2026-09-05 — Part 3 stage 1 deploy and QA gate
Tried: Fly login (separate terminal), app + 1 GB volume, deploy with remote builder, health check, QA gate: MCP server in remote mode synthesising michelle + david through the live service, then receipts / board / run record by job id, then inspect the volume over ssh.
Happened: Deployed at https://motif-hosted.fly.dev after two fixes (dockerfile path relative to fly.toml; .dockerignore cut a 250 MB context). QA passed: 15 insights, 3 contested, $1.14, 719.5 s engine / 721.4 s client, 21 progress notifications; volume holds digests only, no corpus. Fixed: remote mode did not load .env.
Next: Publish 0.3.0 to PyPI (remote mode for installed users); start stage 2 (plugin, free tier).

## 2026-09-05 — Release 0.3.0 (remote contract) and registry update
Tried: Bump to 0.3.0, build, publish to PyPI, verify from PyPI in an empty venv (CLI, local stdio handshake, zero-cost remote probes, one live remote synthesis), publish the registry manifest at 0.3.0.
Happened: All passed. PyPI 0.3.0 live; registry lists 0.3.0 as latest. Live remote run from the installed package: 13 insights, 2 contested, $0.458, 338.3 s engine / 339.2 s client. Gotchas: the publisher token expires within a day (device flow again); pip's index lagged the upload by about two minutes.
Next: Stage 2, the Figma plugin on the free tier, against the live service.

## 2026-09-05 — Part 3 stage 2 build (plugin, free tier, no board)
Tried: Figma plugin in TypeScript with client-side docx extraction, CORS on the service, a browser harness at 440/375/320 px with overflow scans of every screen, a live run launched from the plugin UI against the hosted engine.
Happened: Parity with python-docx on 1,868 turns (one in-paragraph break becomes a space by design). Harness caught a hidden-card CSS bug and a clipboard fallback gap; both fixed. Live browser-path run: 12 insights, 2 contested, $1.03, 660 s. Zero layout issues at any width.
Next: User runs the ten-minute Figma QA (import manifest, key, sample corpus) and reports timing plus whether copy works inside Figma; then stage 3, the board writer.

## 2026-09-05 — Part 3 stage 3 build (board writer, critique mode, Design renderer)
Tried: Verdict layout and run card in board.py; plugin board writer for FigJam and Design with a real-board check through Figma's MCP; Build board, stored last result, Check-a-synthesis mode, confidence chip wording; harness at three widths.
Happened: Real FigJam board: 4 sections, 20 stickies, 1 connector, all palette colours on readback; Design file: frames hug text. Fake-API tests cover 15- and 9-section layouts and failure paths. Fixed: bare number formatting in the sandbox, connector bounds, harness count. Zero layout issues.
Next: User's Figma QA: build a board from a run (or a verdict from Check a synthesis) in a fresh FigJam file and in a Design file; compare with the recorded-run exhibit; then stage 4, the listing.

## 2026-09-05 — Stage 3 fixes after the Figma QA run
Tried: Fix the three findings from the user's Check-a-synthesis run: counter receipts missing from the report (quote_mismatch on every counter), getNodeById forbidden under dynamic-page access, plugin not opening on the stored result.
Happened: Report prints counter receipts and the check treats an absent counter receipt as absence; async node lookup; open-on-result. Live re-check on the old-format report: 0 mechanical failures, 1 model fail (I-11, correct), 1 warn. 35 tests pass. Deployed.
Next: User re-runs the synthesis and Build board in a fresh FigJam file and in a Design file; then stage 4, the listing.

## 2026-09-05 — stage 3 close
- tried: user's FigJam and Figma Design runs of the full stage-3 surface (critique → verdict board, synthesis → board, stored result in a fresh file); fifteen screenshots read for counts, colours, clipping.
- happened: gate passed; 16 / 71 / 4 on both boards and the counts reconcile against the insight structure; pre-fix critique board kept as the 6-fail exhibit; section-title truncation noted as a cosmetic open item; MCP spec v1-on-disk discrepancy recorded.
- next: stage 4, the Community listing (free tier only).

## 2026-09-05 — stage 4 start (listing draft)
- tried: listing copy from the spec's § Listing and the registry copy; screenshot picks from the stage-3 exhibits; manifest and review-requirements check; live read of etot.design for links and a privacy page.
- happened: `surfaces/figma/listing.md` drafted (not submitted); links corrected to `/tools/motif/`; needed from the user: post-fix verdict screenshot, icon; gaps: real plugin id at publish, privacy policy URL, support contact with response time; paid-tier control hide-or-label awaiting ruling.
- next: user reviews the copy and rules on the paid-tier control; then the submission session.

## 2026-09-05 — stage 4: post-fix critique run, two polish items, rulings
- tried: user's post-fix Check-a-synthesis on the live plugin path (report of `20260905-221749-C-hosted` pasted, two transcripts re-added); six screenshots into `stage3-plugin/16–21`; polish (a) reason line under the run button and (b) cost and time tiles on the verdict screen; harness at 440 / 375 / 320 on the affected screens; the five rulings into the listing and README.
- happened: round trip clean (0 deterministic failures); FAIL 16 / 2 / 0, I-01 counterexample matches the original contested flag, I-13 new, I-10 passed (variance, recorded); board 16 sections, 19 stickies; pass cost $0.1793, 116.6 s, from the run's meta on the volume. Both polish items built and scanned, zero layout issues; the harness caught a build bug that had been dropping the `$` from the cost tile in every build (`String.replace` `$$`), fixed. Engine returns cost and time for critique runs; hosted deploy blocked in this session, so the live verdict tiles read "–" until `fly deploy` runs. Credits control hidden; support contact and response time in; `[privacy URL]` placeholder and blockers list; icon rule and path recorded, source path pending.
- next: user runs `fly deploy -c surfaces/hosted/fly.toml`; exports the icon to `surfaces/figma/listing/icon.png` and gives the source path; privacy page in an etot-site session; then the submission session. Not submitted.

## 2026-09-05 — stage 4: deploy and live verification of the polish items
- tried: confirm commit `508975c` (other session) was complete and pushed; deploy the engine change it could not deploy; verify cost and time on a live critique pass; re-run the harness scan with the script.
- happened: nothing redone; deployed; live critique returns cost $0.1546 and 88.4 s on 15 claims; harness scan 0 issues at three widths on four screens; post-fix critique pass cost re-read from the volume (0.1793 / 116.6 s).
- next: icon at `surfaces/figma/listing/icon.png` with its source path; privacy page in an etot-site session; then the submission session. Not submitted.

## 2026-09-05 — hosted engine: 30-day retention sweep
- tried: sweep of redacted run records older than 30 days (startup + hourly), test with an old and a young record, deploy, plant a 67-day-old record on the live volume and confirm the startup sweep removes only it.
- happened: 36 tests pass; live volume after deploy holds the 11 real records and not the planted one; `/healthz` reports the retention setting and the last sweep time; README and listing FAQ state the 30 days.
- next: privacy page on etot.design can state "deleted 30 days after the run"; cover image; plugin id at first publish; then the submission session.

## 2026-09-06 — listing: privacy URL
- tried: fill the `[privacy URL]` placeholder in `surfaces/figma/listing.md` now that etot.design/privacy/ is live (etot-site 698104c).
- happened: Links entry points at https://etot.design/privacy/; blocker 3 dropped from § Blockers before submission. `manifest.json` has no privacy field (the URL is a Community listing form field, recorded in listing.md), so it is unchanged.
- next: cover image; plugin id at first publish; then the submission session.

## 2026-09-05 — verdict tiles re-wrap
- tried: stop the six-tile verdict row from orphaning "minutes" at 440 px; re-run the harness on the verdict (live fixture) and synthesis (stored-result fixture) screens at 440 / 375 / 320 with a new tiles-per-row check.
- happened: flex-wrap at 30% basis gives 3 + 3 for six tiles at every width and 5 or 3 + 2 for five; 0 layout issues, 0 orphans; scan script extended and its output kept as an exhibit. Blossom noted as a comparable to check before the listing goes live.
- next: user adds exhibit 22; publish flow in the Figma developer console; Blossom check.

## 2026-09-06 — Motif submitted to Figma Community review
- tried: publish flow in the Figma desktop app under @etot; listing copy, five tags, category, carousel, data-security answers, settings.
- happened: submitted 00:31 CDT, plugin id 1678295978273812914 (second generated id, commit 7cd99fd); category is Design tools › Content generation since the spec's category does not exist; raw exhibits with chrome caught before submission and a no-raw-screenshots rule added to CONTRIBUTING and the plan; listing.md updated to what was submitted.
- next: await review; record the listing link and outcome; Blossom comparable check; first installs and feedback into the notes per the spec's success criteria.

## 2026-09-06 — history scrub of the raw stage-3 exhibits
- tried: record pre-scrub HEAD; mirror backup; `git filter-repo --invert-paths` on `docs/exhibits/stage3-plugin/` in a fresh clone; cropped replacements with the same 22 names; user force-pushed; working checkout re-cloned with `.venv`, `runs/`, `.env`, and the plugin's `node_modules` copied across.
- happened: folder absent from every commit of the new history; pack 43.47 → 24.22 MiB; origin main is `fcea463`; the fresh checkout at the same path runs 36 tests and the plugin typecheck clean with the copied venv; 32 run dirs intact. Old checkout kept at `~/opt/claude/agentic-loop/motif-old-2026-09-06`, mirror at `~/opt/claude/motif-mirror-backup-2026-09-06`, scrub clone at `~/opt/claude/motif-scrub`; none deleted.
- next: delete the old checkout and the scrub clone once the user is satisfied; keep the mirror until the Community review is through; exhibits 01–22 are the cropped set from here on.

## 2026-09-06 — v3 evaluation: instrument frozen, changes built, awaiting ruling
- tried: read the v3 spec, `docs/eval2-results.md`, CONTRIBUTING § Run the evaluation and every "v3 eval item" line; add items (a)–(d) to the change list; freeze and tag `v2.1-eval`; write pre-registered bars with their arithmetic; cost the run plan; build the changes config-switchable with offline tests on the real critic path.
- happened: tag `v2.1-eval` = `3675228`, its "one deterministic change since Eval 2" claim verified against four paths. Four condition configs in `eval3/configs/` (control is the frozen instrument byte-for-byte). New: `second_finding` (model), `duplicate_insight`, `duplicate_receipt`, `critic_citation` (deterministic), `features.dissent_at_intake`, `features.report_unevaluated_sections`. 52 tests pass, 16 of them new. Plan A costs $38.49 against a $25–40 band, leaving less than one run of margin; Plan B is $30.80.
- next: user's ruling on Plan A vs Plan B and on the bars; nothing is spent before it. Then the runs, the blind pack, and `docs/eval3-results.md`.

## 2026-09-06
- tried: draft part 3 case-study copy from docs/part3-notes.md, matching part 2's structure and register
- happened: docs/case-study/part3-draft.md written, nine sections plus ledger, nine [not in notes] brackets left open
- next: fill the Community review outcome and the hosting invoice when they land; build session to place figures and port to motif-build-part3.py

## 2026-09-06 — Eval 3 scored blind and written up
- tried: score all ten blind reports R1→R10 against `docs/ground-truth.md` with the key and metrics closed, one report at a time for user review; then open `eval3/key.json`, join with `eval3/metrics.csv` and the run verdicts, and write `docs/eval3-results.md`.
- happened: ten sheets in `eval3/scoring.md` with seven dated, user-ruled conventions applied identically from the point each was set. Theme sums R1 8.0, R2 10.5, R3 7.5, R4 10.5, R5 9.5, R6 10.0, R7 10.5, R8 11.0, R9 8.5, R10 10.5. Unsupported 0 of 40 spot-checks (fixed positions 1/4/7/10, rule set before scoring), miscalibrated 0 of 171 insights, one under-confidence (R6). Key: control R3/R6/R9, all-v3 R2/R4/R10, opus-critic R5/R8, cap5 R1/R7. Bars 1, 2, 3, 8, 9 pass; 4 and 5 pass unattributed (`duplicate_insight` never fired; control passed P-03 too); 6's rule says adopt on n=2; 7 says do not raise the cap; 10 not run. `second_finding` fired 25 times across the three all-v3 runs and named `david:0022` and `penni:0031` in iteration 1 of each — T-11 and T-15 went 0/3 to 3/3. `critic_pass` reached in 0 of 10 runs at both caps.
- next: v4 items — hand a newly added insight to the counter-evidence search; count a source only when its turn carries the claim; a stopping rule the loop can reach; run bar 10's live pass; `confidence_threshold` scaling.

## 2026-09-06 — Release 0.4.0, the v3 default, shipped everywhere
- tried: ship `second_finding`, `critic_citation`, `duplicate_receipt` as default critic rules in `synth/synth.yaml` (`duplicate_insight` and `dissent_at_intake` stay in, commented, per the Eval 3 rulings); confirm and test; publish PyPI 0.4.0; re-authenticate `mcp-publisher` and publish the registry entry; deploy the hosted engine; confirm every surface live; tag the release.
- happened: 52 tests pass with the new defaults. PyPI 0.4.0 built, `twine check` passed, uploaded, verified in a clean venv (`motif --help`, stdio handshake `motif 0.4.0`, five tools). Registry token from 0.3.0 had expired overnight (same gotcha as last release); fresh `login github` device flow, `publish` from `surfaces/mcp/` succeeded; public API confirms 0.4.0 `isLatest: true` alongside 0.2.0 and 0.3.0. Hosted: `fly deploy`, machine `801e44c60de958`, rolling update with no downtime; `/healthz` gained a `version` field (new, sourced from the FastAPI app's own version) and reports `0.4.0` live; one zero-cost probe (`GET` an unknown job id → 404, no model call) confirmed the live service without spending anything. Tagged `v3` on the release commit.
- next: the case study's part-3 draft can now say the free tier runs the shipped v3 default, not the eval instrument; watch for the plugin listing review and the first Fly.io invoice, still open per the part-3 notes.

## 2026-09-07 — Stage-4 demo-recording polish: run-state visibility, American English, one-click check, "Start another"
- tried: fix four plugin-UI items found while reviewing the demo recording sent to Figma review: run state invisible between screens ("Stop following" reads as cancel; the in-flight card only shows on reopen); British spellings throughout the plugin; checking a synthesis' own report takes four manual steps; "New run" reads as "restart" now that a third mode exists. No publish of any kind (PyPI, registry, Fly, or the Figma listing) — Motif is still under Community review.
- happened: `ui.html`/`ui.ts` — Stop following relabelled "Stop watching — run keeps going"; `show()` now refreshes the setup screen's status line every time it's shown (not only at `init`), so returning mid-session reads "A run is going — Follow it." and a genuine reopen still reads "A run is still going from last time."; found and fixed the same-shaped bug where `runBtn.disabled` was never reset on return to the form, leaving Synthesize stuck disabled after a completed run with no reason shown. Added a one-click "Check this synthesis" button on a synthesis result, reusing that run's transcripts from an in-memory-only `resultUploads` (never persisted, so the discard-after-run privacy line still holds); `submitRun()` factored out so it shares the submit/follow path with the form's Run button. Renamed "New run" to "Start another". Swept `Synthesise`/`Synthesising`/`colour`/`grey` to American spelling across `ui.html`, `ui.ts`, `README.md`, and `listing.md`; rule recorded in `CONTRIBUTING.md`. All four verified with mocked job/event routes in Playwright (no real job, no API cost) and the harness scan script at 440/375/320 px across 8 scenarios (3 new): 0 layout issues. Typecheck, `npm test`, `node test/board_render.mjs`, and 52 Python tests all still pass.
- next: publish is on hold for the Community review outcome; once through, push the American-English listing text to the live Figma submission (currently only corrected locally) and re-check the plugin id.

## 2026-09-07 — Motif approved on the Figma Community
- tried: nothing — this is Figma's ruling on the 2026-09-06 submission, after the demo recording Mya W. (request 2115698) asked for.
- happened: approved 20:25 CDT. Listing live: https://www.figma.com/community/plugin/1678295978273812914. Link and "live 2026-09-07" recorded in `README.md`, `surfaces/figma/README.md`, and `surfaces/figma/listing.md` (§ Status); review exchange written up in `docs/part3-notes.md`.
- next: two Figma-side actions still open, both for the user to take directly (Manage plugins → Motif, since these touch the live listing): push the American-English copy already corrected in `listing.md` to the live listing text, and publish the four stage-4 UI fixes (`0edcf5f`) as a new plugin version. PyPI, the MCP registry, and the hosted engine are untouched — nothing changed there.

## 2026-09-08
- Tried: replace the screenshot-derived Community listing assets with generated ETOT frames, and spec the plugin panel restyle onto the chassis.
- Happened: six frames generated from `listing.py` and exported; restyle spec written against `ui.html`/`ui.ts` and reconciled with `chassis.py`; listing description rewritten in the how-to register; demo shot list written.
- Next: Sonnet 5 session applies `docs/specs/plugin-restyle.md`; then publish version 3 and swap the listing assets and text.

## 2026-09-08 — Plugin restyle applied
- Tried: apply `docs/specs/plugin-restyle.md` (ETOT chassis onto the panel: chassis type/color/hairlines, panel's own type scale, dark theme via Figma's `figma-dark` class, embedded chassis fonts) touching only `ui.css` (the spec's "`<style>` block" — `ui.html` only holds a build-time placeholder for it), `build.mjs` (fonts), and confirming `code.ts` §2 (already done, no edit needed); then the full §8 QA gate.
- Happened: `code.ts` needed no change (`themeColors:true` already present). Five Latin-subset chassis fonts fetched and embedded as base64 `@font-face` in `build.mjs`; `dist/ui.html` 48.5 KB → 133.9 KB. Found and fixed one real bug the automated scan missed: `.insight summary` as the spec's literal 3-column grid collapsed a contested insight's title to one character per line at 320px (fixed with a wrapping flexbox instead — same visual grouping, robust to the badge count). QA gate: 10 screens × 3 widths × 2 themes, 0 layout issues; resume-card check passed; fonts render with all non-local network blocked; all six §8.5 contrast pairs pass (one, light `red`/`panel` at 4.20:1, flagged as borderline if judged as body text rather than a chip); screenshots and the scan JSON in `docs/exhibits/stage4-restyle/`. Details and every number: `docs/part3-notes.md`.
- Next: §8.8 — the panel in the real Figma desktop app, both themes, is Eric's hand check; not done until that's run. Then, separately: push the restyle as a new plugin version, and the still-open American-English listing-text push from the 2026-09-07 approval.
