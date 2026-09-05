"""Offline tests for the hosted engine service, its remote client, and the MCP server in remote mode.
The model is stubbed (tests.test_engine.make_stub); jobs run on worker threads inside this process."""

import base64
import json
import os
import socket
import sys
import threading
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core import llm
from surfaces.hosted import credits
from surfaces.hosted.app import create_app
from surfaces.hosted.jobs import JobStore
from surfaces.mcp import remote
from tests.test_engine import ALICE, BOB, GOOD_INSIGHTS, happy, make_stub

ROOT = Path(__file__).resolve().parent.parent
KEY = {"X-Motif-Key": "sk-test-not-used"}


def b64(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


TRANSCRIPTS = [{"name": "alice.txt", "bytes_b64": b64(ALICE)}, {"name": "bob.txt", "bytes_b64": b64(BOB)}]


@pytest.fixture
def store(tmp_path):
    return JobStore(tmp_path / "runs", ttl_seconds=3600, per_ip_concurrent=2, per_ip_daily=5,
                    work_dir=str(tmp_path))


@pytest.fixture
def client(store, monkeypatch):
    monkeypatch.setattr(llm, "call", make_stub(happy))
    return TestClient(create_app(store, max_file_mb=1, max_job_mb=1))


def follow(client, job_id) -> tuple[list[str], dict]:
    """Read the SSE stream to its end event. Returns (messages, end payload)."""
    msgs, end = [], None
    with client.stream("GET", f"/v1/jobs/{job_id}/events") as r:
        assert r.status_code == 200 and r.headers["content-type"].startswith("text/event-stream")
        event = None
        for line in r.iter_lines():
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                d = json.loads(line[5:])
                if event == "end":
                    end = d
                    break
                msgs.append(d["message"])
                event = None
    assert end is not None, "stream ended without an end event"
    return msgs, end


def wait_done(client, job_id, timeout=20) -> dict:
    t0 = time.time()
    while time.time() - t0 < timeout:
        j = client.get(f"/v1/jobs/{job_id}").json()
        if j["state"] in ("done", "failed"):
            return j
        time.sleep(0.05)
    raise AssertionError("job did not finish")


# ------------------------------------------------------------------ service

def test_synthesize_job_end_to_end(client, store):
    r = client.post("/v1/jobs", json={"kind": "synthesize", "transcripts": TRANSCRIPTS, "question": "Q?"}, headers=KEY)
    assert r.status_code == 202, r.text
    job_id = r.json()["job_id"]
    msgs, end = follow(client, job_id)
    assert end["state"] == "done" and end["error"] is None
    assert any("critic_pass" in m for m in msgs) and any("alice" in m for m in msgs)

    j = client.get(f"/v1/jobs/{job_id}").json()
    res = j["result"]
    assert j["state"] == "done" and j["words"] > 0 and res["n_insights"] == 2 and res["contested"] == []
    assert res["stop_reason"] == "critic_pass" and "Anonymisation is unfunded labour" in res["report_markdown"]

    # redacted run: digests instead of prompt bodies, no corpus snapshot, no transcript text on the runs volume
    run_dir = store.runs_root / j["run_id"]
    meta = json.load(open(run_dir / "meta.json"))
    assert meta["redacted"] is True and not (run_dir / "corpus").exists()
    call = json.load(open(sorted((run_dir / "calls").glob("*.json"))[0]))
    assert set(call["user"]) == {"chars", "sha256"}
    for f in (run_dir / "calls").glob("*.json"):
        assert "anonymisation work takes weeks" not in f.read_text(), f"transcript text leaked into {f.name}"

    # board, receipts, run record by job id
    b = client.get(f"/v1/jobs/{job_id}/board?columns=1").json()
    assert [s["insight_id"] for s in b["board"]["sections"]] == ["I-01", "I-02"] and len(b["scripts"]) == 2
    rc = client.post(f"/v1/jobs/{job_id}/receipts", json={"turn_ids": ["alice:0002", "nobody:0001"]}).json()
    assert rc["receipts"][0]["found"] and "weeks" in rc["receipts"][0]["text"] and rc["missing"] == ["nobody:0001"]
    rr = client.get(f"/v1/jobs/{job_id}/run?include=meta,verdicts,calls").json()
    assert rr["meta"]["stop_reason"] == "critic_pass" and rr["verdicts"][0]["pass"] is True and len(rr["calls"]) == 4

    # resuming the stream from an id replays only the rest
    with client.stream("GET", f"/v1/jobs/{job_id}/events", headers={"Last-Event-ID": str(len(msgs) - 1)}) as r:
        lines = [ln for ln in r.iter_lines() if ln.startswith("data:")]
    assert len(lines) == 2  # the last message and the end event


def test_no_key_is_refused_and_paid_tier_is_off(client):
    r = client.post("/v1/jobs", json={"kind": "synthesize", "transcripts": TRANSCRIPTS})
    assert r.status_code == 403 and "X-Motif-Key" in r.json()["detail"]
    r = client.post("/v1/jobs", json={"kind": "synthesize", "transcripts": TRANSCRIPTS},
                    headers={"Authorization": "Bearer someone"})
    assert r.status_code == 403
    assert client.get("/healthz").json()["paid_tier"] is False
    assert client.get("/v1/credits/me").status_code == 404


def test_input_caps(client):
    big = {"name": "big.txt", "bytes_b64": b64("Alice: " + "word " * 300_000)}
    r = client.post("/v1/jobs", json={"kind": "synthesize", "transcripts": [big]}, headers=KEY)
    assert r.status_code == 413 and "per-file limit" in r.json()["detail"]
    half = {"name": "h.txt", "bytes_b64": b64("Alice: " + "word " * 120_000)}
    r = client.post("/v1/jobs", json={"kind": "synthesize", "transcripts": [half, dict(half, name="h2.txt")]}, headers=KEY)
    assert r.status_code == 413 and "split the job" in r.json()["detail"]
    r = client.post("/v1/jobs", json={"kind": "synthesize", "transcripts": [{"name": "x.pdf", "bytes_b64": b64("hi")}]}, headers=KEY)
    assert r.status_code == 400 and ".docx" in r.json()["detail"]
    r = client.post("/v1/jobs", json={"kind": "synthesize", "transcripts": []}, headers=KEY)
    assert r.status_code == 400
    r = client.post("/v1/jobs", json={"kind": "synthesize", "transcripts": [{"name": "x.txt", "bytes_b64": "!!"}]}, headers=KEY)
    assert r.status_code == 400 and "base64" in r.json()["detail"]
    r = client.post("/v1/jobs", json={"kind": "critique", "document": "x" * 400_001, "transcripts": TRANSCRIPTS}, headers=KEY)
    assert r.status_code == 413
    r = client.post("/v1/jobs", json={"kind": "synthesize", "transcripts": TRANSCRIPTS, "condition": "Z"}, headers=KEY)
    assert r.status_code == 400
    assert client.get("/v1/jobs/nope").status_code == 404


def test_per_ip_concurrency_cap(store, monkeypatch):
    gate = threading.Event()

    def slow(label):
        gate.wait(10)
        return happy(label)
    monkeypatch.setattr(llm, "call", make_stub(slow))
    client = TestClient(create_app(store))
    ids = [client.post("/v1/jobs", json={"kind": "synthesize", "transcripts": TRANSCRIPTS}, headers=KEY).json()["job_id"]
           for _ in range(2)]
    r = client.post("/v1/jobs", json={"kind": "synthesize", "transcripts": TRANSCRIPTS}, headers=KEY)
    assert r.status_code == 429 and "2 at a time" in r.json()["detail"]
    gate.set()
    for i in ids:
        assert wait_done(client, i)["state"] == "done"
    # daily cap: 5 per address in this fixture; 2 used so far (a refused submission does not count)
    for _ in range(3):
        r = client.post("/v1/jobs", json={"kind": "synthesize", "transcripts": TRANSCRIPTS}, headers=KEY)
        assert r.status_code == 202 and wait_done(client, r.json()["job_id"])["state"] == "done"
    r = client.post("/v1/jobs", json={"kind": "synthesize", "transcripts": TRANSCRIPTS}, headers=KEY)
    assert r.status_code == 429 and "24 hours" in r.json()["detail"]


def test_empty_synthesis_fails_the_job(store, monkeypatch):
    monkeypatch.setattr(llm, "call", make_stub(lambda label: {} if label.startswith("synthesis") else happy(label)))
    client = TestClient(create_app(store))
    job_id = client.post("/v1/jobs", json={"kind": "synthesize", "transcripts": TRANSCRIPTS}, headers=KEY).json()["job_id"]
    _, end = follow(client, job_id)
    assert end["state"] == "failed" and "synthesis failed" in end["error"]
    j = client.get(f"/v1/jobs/{job_id}").json()
    assert j["state"] == "failed" and "result" not in j
    assert client.get(f"/v1/jobs/{job_id}/board").status_code == 409


def test_critique_job_and_corpus_reuse(client):
    job_id = client.post("/v1/jobs", json={"kind": "critique", "insights": GOOD_INSIGHTS, "transcripts": TRANSCRIPTS},
                         headers=KEY).json()["job_id"]
    j = wait_done(client, job_id)
    assert j["state"] == "done" and j["result"]["verdict"]["pass"] is True and j["result"]["summary"]["n_fail"] == 0
    assert "missing_theme" in j["result"]["verdict"]["skipped_rules"] and "run_dir" not in j["result"]
    # a second critique on the same corpus, no re-upload
    j2_id = client.post("/v1/jobs", json={"kind": "critique", "insights": GOOD_INSIGHTS, "corpus_job_id": job_id},
                        headers=KEY).json()["job_id"]
    assert wait_done(client, j2_id)["state"] == "done"
    assert client.post("/v1/jobs", json={"kind": "critique", "insights": GOOD_INSIGHTS, "corpus_job_id": "nope"},
                       headers=KEY).status_code == 404
    r = client.post("/v1/jobs", json={"kind": "critique", "transcripts": TRANSCRIPTS}, headers=KEY)
    job_id = r.json()["job_id"]
    assert wait_done(client, job_id)["error"].startswith("give exactly one")


def test_expiry_drops_corpus_and_run_content(tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "call", make_stub(happy))
    store = JobStore(tmp_path / "runs", ttl_seconds=0, work_dir=str(tmp_path))
    client = TestClient(create_app(store))
    job_id = client.post("/v1/jobs", json={"kind": "synthesize", "transcripts": TRANSCRIPTS}, headers=KEY).json()["job_id"]
    job = store.jobs[job_id]
    with job.cond:
        while job.state not in ("done", "failed"):
            job.cond.wait(0.1)
    run_dir = store.runs_root / job.run_id
    assert (run_dir / "output.json").exists() and job.workdir.exists()
    time.sleep(0.01)
    assert client.get(f"/v1/jobs/{job_id}").status_code == 404
    assert not job.workdir.exists() and not (run_dir / "output.json").exists()
    assert (run_dir / "meta.json").exists() and list((run_dir / "calls").glob("*.json"))


# ------------------------------------------------------------------ credits

def test_ledger_reserve_settle_refuse(tmp_path):
    led = credits.Ledger(tmp_path / "credits.db")
    assert led.balance("u1") == 0
    with pytest.raises(credits.InsufficientCredits):
        led.reserve("u1", 100, "j1")
    assert led.add("u1", 2000, "stripe:cs_test") == 2000
    rid = led.reserve("u1", credits.estimate_cents(11_482), "j1")
    assert led.balance("u1") == 2000 - 115
    assert led.settle(rid, credits.settle_cents(0.5529)) == 115 - 111
    assert led.balance("u1") == 2000 - 111
    with pytest.raises(RuntimeError):
        led.settle(rid, 1)
    rid2 = led.reserve("u1", 500, "j2")
    assert led.release(rid2) == 500 and led.balance("u1") == 2000 - 111
    assert credits.estimate_cents(10) == 50  # floor
    with pytest.raises(NotImplementedError):
        credits.stripe_topup()


# --------------------------------------------------------------- remote mode

def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def hosted(store, monkeypatch):
    """The service on a real port in a background thread, model stubbed in this process."""
    import uvicorn
    monkeypatch.setattr(llm, "call", make_stub(happy))
    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(create_app(store), host="127.0.0.1", port=port, log_level="warning"))
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    url = f"http://127.0.0.1:{port}"
    monkeypatch.setenv("MOTIF_REMOTE_URL", url)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-not-used")
    monkeypatch.delenv("MOTIF_REMOTE_TOKEN", raising=False)
    yield url
    server.should_exit = True
    t.join(5)


