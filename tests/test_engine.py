"""Offline tests for synth.engine with a stubbed model. No API calls, no cost."""

import json
from pathlib import Path

import pytest

from core import llm
from synth import engine

ROOT = Path(__file__).resolve().parent.parent

ALICE = """Interviewer: Tell me about sharing your data.
Alice: I would love to share my interview data but the anonymisation work takes weeks and nobody funds it.
Interviewer: Anything else?
Alice: Our library team were absolutely brilliant when I asked about the repository.
"""
BOB = """Interviewer: Tell me about sharing your data.
Bob: Anonymisation takes weeks of work and the funder gave us no budget line for it at all.
Interviewer: Did you find guidance?
Bob: I never found any guidance and I did not know who to ask.
"""


@pytest.fixture
def raw(tmp_path):
    d = tmp_path / "raw"
    d.mkdir()
    (d / "alice.txt").write_text(ALICE)
    (d / "bob.txt").write_text(BOB)
    return d


GOOD_INSIGHTS = [
    {"id": "I-01", "title": "Anonymisation is unfunded labour",
     "claim": "Anonymising interview data takes weeks and is not budgeted.",
     "evidence": [{"turn": "alice:0002", "quote": "the anonymisation work takes weeks and nobody funds it"},
                  {"turn": "bob:0002", "quote": "Anonymisation takes weeks of work and the funder gave us no budget line"}],
     "confidence": "medium", "counter_evidence": [], "counter_note": "",
     "opportunity": "Add an anonymisation budget line to the data management plan template."},
    {"id": "I-02", "title": "Guidance is hard to find",
     "claim": "Bob, a researcher with no library contact, never found guidance.",
     "evidence": [{"turn": "bob:0004", "quote": "I never found any guidance and I did not know who to ask"}],
     "confidence": "low",
     "counter_evidence": [{"turn": "alice:0004", "quote": "Our library team were absolutely brilliant"}],
     "counter_note": "Alice found the library helpful.",
     "opportunity": "Name a first point of contact on the repository landing page."},
]


def make_stub(responses, captured=None):
    """responses: callable(label) -> data dict. captured collects prompts per label."""
    def fake_call(*, model, system, user, max_tokens=8000, json_out=True, logger=None, label="call"):
        data = responses(label)
        if captured is not None:
            captured.append({"label": label, "system": system, "user": user})
        result = {"label": label, "model": model, "text": json.dumps(data) if data is not None else "??",
                  "data": data, "in_tok": 10, "out_tok": 5, "cost": 0.0, "seconds": 0.0,
                  "stop_reason": "end_turn", "block_types": ["text"]}
        if data is None:
            result["json_error"] = "no JSON found in response"
        if logger:
            logger.record_call(label, system, user, result)
        return result
    return fake_call


def happy(label):
    if label.startswith("intake_"):
        name = label.split("_", 1)[1]
        return {"name": name, "profile_summary": f"{name} is a researcher.",
                "topics": [{"topic": "anonymisation cost", "turns": [f"{name}:0002"], "note": "weeks of work"}],
                "notable_positions": [], "dissent_or_unusual": []}
    if label.startswith("synthesis"):
        return {"insights": json.loads(json.dumps(GOOD_INSIGHTS))}
    if label.startswith("critic"):
        return {"pass": True, "failures": [], "notes": "all good"}
    if label == "revise":
        return {"insights": [], "dropped": []}
    raise AssertionError(f"unexpected label {label}")


