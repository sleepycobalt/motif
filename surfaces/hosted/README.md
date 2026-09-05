# Motif hosted engine

The engine module (`synth/engine.py`) behind one small HTTP service, so surfaces
without a Python runtime can use it: the Figma plugin, and the MCP server in
remote mode. Nothing about prompts, models, or the loop lives here; the service
is a job runner around the same engine the CLI calls.

## Tiers

**Bring your own key.** Send your Anthropic key in the `X-Motif-Key` header.
It is bound to that job's model calls and dropped when the job ends; it is
never written to disk or to a log. Unlimited runs, on your own bill.

**Paid credits.** Not switched on. The ledger and metering exist
(`credits.py`), the payment rails do not; the service refuses any job that
does not carry a key until `MOTIF_PAID_ENABLED=1` and the prerequisites in
`docs/specs/motif-figma-plugin.md` are met. No unpaid run ever uses ETOT's key.

## API

```
POST /v1/jobs                    submit                    -> 202 {"job_id", "state": "queued"}
GET  /v1/jobs/{id}               state; the result when done
GET  /v1/jobs/{id}/events        text/event-stream of engine progress; final event "end"
GET  /v1/jobs/{id}/board         the run laid out for a board (synthesize jobs); ?columns=&origin_x=&origin_y=
POST /v1/jobs/{id}/receipts      {"turn_ids": [...]} -> verbatim turns from the job's corpus
GET  /v1/jobs/{id}/run           the redacted run record; ?include=meta,notes,iterations,verdicts,calls
GET  /healthz
```

Submit body:

```json
{"kind": "synthesize",
 "transcripts": [{"name": "michelle.docx", "bytes_b64": "..."}],
 "question": "What frustrates users about onboarding?",
 "condition": "C", "max_iterations": 3}
```

```json
{"kind": "critique",
 "insights": [...]            or  "document": "...markdown or prose...",
 "transcripts": [...]         or  "corpus_job_id": "<a live job whose corpus to reuse>",
 "question": "...", "transcripts_subset": ["michelle"], "structure_with_model": false}
```

Transcripts are raw files (`.docx`, `.txt`, `.md`); ingest runs here. Events are
the engine's own progress lines, one per `data:` line with an `id:` so a
client can resume with `Last-Event-ID` or `?since=`; a keep-alive comment goes
out every 15 s. A job that produces nothing, whose critic returns no verdict,
or that raises, ends `failed` with the message. There is no `done` with empty
content.

Job ids are random and are the only handle to a job's content. A finished job
stays fetchable for `MOTIF_JOB_TTL` seconds (default one hour), then its
uploads, processed corpus, and the run's output files are deleted.

## What is stored

- During a job and its TTL: the uploads and processed corpus, on the machine's
  scratch disk (never on the volume).
- Permanently, on the volume: the redacted run record. Prompt and response
  bodies are stored as length and SHA-256; token counts, timings, cost, stop
  reason, the critic's verdict summaries, and notes remain. That is the
  metering record, and it holds no transcript text.

## Caps (public path)

| Cap | Default | Env |
|---|---|---|
| jobs running at once per address | 2 | `MOTIF_IP_CONCURRENT` |
| jobs per address per 24 h | 20 | `MOTIF_IP_DAILY` |
| per transcript file | 12 MB | `MOTIF_MAX_FILE_MB` |
| per job, all files | 64 MB | `MOTIF_MAX_JOB_MB` |
| files per job | 40 | |
| critique document | 400,000 chars | |

The sample corpus's `.docx` files are about 6 MB each because they embed
fonts; the text inside is a few hundred KB. Every refusal names the cap.

## Run locally

```bash
cd /path/to/motif
.venv/bin/python -m pip install -e ".[hosted]"
MOTIF_RUNS_DIR=/tmp/motif-runs PORT=8080 .venv/bin/motif-hosted
curl -s localhost:8080/healthz
```

Point the MCP server at it: `MOTIF_REMOTE_URL=http://localhost:8080 motif-mcp`
(the server forwards `ANTHROPIC_API_KEY` from its environment or `.env` as the
job key).

## Deploy (Fly.io)

From the repository root. The build runs on Fly's builders; no local Docker.

```bash
fly auth login
fly apps create motif-hosted
fly volumes create motif_data --region ord --size 1 -a motif-hosted
fly deploy -c surfaces/hosted/fly.toml
curl -s https://motif-hosted.fly.dev/healthz
```

Later: `fly certs add api.etot.design -a motif-hosted` plus the CNAME it
prints. Secrets: none for the BYOK tier. Switching the paid tier on is
`fly secrets set ANTHROPIC_API_KEY=... MOTIF_PAID_ENABLED=1 -a motif-hosted`,
and is not done until the prerequisites are met.

## Tests

```bash
.venv/bin/python -m pytest -q tests/test_hosted.py
```

Offline, stubbed model: the service through FastAPI's test client, the remote
client against a real port, and the MCP server as a subprocess in remote mode.
