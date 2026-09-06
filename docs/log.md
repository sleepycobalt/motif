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
