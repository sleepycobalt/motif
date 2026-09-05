"""
Remote mode: forward tool calls to the hosted Motif service instead of running
the engine in-process. Selected by MOTIF_REMOTE_URL.

The hosted service is a job API (surfaces/hosted/app.py): submit, follow the
event stream, fetch. This module wraps that into calls shaped like the local
tools, so surfaces/mcp/server.py returns the same result either way. In
remote mode a tool's `run_id` is the hosted job id: the only handle the
service gives out, valid until the job expires (an hour after it finishes).

Key: the user's ANTHROPIC_API_KEY (environment or .env) is forwarded as the
`X-Motif-Key` header and used for that job only. MOTIF_REMOTE_TOKEN, if set,
selects the paid tier instead (Authorization: Bearer).

Nothing about the transcripts is logged on this side: no bodies, no names,
only the job id and progress lines the engine emits.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

from synth.ingest import _source_files

Emit = Callable[[str], None] | None


class RemoteUnavailable(RuntimeError):
    pass


def _url(path: str) -> str:
    base = os.environ.get("MOTIF_REMOTE_URL", "").rstrip("/")
    if not base:
        raise RemoteUnavailable("MOTIF_REMOTE_URL is not set")
    return base + path


def _headers() -> dict:
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    token = os.environ.get("MOTIF_REMOTE_TOKEN")
    key = os.environ.get("ANTHROPIC_API_KEY")
    if token:
        h["Authorization"] = f"Bearer {token}"
    elif key:
        h["X-Motif-Key"] = key
    return h


def _request(method: str, path: str, payload: dict | None = None, timeout: float = 120):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(_url(path), data=data, method=method, headers=_headers())
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode("utf-8")).get("detail")
        except Exception:  # noqa: BLE001
            detail = None
        raise RemoteUnavailable(f"hosted Motif service returned {e.code} for {path}: {detail or e.reason}") from None
    except (urllib.error.URLError, OSError) as e:
        raise RemoteUnavailable(f"hosted Motif service unreachable at {_url(path)}: {e}") from None


def _call(method: str, path: str, payload: dict | None = None, timeout: float = 120) -> dict:
    with _request(method, path, payload, timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    if not isinstance(body, dict):
        raise RemoteUnavailable(f"hosted Motif service returned a non-object for {path}")
    return body


def _follow(job_id: str, emit: Emit) -> None:
    """Consume the job's event stream until the service says it ended."""
    since = 0
    while True:
        with _request("GET", f"/v1/jobs/{job_id}/events?since={since}", timeout=90) as resp:
            event, data = None, None
            for raw in resp:
                line = raw.decode("utf-8").rstrip("\n")
                if line.startswith("id:"):
                    since = int(line[3:].strip())
                elif line.startswith("event:"):
                    event = line[6:].strip()
                elif line.startswith("data:"):
                    data = line[5:].strip()
                elif line == "":
                    if data is not None:
                        if event == "end":
                            return
                        if emit:
                            emit(json.loads(data).get("message", ""))
                    event, data = None, None
        # stream closed without an end event (proxy idle cut): resume from the last id


def transcripts_payload(source) -> list[dict]:
    """Raw transcript files (a folder or a list of paths) as the service's upload shape."""
    files = _source_files(source)
    if not files:
        raise ValueError(f"no transcripts found in {source}")
    return [{"name": f.name, "bytes_b64": base64.b64encode(f.read_bytes()).decode("ascii")} for f in files]


def run_job(payload: dict, emit: Emit = None) -> dict:
    """Submit, follow, fetch. Returns the finished job's public record; a failed job raises."""
    job_id = _call("POST", "/v1/jobs", payload)["job_id"]
    if emit:
        emit(f"hosted job {job_id} submitted")
    _follow(job_id, emit)
    job = _call("GET", f"/v1/jobs/{job_id}")
    if job.get("state") != "done":
        raise RemoteUnavailable(f"hosted job {job_id} {job.get('state')}: {job.get('error') or 'no result'}")
    if not job.get("result"):
        raise RemoteUnavailable(f"hosted job {job_id} finished with no result")
    return job


def _as_tool_result(job: dict) -> dict:
    """The local tool's shape, with run_id = the hosted job id (the handle later calls need)."""
    return {**job["result"], "hosted_run_id": job.get("run_id"), "run_id": job["job_id"]}


def synthesize(source, *, question: str | None, condition: str, max_iterations: int | None, emit: Emit = None) -> dict:
    job = run_job({"kind": "synthesize", "transcripts": transcripts_payload(source), "question": question,
                   "condition": condition, "max_iterations": max_iterations}, emit)
    return _as_tool_result(job)


def critique(*, insights, document, run_id: str | None, source, transcripts: list[str] | None,
             question: str | None, structure_with_model: bool, emit: Emit = None) -> dict:
    payload = {"kind": "critique", "insights": insights, "document": document, "question": question,
               "transcripts_subset": transcripts, "structure_with_model": structure_with_model}
    if run_id:
        payload["corpus_job_id"] = run_id
    elif source:
        payload["transcripts"] = transcripts_payload(source)
    else:
        raise ValueError("give run_id (a hosted job id) or transcripts_dir")
    job = run_job(payload, emit)
    return _as_tool_result(job)


def receipts(run_id: str, turn_ids: list[str], transcripts: list[str] | None = None) -> dict:
    return _call("POST", f"/v1/jobs/{run_id}/receipts", {"turn_ids": turn_ids, "transcripts": transcripts})


def get_run(run_id: str, include: list[str] | None = None) -> dict:
    q = f"?include={','.join(include)}" if include else ""
    return _call("GET", f"/v1/jobs/{run_id}/run{q}")


def board(run_id: str, columns: int = 2, origin_x: float = 0, origin_y: float = 0) -> dict:
    return _call("GET", f"/v1/jobs/{run_id}/board?columns={columns}&origin_x={origin_x}&origin_y={origin_y}")