@pytest.fixture
def raw(tmp_path):
    d = tmp_path / "raw"
    d.mkdir()
    (d / "alice.txt").write_text(ALICE)
    (d / "bob.txt").write_text(BOB)
    return d


def test_remote_client_round_trip(hosted, raw):
    lines = []
    out = remote.synthesize(raw, question="Q?", condition="C", max_iterations=None, emit=lines.append)
    assert out["n_insights"] == 2 and out["stop_reason"] == "critic_pass" and out["run_id"]
    assert lines[0].startswith("hosted job ") and any("critic_pass" in ln for ln in lines)
    job_id = out["run_id"]
    rc = remote.receipts(job_id, ["bob:0004"])
    assert rc["receipts"][0]["found"] and "guidance" in rc["receipts"][0]["text"]
    assert len(remote.board(job_id)["board"]["sections"]) == 2
    assert remote.get_run(job_id, ["meta"])["meta"]["redacted"] is True
    crit = remote.critique(insights=GOOD_INSIGHTS, document=None, run_id=job_id, source=None, transcripts=None,
                           question=None, structure_with_model=False)
    assert crit["verdict"]["pass"] is True
    with pytest.raises(remote.RemoteUnavailable, match="404"):
        remote.receipts("nope", ["bob:0004"])


def test_remote_failure_is_loud(hosted, raw, monkeypatch):
    monkeypatch.setattr(llm, "call", make_stub(lambda label: {} if label.startswith("synthesis") else happy(label)))
    with pytest.raises(remote.RemoteUnavailable, match="synthesis failed"):
        remote.synthesize(raw, question=None, condition="C", max_iterations=None)
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    with pytest.raises(remote.RemoteUnavailable, match="403"):
        remote.synthesize(raw, question=None, condition="C", max_iterations=None)


