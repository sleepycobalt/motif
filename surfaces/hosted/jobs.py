"""
Job registry for the hosted engine.

A job is one engine call (synthesize or critique) running on a worker thread.
The caller submits transcripts and parameters, follows progress as events,
and fetches the result, the board layout, and receipts by job id until the
job expires. Job ids are random and are the only handle to a job's content.

What is kept where:
  - the caller's Anthropic key: an argument to the worker thread, bound to the
    engine's per-context client for the duration of the run, never stored on
    the job and never logged;
  - raw uploads and the processed corpus: a temporary directory on the
    machine's scratch disk, deleted when the job expires;
  - the run log: written by the engine under `runs_root` with redact=True
    (prompt bodies as digests, no corpus snapshot). At expiry the run's
    output files (insights and report, which quote the transcripts) are
    removed too, leaving meta, notes, and per-call usage: the metering record.

Silence is never approval: an empty synthesis, a missing verdict, a parse
failure, or an exception ends the job as `failed` with the message.
"""

from __future__ import annotations

import contextlib
import os
import re
import secrets
import shutil
import tempfile
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from core import llm
from synth import engine
from synth.ingest import EXTENSIONS
from surfaces.hosted import credits

KINDS = ("synthesize", "critique")
TERMINAL = ("done", "failed")
SAFE_NAME = re.compile(r"[^A-Za-z0-9._ -]+")


class CapExceeded(RuntimeError):
    pass


@dataclass
class Job:
    id: str
    kind: str
    ip: str
    tier: str                       # "byok" | "paid"
    user: str | None                # paid tier only
    created: float
    state: str = "queued"           # queued | running | done | failed
    events: list = field(default_factory=list)
    result: dict | None = None
    error: str | None = None
    run_id: str | None = None
    words: int | None = None
    finished: float | None = None
    workdir: Path | None = None
    processed: Path | None = None
    reservation: int | None = None
    cond: threading.Condition = field(default_factory=threading.Condition, repr=False)

    def emit(self, msg: str) -> None:
        with self.cond:
            self.events.append(msg)
            self.cond.notify_all()

    def wait(self, since: int, timeout: float) -> tuple[list[str], int, bool]:
        """Events after index `since`, the new index, and whether the job is finished."""
        with self.cond:
            if len(self.events) <= since and self.state not in TERMINAL:
                self.cond.wait(timeout)
            new = self.events[since:]
            return new, since + len(new), self.state in TERMINAL

    def public(self) -> dict:
        out = {"job_id": self.id, "kind": self.kind, "tier": self.tier, "state": self.state,
               "created": self.created, "finished": self.finished, "run_id": self.run_id,
               "words": self.words, "n_events": len(self.events), "error": self.error}
        if self.state == "done":
            out["result"] = self.result
        return out


