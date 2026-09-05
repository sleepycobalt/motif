# Part 3 build plan — hosted engine, Figma plugin, board writer, listing

*Proposed 2026-09-04 from `docs/specs/motif-figma-plugin.md`, `docs/specs/motif-mcp-server.md`, and `CONTRIBUTING.md`. Status: approved 2026-09-04 (Fly.io; Design renderer at the end of stage 3; Stripe Checkout with an ETOT ledger, designed in stage 1, built when the prerequisites are dated; per-IP concurrency and per-job transcript size caps on the BYOK path; the listing icon comes from the Motif field thumbnail, supplied by the user). Stage 1 in progress.*

## The shape in one paragraph

One hosted Python service wraps `synth/engine.py` unchanged behind a job-style HTTP API: submit a run, stream its progress, fetch its result and its board layout. The MCP server's remote mode and the Figma plugin are two clients of that service. The plugin's free tier forwards the user's own Anthropic key with each job; the paid tier uses ETOT's key against a prepaid credit ledger and stays behind a server-side flag until the spec's prerequisites are met. The plugin draws the board itself from the same layout data `motif_board` already produces, so `synth/board.py::layout` stays the single source of truth for what a Motif board looks like.

## Constraints found in the code and specs

- **Per-request keys.** `core/llm.py` holds one module-level `Anthropic()` client built from the environment. A hosted service serving BYOK jobs needs the key per request, held in memory for that job only. Engine change: a `contextvars.ContextVar` for the client in `core/llm.py`, set by the service per job, defaulting to the environment as today. The CLI and MCP local mode do not change.
- **Runs are long.** From `docs/part2-notes.md`: the refactor regression took 440.9 s; the recorded 15-transcript run took 2,064.6 s and cost $4.88. A single HTTP request that long dies at every proxy. Hence a job model: submit, then stream, then fetch. A plugin window that closes mid-run can pick the job up again by id.
- **Nothing stored.** The spec's privacy line ("transcripts processed for the run and discarded; nothing stored") maps to what the logger already has: `redact=True` keeps token counts and timings and stores prompt bodies as digests, and skips the corpus snapshot. The processed corpus lives in the job's memory for the job plus a short TTL so the client can fetch receipts and the board, then is dropped. Redacted run logs are kept for metering and debugging; they contain no transcript text.
- **Two Figma editors, two renderers.** Stickies and connectors are FigJam plugin-API nodes; the Design editor has sections but not stickies. The plugin's board writer therefore has a FigJam renderer first and a Design renderer (frames and text) as a separate step. The layout data is identical for both.
- **Consumable credits.** Figma's payments API sells one-time purchases or subscriptions, not a depleting balance. Credits therefore need a ledger ETOT owns, topped up by Stripe Checkout through a webhook. This matches the spec's "or Stripe via the plugin UI" fallback. To verify against Figma's docs when stage 4 starts.
- **`surfaces/mcp/remote.py` changes.** Its draft contract is one synchronous call per tool. It becomes a client of the job API below. It already promises "the hosted service is not live yet; fails loudly", so nothing shipped depends on the old shape.

## Architecture

```
Figma plugin (TS)                     Claude Code / Cursor (MCP host)
  ui.ts  ── fetch/SSE ──┐               motif-mcp --remote ──┐
  code.ts (board writer)│                                    │
                        ▼                                    ▼
             ┌──────────────────────────────────────────────────┐
             │  surfaces/hosted/  (FastAPI, one container)       │
             │  POST /v1/jobs            submit synth/critique   │
             │  GET  /v1/jobs/{id}/events  SSE progress          │
             │  GET  /v1/jobs/{id}       result: insights, md,   │
             │                           verdicts, cost          │
             │  GET  /v1/jobs/{id}/board layout JSON             │
             │  POST /v1/jobs/{id}/receipts  verbatim turns      │
             │  GET  /v1/credits/me      balance (paid, flagged) │
             │  POST /v1/stripe/webhook  top-up   (paid, flagged)│
             │                                                   │
             │  synth/engine.py   redact=True, in-memory corpus  │
             │  core/llm.py       key from job context           │
             └──────────────────────────────────────────────────┘
                                   │ ANTHROPIC key: user's (BYOK) or ETOT's (paid)
                                   ▼
                              Anthropic API
```