def test_mcp_server_remote_mode(hosted, raw, tmp_path):
    """The MCP server as a subprocess forwarding to the in-process hosted service."""
    import asyncio
    from mcp.client import Client
    from mcp.client.stdio import StdioServerParameters

    params = StdioServerParameters(command=sys.executable, args=["-m", "surfaces.mcp.server"], cwd=str(ROOT),
                                   env={"MOTIF_REMOTE_URL": hosted, "ANTHROPIC_API_KEY": "sk-test-not-used",
                                        "MOTIF_RUNS_DIR": str(tmp_path / "unused"), "PATH": "/usr/bin:/bin"})

    async def scenario():
        progress = []

        async with Client(params) as client:
            async def on_progress(*a):
                progress.append(a)

            res = await client.call_tool("motif_synthesize", {"transcripts_dir": str(raw), "question": "Q?"},
                                         progress_callback=on_progress)
            assert not res.is_error, res.content
            d = res.structured_content or json.loads(res.content[0].text)
            d = d.get("result", d)
            assert d["n_insights"] == 2 and d["run_id"]
            job_id = d["run_id"]
            r = await client.call_tool("motif_receipts", {"turn_ids": ["alice:0002"], "run_id": job_id})
            assert not r.is_error and "weeks" in r.content[0].text
            r = await client.call_tool("motif_receipts", {"turn_ids": ["alice:0002"], "transcripts_dir": str(raw)})
            assert r.is_error and "run_id" in r.content[0].text
            r = await client.call_tool("motif_board", {"run_id": job_id})
            assert not r.is_error and "I-02" in r.content[0].text
            r = await client.call_tool("motif_runs_get", {"run_id": "nope"})
            assert r.is_error and "404" in r.content[0].text
        assert progress, "no progress notifications reached the host"

    asyncio.run(scenario())