def test_ingest_and_synthesize_layout(raw, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(llm, "call", make_stub(happy))
    lines = []
    processed = engine.ingest(raw, tmp_path / "processed", emit=lines.append)
    assert (processed / "manifest.json").exists() and (processed / "alice.jsonl").exists()

    res = engine.synthesize(processed, question="Q?", runs_root=tmp_path / "runs", emit=lines.append)
    assert res.ok and res.stop_reason == "critic_pass" and res.iterations == 1
    assert [i["sources"] for i in res.insights] == [["alice", "bob"], ["bob"]]
    d = res.run_dir
    for rel in ("meta.json", "output.json", "output.md", "notes.txt", "corpus/manifest.json",
                "corpus/alice.txt", "corpus/bob.jsonl", "iterations/00_produce.json", "iterations/01_check.json"):
        assert (d / rel).exists(), rel
    assert len(list((d / "calls").glob("*.json"))) == 4  # 2 intake + synthesis + critic
    meta = json.load(open(d / "meta.json"))
    assert meta["corpus"]["transcripts"] == ["alice", "bob"] and meta["stop_reason"] == "critic_pass"
    assert "Anonymisation is unfunded labour" in res.markdown
    # nothing on stdout: the MCP server owns stdout
    assert capsys.readouterr().out == ""
    assert any("critic_pass" in ln for ln in lines)


def test_default_emit_goes_to_stderr_not_stdout(raw, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(llm, "call", make_stub(happy))
    processed = engine.ingest(raw, tmp_path / "processed")
    engine.synthesize(processed, runs_root=tmp_path / "runs")
    out, err = capsys.readouterr()
    assert out == "" and "critic_pass" in err


def test_empty_synthesis_is_a_failure(raw, tmp_path, monkeypatch):
    def empty(label):
        return {} if label.startswith("synthesis") else happy(label)
    monkeypatch.setattr(llm, "call", make_stub(empty))
    processed = engine.ingest(raw, tmp_path / "processed")
    res = engine.synthesize(processed, runs_root=tmp_path / "runs")
    assert not res.ok and res.stop_reason == "synthesis_failed"
    assert res.verdicts and res.verdicts[0]["failures"][0]["rule"] == "empty_synthesis"


def test_ingest_empty_dir_raises(tmp_path):
    (tmp_path / "empty").mkdir()
    with pytest.raises(ValueError):
        engine.ingest(tmp_path / "empty", tmp_path / "p")


def test_bad_condition_raises(raw, tmp_path):
    processed = engine.ingest(raw, tmp_path / "processed")
    with pytest.raises(ValueError):
        engine.synthesize(processed, condition="Z", runs_root=tmp_path / "runs")


def test_critique_rejects_empty_or_malformed(raw, tmp_path):
    processed = engine.ingest(raw, tmp_path / "processed")
    with pytest.raises(ValueError):
        engine.critique([], processed, runs_root=tmp_path / "runs")
    with pytest.raises(ValueError):
        engine.critique([{"id": "I-01"}], processed, runs_root=tmp_path / "runs")


def test_critique_json_path_and_missing_theme_skipped(raw, tmp_path, monkeypatch):
    captured = []
    monkeypatch.setattr(llm, "call", make_stub(happy, captured))
    processed = engine.ingest(raw, tmp_path / "processed")
    out = engine.critique(GOOD_INSIGHTS, processed, runs_root=tmp_path / "runs")
    v = out["verdict"]
    assert v["pass"] is True and v["skipped_rules"] == ["missing_theme"] and v["question_assumed"]
    assert "missing_theme" not in captured[0]["system"]  # rule not shown to the model without intake maps
    assert out["summary"]["n_fail"] == 0 and out["source_format"] == "json"
    assert Path(out["run_dir"]).name.startswith(out["run_id"]) and "-critique" in out["run_id"]
    assert (Path(out["run_dir"]) / "corpus" / "manifest.json").exists()
    # with intake notes the rule stays in
    captured.clear()
    notes = {"alice": happy("intake_alice"), "bob": happy("intake_bob")}
    out2 = engine.critique(GOOD_INSIGHTS, processed, intake_notes=notes, runs_root=tmp_path / "runs")
    assert out2["verdict"]["skipped_rules"] == [] and "missing_theme" in captured[0]["system"]


def test_critique_deterministic_rules_still_fire(raw, tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "call", make_stub(happy))
    processed = engine.ingest(raw, tmp_path / "processed")
    bad = json.loads(json.dumps(GOOD_INSIGHTS))
    bad[0]["evidence"][0]["quote"] = "words that are not in the turn at all"
    bad[0]["confidence"] = "high"
    bad[1]["evidence"] = [{"turn": "bob:0003", "quote": "Did you find guidance?"}]  # interviewer turn
    out = engine.critique(bad, processed, runs_root=tmp_path / "runs")
    rules = out["summary"]["by_rule"]
    assert "quote_mismatch" in rules and "confidence_threshold" in rules and "interviewer_cited" in rules
    assert out["verdict"]["pass"] is False


def test_critic_without_verdict_is_a_failure(raw, tmp_path, monkeypatch):
    def mute(label):
        return None if label.startswith("critic") else happy(label)
    monkeypatch.setattr(llm, "call", make_stub(mute))
    processed = engine.ingest(raw, tmp_path / "processed")
    out = engine.critique(GOOD_INSIGHTS, processed, runs_root=tmp_path / "runs")
    assert out["verdict"]["pass"] is False
    assert "critic_error" in out["summary"]["by_rule"]


R5 = ROOT / "eval2" / "blind" / "R5.md"


@pytest.mark.skipif(not R5.exists(), reason="eval2 blind report not present")
def test_parse_motif_markdown_r5():
    ins = engine.parse_motif_markdown(R5.read_text(encoding="utf-8"))
    assert len(ins) == 15
    assert [i["id"] for i in ins][:3] == ["I-01", "I-02", "I-03"]
    first = ins[0]
    assert first["title"] == "Metadata cannot substitute for lived context of data collection"
    assert first["claim"].startswith("Researchers argue that qualitative data is inseparable")
    assert first["confidence"] == "medium"
    assert [e["turn"] for e in first["evidence"]] == ["michelle:0028", "stephen:0022"]
    assert first["evidence"][0]["quote"].startswith("it doesn't matter how much metadata")
    assert [c["turn"] for c in first["counter_evidence"]] == ["david:0040"]
    assert first["counter_note"].startswith("David reframes")
    assert first["opportunity"].startswith("Build a mandatory narrative")
    assert all(i["claim"] and i["evidence"] for i in ins)


def test_parse_motif_markdown_rejects_other_text():
    assert engine.parse_motif_markdown("# Some report\n\nJust prose, no insights.\n") == []


def test_critique_document_motif_format(raw, tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "call", make_stub(happy))
    processed = engine.ingest(raw, tmp_path / "processed")
    md = ("# Synthesis\n\n## I-01 — Anonymisation is unfunded labour\n"
          "**Claim:** Anonymising interview data takes weeks and is not budgeted.  \n"
          "**Confidence:** medium  \n**Sources:** alice, bob  \n"
          "**Evidence:** alice:0002, bob:0002  \n**Counter-evidence:** none  \n"
          "**Opportunity:** Budget for it.\n\n<details><summary>Cited turns</summary>\n\n```\n"
          '  receipt alice:0002: "the anonymisation work takes weeks and nobody funds it"\n'
          '  receipt bob:0002: "Anonymisation takes weeks of work"\n```\n</details>\n')
    out = engine.critique_document(md, processed, runs_root=tmp_path / "runs")
    assert out["source_format"] == "motif_markdown"
    assert out["insights"][0]["claim"].startswith("Anonymising") and out["insights"][0]["sources"] == ["alice", "bob"]
    assert out["verdict"]["pass"] is True
    assert (Path(out["run_dir"]) / "input.md").exists()
    assert (Path(out["run_dir"]) / "iterations" / "00_structure.json").exists()


def test_critique_document_model_path_and_empty(raw, tmp_path, monkeypatch):
    def structurer(label):
        if label == "structure":
            return {"insights": json.loads(json.dumps(GOOD_INSIGHTS))}
        return happy(label)
    monkeypatch.setattr(llm, "call", make_stub(structurer))
    processed = engine.ingest(raw, tmp_path / "processed")
    out = engine.critique_document("Researchers said anonymisation takes weeks (alice:0002).",
                                   processed, runs_root=tmp_path / "runs")
    assert out["source_format"] == "model" and len(out["insights"]) == 2
    with pytest.raises(ValueError):
        engine.critique_document("   ", processed, runs_root=tmp_path / "runs")
    monkeypatch.setattr(llm, "call", make_stub(lambda label: {} if label == "structure" else happy(label)))
    with pytest.raises(ValueError):
        engine.critique_document("Some prose with no findings.", processed, runs_root=tmp_path / "runs")


def test_receipts(raw, tmp_path):
    processed = engine.ingest(raw, tmp_path / "processed")
    out = engine.receipts(["alice:0002", "alice:0001", "zed:0001"], processed)
    assert [r["found"] for r in out["receipts"]] == [True, True, False]
    assert out["receipts"][0]["speaker"] == "Alice" and not out["receipts"][0]["interviewer"]
    assert out["receipts"][1]["interviewer"] is True
    assert out["missing"] == ["zed:0001"]
    with pytest.raises(LookupError):
        engine.receipts(["zed:0001"], processed)
    with pytest.raises(ValueError):
        engine.receipts([], processed)


def test_load_run_and_corpus_for_run(raw, tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "call", make_stub(happy))
    processed = engine.ingest(raw, tmp_path / "processed")
    res = engine.synthesize(processed, runs_root=tmp_path / "runs")
    got = engine.load_run(res.run_id, tmp_path / "runs", include=("meta", "notes", "iterations", "verdicts", "calls"))
    assert got["meta"]["stop_reason"] == "critic_pass"
    stages = [i["stage"] for i in got["iterations"]]
    assert stages == ["produce", "check"] and got["iterations"][1]["pass"] is True
    assert got["verdicts"][0]["pass"] is True
    assert {c["label"] for c in got["calls"]} >= {"synthesis", "critic"}
    assert all("user" not in c for c in got["calls"])  # no prompt bodies
    snap, names = engine.corpus_for_run(res.run_id, tmp_path / "runs")
    assert snap == res.run_dir / "corpus" and names is None
    with pytest.raises(LookupError):
        engine.load_run("nope", tmp_path / "runs")


def test_redact_mode_keeps_transcripts_off_disk(raw, tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "call", make_stub(happy))
    processed = engine.ingest(raw, tmp_path / "processed")
    res = engine.synthesize(processed, runs_root=tmp_path / "runs", redact=True)
    assert not (res.run_dir / "corpus").exists()
    call = json.load(open(sorted((res.run_dir / "calls").glob("*.json"))[0]))
    assert set(call["user"]) == {"chars", "sha256"} and "Alice" not in json.dumps(call["user"])
    assert res.meta["redacted"] is True and res.meta["corpus"]["transcripts"] == ["alice", "bob"]


def test_motif_report_round_trips_through_the_critic(raw, tmp_path, monkeypatch):
    """Motif's own report must come back through critique_document with zero mechanical failures:
    receipts for evidence and counter-evidence are printed, parsed, and pass the deterministic checks."""
    from synth.corpus import Corpus
    from synth.report import to_markdown
    monkeypatch.setattr(llm, "call", make_stub(happy))
    processed = engine.ingest(raw, tmp_path / "processed")
    corpus = Corpus(processed)
    ins = json.loads(json.dumps(GOOD_INSIGHTS))
    ins[1]["sources"] = ["bob"]; ins[0]["sources"] = ["alice", "bob"]
    md = to_markdown(ins, corpus, {"run_id": "r", "condition": "C", "iterations": 1, "stop_reason": "critic_pass"})
    assert 'receipt alice:0004: "Our library team were absolutely brilliant"' in md
    parsed = engine.parse_motif_markdown(md)
    assert parsed[1]["counter_evidence"] == [{"turn": "alice:0004", "quote": "Our library team were absolutely brilliant"}]
    out = engine.critique_document(md, processed, runs_root=tmp_path / "runs")
    assert out["source_format"] == "motif_markdown"
    mechanical = [f for f in out["verdict"]["failures"] if f["rule"] in ("quote_mismatch", "bad_citation", "interviewer_cited")]
    assert mechanical == [], mechanical


def test_counter_without_receipt_is_not_a_quote_mismatch(raw, tmp_path, monkeypatch):
    """A pre-2026-09-05 report (no counter receipts) parses to counters with empty quotes; that is absence, not mismatch."""
    monkeypatch.setattr(llm, "call", make_stub(happy))
    processed = engine.ingest(raw, tmp_path / "processed")
    ins = json.loads(json.dumps(GOOD_INSIGHTS))
    ins[1]["counter_evidence"] = [{"turn": "alice:0004", "quote": ""}]
    ins[0]["evidence"][0]["quote"] = ""   # an evidence receipt that is missing still fails
    out = engine.critique(ins, processed, runs_root=tmp_path / "runs")
    qm = [f for f in out["verdict"]["failures"] if f["rule"] == "quote_mismatch"]
    assert [f["insight_id"] for f in qm] == ["I-01"] and "alice:0002" in qm[0]["detail"]
