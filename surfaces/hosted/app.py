"""
Motif hosted engine: the engine module behind one small HTTP service.

    motif-hosted                       # serves on $PORT (default 8080)

Clients: the Figma plugin and the MCP server's remote mode. Both submit a
job, follow its events, and fetch the result by job id.

    POST /v1/jobs                        submit (202 -> {"job_id", "state"})
    GET  /v1/jobs/{id}                   state, and the result once done
    GET  /v1/jobs/{id}/events            text/event-stream of engine progress; ends with event "end"
    GET  /v1/jobs/{id}/board             the run laid out for a board (synthesize jobs)
    POST /v1/jobs/{id}/receipts          verbatim turns from the job's corpus
    GET  /v1/jobs/{id}/run               the redacted run record (meta, notes, iterations, verdicts, calls)
    GET  /healthz

Tiers. Bring-your-own-key: header `X-Motif-Key: <Anthropic key>`; the key is
used for that job only and never logged. Paid: `Authorization: Bearer <token>`
against a credit balance; refused with 403 until MOTIF_PAID_ENABLED=1 and the
rails exist (see credits.py).

Caps on the public path: per-address concurrency and daily count, per-file
and per-job upload size, document length. Every refusal says which cap.

Environment:
    PORT                    listen port (8080)
    MOTIF_RUNS_DIR          redacted run logs (default ~/.motif/runs; /data/runs in the container)
    MOTIF_WORK_DIR          scratch for uploads and processed corpora (system temp)
    MOTIF_CONFIG            YAML config override
    MOTIF_JOB_TTL           seconds a finished job stays fetchable (3600)
    MOTIF_IP_CONCURRENT     jobs running at once per address (2)
    MOTIF_IP_DAILY          jobs per address per 24 h (20)
    MOTIF_MAX_FILE_MB       per transcript file (12)
    MOTIF_MAX_JOB_MB        per job, all files decoded (64)
    MOTIF_PAID_ENABLED      "1" to enable the credit tier (off)
    MOTIF_LEDGER            SQLite path for credits (/data/credits.db)
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import json
import logging
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from synth import engine
from surfaces.hosted import credits
from surfaces.hosted.jobs import CapExceeded, JobStore

log = logging.getLogger("motif.hosted")

MAX_FILES = 40
MAX_DOC_CHARS = 400_000
HEARTBEAT_SECONDS = 15


class Transcript(BaseModel):
    name: str = Field(..., max_length=200)
    bytes_b64: str


class JobRequest(BaseModel):
    kind: str
    transcripts: list[Transcript] | None = None
    corpus_job_id: str | None = None
    question: str | None = Field(default=None, max_length=2000)
    condition: str = "C"
    max_iterations: int | None = Field(default=None, ge=1, le=6)
    # critique
    insights: list[dict[str, Any]] | None = None
    document: str | None = None
    transcripts_subset: list[str] | None = None
    intake_notes: dict[str, Any] | None = None
    structure_with_model: bool = False


class ReceiptsRequest(BaseModel):
    turn_ids: list[str] = Field(..., min_length=1, max_length=500)
    transcripts: list[str] | None = None


def _env_int(name: str, default: int) -> int:
    return int(os.environ.get(name) or default)


def _default_runs_root() -> Path:
    if (engine.ROOT / "pyproject.toml").exists():
        return engine.ROOT / "runs"
    return Path.home() / ".motif" / "runs"


def store_from_env() -> JobStore:
    paid = os.environ.get("MOTIF_PAID_ENABLED", "") in ("1", "true", "yes")
    ledger = credits.Ledger(os.environ.get("MOTIF_LEDGER") or "/data/credits.db") if paid else None
    return JobStore(os.environ.get("MOTIF_RUNS_DIR") or _default_runs_root(),
                    ttl_seconds=_env_int("MOTIF_JOB_TTL", 3600),
                    per_ip_concurrent=_env_int("MOTIF_IP_CONCURRENT", 2),
                    per_ip_daily=_env_int("MOTIF_IP_DAILY", 20),
                    config_path=os.environ.get("MOTIF_CONFIG") or None,
                    work_dir=os.environ.get("MOTIF_WORK_DIR") or None, ledger=ledger)


def client_ip(request: Request) -> str:
    h = request.headers
    return (h.get("fly-client-ip") or (h.get("x-forwarded-for") or "").split(",")[0].strip()
            or (request.client.host if request.client else "?"))


def create_app(store: JobStore | None = None, *, max_file_mb: int | None = None, max_job_mb: int | None = None) -> FastAPI:
    store = store or store_from_env()
    max_file = (max_file_mb or _env_int("MOTIF_MAX_FILE_MB", 12)) * 1_000_000
    max_job = (max_job_mb or _env_int("MOTIF_MAX_JOB_MB", 64)) * 1_000_000
    app = FastAPI(title="Motif hosted engine", version="0.3.0", docs_url=None, redoc_url=None)
    app.state.store = store
    # The Figma plugin's UI runs in a sandboxed iframe whose origin is "null", so the browser
    # sends a CORS preflight for every call. The key travels in a request header, never a cookie,
    # so allowing any origin exposes nothing that the caller did not already hold.
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"],
                       allow_headers=["Content-Type", "X-Motif-Key", "Authorization", "Last-Event-ID"],
                       expose_headers=["Content-Type"], max_age=600)

    def job_or_404(job_id: str):
        try:
            return store.get(job_id)
        except LookupError as e:
            raise HTTPException(404, str(e)) from None

    @app.get("/healthz")
    async def healthz() -> dict:
        return {"ok": True, "paid_tier": store.ledger is not None, "jobs": len(store.jobs)}

    @app.post("/v1/jobs", status_code=202)
    async def submit(req: JobRequest, request: Request,
                     x_motif_key: str | None = Header(default=None),
                     authorization: str | None = Header(default=None)) -> dict:
        ip = client_ip(request)
        if x_motif_key:
            tier, user, api_key = "byok", None, x_motif_key
        elif authorization and store.ledger is not None:
            tier, user, api_key = "paid", _paid_user(authorization), None
        else:
            raise HTTPException(403, "This service runs on your own Anthropic key: send it in the X-Motif-Key "
                                     "header. The paid tier is not available yet.")
        if req.kind not in ("synthesize", "critique"):
            raise HTTPException(400, "kind must be 'synthesize' or 'critique'")
        if req.kind == "synthesize" and req.condition not in engine.CONDITIONS:
            raise HTTPException(400, f"condition must be one of {sorted(engine.CONDITIONS)}")
        if req.document is not None and len(req.document) > MAX_DOC_CHARS:
            raise HTTPException(413, f"document is {len(req.document):,} characters; the limit is {MAX_DOC_CHARS:,}")
        transcripts = None
        if not req.corpus_job_id:
            if not req.transcripts:
                raise HTTPException(400, "give transcripts (name + bytes_b64) or corpus_job_id")
            if len(req.transcripts) > MAX_FILES:
                raise HTTPException(413, f"{len(req.transcripts)} files; the limit is {MAX_FILES} per job")
            transcripts, total = [], 0
            for t in req.transcripts:
                try:
                    data = base64.b64decode(t.bytes_b64, validate=True)
                except (binascii.Error, ValueError):
                    raise HTTPException(400, f"{t.name}: bytes_b64 is not valid base64") from None
                if len(data) > max_file:
                    raise HTTPException(413, f"{t.name} is {len(data) / 1e6:.1f} MB; the per-file limit is "
                                             f"{max_file / 1e6:.0f} MB")
                total += len(data)
                if total > max_job:
                    raise HTTPException(413, f"transcripts total more than {max_job / 1e6:.0f} MB; split the job")
                transcripts.append((t.name, data))
        params = {"question": req.question, "condition": req.condition, "max_iterations": req.max_iterations,
                  "insights": req.insights, "document": req.document, "transcripts": req.transcripts_subset,
                  "intake_notes": req.intake_notes, "structure_with_model": req.structure_with_model}
        try:
            job = store.submit(kind=req.kind, ip=ip, tier=tier, api_key=api_key, user=user,
                               transcripts=transcripts, corpus_job_id=req.corpus_job_id, params=params)
        except CapExceeded as e:
            raise HTTPException(429, str(e)) from None
        except LookupError as e:
            raise HTTPException(404, str(e)) from None
        except ValueError as e:
            raise HTTPException(400, str(e)) from None
        log.info("job %s submitted: %s, %s tier", job.id[:8], job.kind, job.tier)
        return {"job_id": job.id, "state": job.state}

    @app.get("/v1/jobs/{job_id}")
    async def get_job(job_id: str) -> dict:
        return job_or_404(job_id).public()

    @app.get("/v1/jobs/{job_id}/events")
    async def events(job_id: str, since: int = 0, last_event_id: str | None = Header(default=None)) -> StreamingResponse:
        job = job_or_404(job_id)
        if last_event_id and last_event_id.isdigit():
            since = int(last_event_id)

        async def gen():
            idx = since
            while True:
                new, idx, finished = await asyncio.to_thread(job.wait, idx, HEARTBEAT_SECONDS)
                for i, msg in enumerate(new, start=idx - len(new) + 1):
                    yield f"id: {i}\ndata: {json.dumps({'message': msg})}\n\n"
                if finished and idx >= len(job.events):
                    yield f"event: end\ndata: {json.dumps({'state': job.state, 'error': job.error})}\n\n"
                    return
                if not new:
                    yield ": keep-alive\n\n"

        return StreamingResponse(gen(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @app.get("/v1/jobs/{job_id}/board")
    async def board(job_id: str, columns: int = 2, origin_x: float = 0, origin_y: float = 0) -> dict:
        job = job_or_404(job_id)
        if job.state != "done" or not job.run_id:
            raise HTTPException(409, f"job {job_id} is {job.state}; a board needs a finished job")
        try:
            return await asyncio.to_thread(engine.board, job.run_id, store.runs_root, max(1, columns), (origin_x, origin_y))
        except LookupError as e:
            raise HTTPException(404, str(e)) from None

    @app.post("/v1/jobs/{job_id}/receipts")
    async def receipts(job_id: str, req: ReceiptsRequest) -> dict:
        job = job_or_404(job_id)
        if not job.processed or not (job.processed / "manifest.json").exists():
            raise HTTPException(409, f"job {job_id} has no corpus yet")
        try:
            return await asyncio.to_thread(engine.receipts, req.turn_ids, job.processed, req.transcripts)
        except LookupError as e:
            raise HTTPException(404, str(e)) from None
        except ValueError as e:
            raise HTTPException(400, str(e)) from None

    @app.get("/v1/jobs/{job_id}/run")
    async def run_record(job_id: str, include: str | None = None) -> dict:
        job = job_or_404(job_id)
        if not job.run_id:
            raise HTTPException(409, f"job {job_id} has no run record yet")
        inc = tuple(sorted(set((include or "meta,notes,iterations,verdicts").split(",")) | {"meta"}))
        try:
            return await asyncio.to_thread(engine.load_run, job.run_id, store.runs_root, inc)
        except LookupError as e:
            raise HTTPException(404, str(e)) from None

    if store.ledger is not None:
        @app.get("/v1/credits/me")
        async def credits_me(authorization: str | None = Header(default=None)) -> dict:
            user = _paid_user(authorization)
            return {"user": user, "balance_cents": store.ledger.balance(user)}

        @app.post("/v1/stripe/webhook", status_code=501)
        async def stripe_webhook() -> dict:
            raise HTTPException(501, "payment rails are not built yet")

    return app


def _paid_user(authorization: str | None) -> str:
    """Paid-tier identity. Placeholder until the plugin's signed token exists: a bearer token is the user id."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "paid tier needs Authorization: Bearer <token>")
    return authorization[7:].strip()


app = create_app() if os.environ.get("MOTIF_HOSTED_AUTOCREATE", "1") == "1" else None


def main() -> None:
    import uvicorn
    logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s %(message)s")
    uvicorn.run("surfaces.hosted.app:app", host="0.0.0.0", port=int(os.environ.get("PORT") or 8080),
                log_level="info", timeout_keep_alive=75)


if __name__ == "__main__":
    main()