class JobStore:
    def __init__(self, runs_root: str | Path, *, ttl_seconds: int = 3600, per_ip_concurrent: int = 2,
                 per_ip_daily: int = 20, config_path: str | None = None, work_dir: str | None = None,
                 ledger: credits.Ledger | None = None):
        self.runs_root = Path(runs_root)
        self.runs_root.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl_seconds
        self.per_ip_concurrent = per_ip_concurrent
        self.per_ip_daily = per_ip_daily
        self.config_path = config_path
        self.work_dir = work_dir
        self.ledger = ledger
        self.jobs: dict[str, Job] = {}
        self.daily: dict[str, list[float]] = defaultdict(list)
        self.lock = threading.Lock()

    # ---------------------------------------------------------------- caps

    def _check_caps(self, ip: str) -> None:
        now = time.time()
        running = sum(1 for j in self.jobs.values() if j.ip == ip and j.state not in TERMINAL)
        if running >= self.per_ip_concurrent:
            raise CapExceeded(f"{running} job(s) already running from this address; "
                              f"the limit is {self.per_ip_concurrent} at a time")
        recent = [t for t in self.daily[ip] if now - t < 86400]
        self.daily[ip] = recent
        if len(recent) >= self.per_ip_daily:
            raise CapExceeded(f"{len(recent)} jobs from this address in the last 24 hours; "
                              f"the limit is {self.per_ip_daily}")

    # -------------------------------------------------------------- submit

    def submit(self, *, kind: str, ip: str, tier: str, api_key: str | None, user: str | None,
               transcripts: list[tuple[str, bytes]] | None, corpus_job_id: str | None,
               params: dict) -> Job:
        if kind not in KINDS:
            raise ValueError(f"kind must be one of {KINDS}")
        if tier == "paid" and self.ledger is None:
            raise ValueError("paid tier is not enabled on this service")
        if tier == "byok" and not api_key:
            raise ValueError("bring-your-own-key jobs need an Anthropic key")
        with self.lock:
            self.sweep_locked()
            self._check_caps(ip)
            job = Job(id=secrets.token_urlsafe(18), kind=kind, ip=ip, tier=tier, user=user, created=time.time())
            job.workdir = Path(tempfile.mkdtemp(prefix="motif-job-", dir=self.work_dir))
            if corpus_job_id:
                src = self.jobs.get(corpus_job_id)
                if not src or not src.processed or not (src.processed / "manifest.json").exists():
                    shutil.rmtree(job.workdir, ignore_errors=True)
                    raise LookupError(f"no live job {corpus_job_id} to take the corpus from")
                job.processed = src.processed
            else:
                if not transcripts:
                    shutil.rmtree(job.workdir, ignore_errors=True)
                    raise ValueError("no transcripts given")
                raw = job.workdir / "raw"
                raw.mkdir()
                for name, data in transcripts:
                    safe = SAFE_NAME.sub("_", Path(name).name).strip() or "transcript.txt"
                    if Path(safe).suffix.lower() not in EXTENSIONS:
                        shutil.rmtree(job.workdir, ignore_errors=True)
                        raise ValueError(f"{name}: only {', '.join(EXTENSIONS)} transcripts are accepted")
                    (raw / safe).write_bytes(data)
            self.jobs[job.id] = job
            self.daily[ip].append(job.created)
        t = threading.Thread(target=self._run, args=(job, api_key, params), name=f"motif-job-{job.id[:6]}", daemon=True)
        t.start()
        return job

    # ----------------------------------------------------------------- run

    def _run(self, job: Job, api_key: str | None, params: dict) -> None:
        with job.cond:
            job.state = "running"
        try:
            ctx = llm.using_key(api_key) if api_key else contextlib.nullcontext()
            with ctx:
                if job.processed is None:
                    job.processed = engine.ingest(job.workdir / "raw", job.workdir / "processed", emit=job.emit)
                job.words = self._words(job.processed)
                if job.tier == "paid":
                    job.reservation = self.ledger.reserve(job.user, credits.estimate_cents(job.words), job.id)
                    job.emit(f"reserved {credits.estimate_cents(job.words)} cents for {job.words:,} words")
                if job.kind == "synthesize":
                    job.result = self._synthesize(job, params)
                else:
                    job.result = self._critique(job, params)
            self._settle(job)
            with job.cond:
                job.state = "done"
        except Exception as e:  # noqa: BLE001 — any failure is the job's failure, reported verbatim
            self._settle(job, failed=True)
            with job.cond:
                job.state = "failed"
                job.error = f"{type(e).__name__}: {e}" if not isinstance(e, (ValueError, RuntimeError, LookupError)) else str(e)
        finally:
            with job.cond:
                job.finished = time.time()
                job.cond.notify_all()

    @staticmethod
    def _words(processed: Path) -> int:
        import json
        return sum(m["words"] for m in json.load(open(processed / "manifest.json", encoding="utf-8")))

    def _synthesize(self, job: Job, p: dict) -> dict:
        res = engine.synthesize(job.processed, question=p.get("question"), condition=p.get("condition", "C"),
                                max_iterations=p.get("max_iterations"), config_path=self.config_path,
                                runs_root=self.runs_root, emit=job.emit, redact=True, tag="hosted")
        job.run_id = res.run_id
        if not res.ok:
            raise RuntimeError(f"synthesis failed (stop={res.stop_reason})")
        return {
            "run_id": res.run_id, "stop_reason": res.stop_reason, "iterations": res.iterations,
            "n_insights": len(res.insights),
            "contested": [i["id"] for i in res.insights if i.get("critic_flags")],
            "cost_usd": res.meta.get("cost"), "wall_seconds": res.meta.get("wall_seconds"),
            "insights": res.insights, "report_markdown": res.markdown, "verdicts": res.verdicts,
        }

    def _critique(self, job: Job, p: dict) -> dict:
        insights, document = p.get("insights"), p.get("document")
        if (insights is None) == (document is None):
            raise ValueError("give exactly one of insights (JSON) or document (markdown/prose)")
        common = dict(question=p.get("question"), names=p.get("transcripts"), config_path=self.config_path,
                      runs_root=self.runs_root, emit=job.emit, redact=True)
        if insights is not None:
            insights = [{k: v for k, v in i.items() if k != "critic_flags"} for i in insights]
            out = engine.critique(insights, job.processed, intake_notes=p.get("intake_notes"), **common)
        else:
            out = engine.critique_document(document, job.processed, force_model=bool(p.get("structure_with_model")),
                                           **common)
        job.run_id = out["run_id"]
        out.pop("run_dir", None)
        return out

    def _settle(self, job: Job, failed: bool = False) -> None:
        if job.reservation is None or self.ledger is None:
            return
        try:
            meta = engine.load_run(job.run_id, self.runs_root, ("meta",))["meta"] if job.run_id else {}
            actual = credits.settle_cents(float(meta.get("cost") or 0.0)) if meta.get("calls") else 0
            refund = self.ledger.settle(job.reservation, actual)
            job.emit(f"settled: charged {actual} cents, released {refund}")
        except Exception as e:  # noqa: BLE001
            job.emit(f"settlement error: {e}")

    # ---------------------------------------------------------------- read

    def get(self, job_id: str) -> Job:
        with self.lock:
            self.sweep_locked()
            job = self.jobs.get(job_id)
        if job is None:
            raise LookupError(f"no such job (or it has expired): {job_id}")
        return job

    # --------------------------------------------------------------- sweep

    def sweep_locked(self) -> int:
        """Drop expired jobs: delete their scratch directory and the content files of their run."""
        now = time.time()
        gone = [j for j in self.jobs.values() if j.finished and now - j.finished > self.ttl]
        for j in gone:
            del self.jobs[j.id]
            self._discard(j)
        return len(gone)

    def sweep(self) -> int:
        with self.lock:
            return self.sweep_locked()

    def _discard(self, job: Job) -> None:
        if job.workdir:
            shutil.rmtree(job.workdir, ignore_errors=True)
        if job.run_id:
            run_dir = self.runs_root / job.run_id
            for rel in ("output.json", "output.md", "input.md"):
                with contextlib.suppress(FileNotFoundError):
                    (run_dir / rel).unlink()
            shutil.rmtree(run_dir / "iterations", ignore_errors=True)