**Service (`surfaces/hosted/`).** FastAPI plus uvicorn, one process, a worker thread per job (the engine is synchronous, same as the MCP server's `_in_thread`). Job registry in memory with a TTL sweep; redacted run logs on a volume under `MOTIF_RUNS_DIR`. Progress: the engine's `emit` callable appends to the job's event queue, which the SSE endpoint drains with a heartbeat every 15 s so proxies keep the stream open. Auth per job: header `X-Motif-Key` carrying the user's Anthropic key (BYOK), or `Authorization: Bearer <figma user token>` (paid, later). The key is read into the job context, never logged, never echoed. Failure semantics as everywhere in Motif: an empty synthesis, a missing verdict, or a parse failure ends the job in state `failed` with the message, never `done` with empty content.

Request shapes:

```
POST /v1/jobs
  {"kind": "synthesize", "transcripts": [{"name": "michelle.docx", "bytes_b64": "..."}],
   "question": "...", "condition": "C", "max_iterations": 3}
  {"kind": "critique", "document": "...markdown...", "transcripts": [...], "question": "..."}
  -> 202 {"job_id": "20260904-183000-C", "state": "queued"}

GET /v1/jobs/{id}/events        text/event-stream; one `data:` line per engine emit; final event `state: done|failed`
GET /v1/jobs/{id}               {"state", "insights", "markdown", "verdicts", "contested", "cost", "seconds", "error"}
GET /v1/jobs/{id}/board?columns=2&origin_x=0&origin_y=0   the dict `synth/board.py::layout` returns
POST /v1/jobs/{id}/receipts     {"turn_ids": [...]} -> same shape as `motif_receipts`
```

Ingest runs server-side (python-docx is already a dependency), so the plugin never parses documents. Transcripts travel as base64 file bytes. The sample corpus's `.docx` files are about 6 MB each because they embed fonts (the text inside totals 620 KB), so the caps are 12 MB per file and 64 MB per job, and stage 2 should consider extracting paragraphs in the plugin before upload.

**Plugin (`surfaces/figma/`).** TypeScript, built with esbuild into `code.js` (main thread) and `ui.html` (iframe). No framework: the UI is a drop zone, a question field, a tier switch, a progress log, and one button. Manifest: `editorType: ["figjam", "figma"]`, `networkAccess.allowedDomains` set to the service host only, `documentAccess: "dynamic-page"`. The Anthropic key lives in `figma.clientStorage` and is read in `code.ts`, passed to the iframe only at submit time, and sent only in the request header to the service. `code.ts` owns the board writer; `ui.ts` owns the network. They talk over `postMessage` with a typed message set.

**Board writer.** `code.ts` receives the layout dict and renders it: `figma.createSection` per insight, `figma.createSticky` per sticky with the pinned palette from `synth/board.py::STICKY`, `figma.createConnector` for "contested by" links, one run card sticky at the origin. Font load before any text. Every render returns the node ids it created and fails if any sticky is missing, mirroring the `use_figma` scripts' contract. The Design-editor renderer maps sticky to a fixed-size frame with a text child and connector to a line, same positions.

**Paid tier (designed, dormant).** Server flag `MOTIF_PAID_ENABLED=false` hides the credits endpoints and refuses any job without a BYOK key. When on: the plugin sends `figma.currentUser.id` signed by a short-lived token the service issues; a `credits` table (SQLite on the volume) holds balance in cents; a job first reserves an estimate (words × a per-word rate calibrated from the two runs above, at 2× API cost or more), refuses if the balance is short, then settles the actual cost at finish. Stripe Checkout sells fixed bundles; the webhook credits the ledger. No path exists for a paid job without a positive reserved balance. The listing's FAQ, terms, and support address are part of switching the flag on, not of building it.

## Build order

**Stage 1 — hosted engine service.** `core/llm.py` context-var client; `surfaces/hosted/app.py`, `jobs.py`, `Dockerfile`; `surfaces/mcp/remote.py` rewritten to the job API and wired to the five tools; offline tests with the stubbed model through FastAPI's test client (submit, stream, result, board, receipts, every failure path). Deploy one container with a volume. QA gate: from a laptop, the MCP server in remote mode synthesises the sample corpus against the deployed service and the report comes back; the service's run directory holds a redacted log and no transcript text. Deliverable numbers into `docs/part3-notes.md`: job duration, cost, and the size of the redacted run dir.

**Stage 2 — plugin, free tier only.** Scaffold, manifest, key entry and storage, transcript drop, question, submit to the service, live progress from the SSE stream, result summary in the UI (insight count, contested ids, cost) and the report markdown copied to the clipboard. No board yet. QA gate: a fresh FigJam file, development plugin loaded from the repo, one run on the sample corpus on a personal key, install to result under ten minutes, UI checked at desktop and phone widths for clipping and overflow.

**Stage 3 — board writer.** FigJam renderer from the layout endpoint; run card; contested marking; then the critique mode (paste a summary, get the verdict as stickies, which needs a small `verdict_layout` in `synth/board.py`); then the Design-editor renderer. QA gate: the recorded run's 23 insights rendered in a fresh FigJam file and compared against `docs/exhibits/recorded-run/board-overview.png`; every sticky present; palette colours read back as palette, not CUSTOM.

**Stage 4 — listing assets.** Icon, cover from the I-09 section, four screenshots (board overview, contested section, plugin UI, critique verdict), body copy and FAQ in the register of the best-performing listings, category Research / Whiteboarding. Submit for Community review. First 10 installs and 3 pieces of feedback logged in `docs/part3-notes.md`.

**After the prerequisites — switch on paid.** Entity and bank account, payment rails tested end to end with a real card in Stripe test mode and then one live purchase, support address and response time in the listing, terms and privacy published. Then `MOTIF_PAID_ENABLED=true`, and the first credit purchase logged.

## Decisions needed before stage 1

1. **Hosting platform and hostname.** Recommendation: Fly.io, one shared-CPU machine with a 1 GB volume, at a hostname under etot.design. Railway or Cloud Run would also fit the same container.
2. **Design-editor renderer timing.** Recommendation: end of stage 3, after FigJam is verified, since the spec names FigJam as primary.
3. **Payment rails.** Recommendation: Stripe Checkout plus an ETOT ledger, for the consumable-credits reason above. Designed in stage 1's data model, built and tested only when the prerequisites are dated.

## Open items

- The listing icon ("the field thumbnail, reduced") is not in the repo; needs a source file.
- Rate limiting for BYOK jobs: the service spends no ETOT money on them, but a public endpoint needs a per-IP cap on concurrent jobs. Proposed: 2 concurrent, 20 per day, adjustable.
- The MCP server's remote mode and the plugin share the job API, so `surfaces/mcp/README.md` gains a remote-mode section in stage 1.
