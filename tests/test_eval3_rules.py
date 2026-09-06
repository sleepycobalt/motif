"""Offline tests for the Eval 3 changes, driven through the real critic path with a stubbed model.

Every test loads one of the actual condition configs from eval3/configs/, so what is tested is what
the paid runs will use. The control config must behave exactly as v2.1-eval: each new rule is checked
both for firing when its condition enables it and for staying silent under control.
"""

import json
from pathlib import Path

import pytest
import yaml

from core import llm
from synth import agents, engine, prompts
from synth.corpus import Corpus
from tests.test_engine import ALICE, BOB, GOOD_INSIGHTS, happy, make_stub

ROOT = Path(__file__).resolve().parent.parent
CONFIGS = ROOT / "eval3" / "configs"


@pytest.fixture
def raw(tmp_path):
    d = tmp_path / "raw"
    d.mkdir()
    (d / "alice.txt").write_text(ALICE)
    (d / "bob.txt").write_text(BOB)
    return d


@pytest.fixture
def corpus(raw, tmp_path):
    return Corpus(engine.ingest(raw, tmp_path / "processed"))


def cfg(name):
    return engine.load_cfg(CONFIGS / f"{name}.yaml")


def rules_of(c):
    return {r["id"] for r in c["critic"]["rules"]}


def fired(failures, rule):
    return [f for f in failures if f["rule"] == rule]


# --------------------------------------------------------------- the configs

def test_control_is_the_frozen_instrument():
    """control.yaml must be synth/synth.yaml as tagged; the other three differ only where stated."""
    base = yaml.safe_load((ROOT / "synth" / "synth.yaml").read_text())
    ctl = yaml.safe_load((CONFIGS / "control.yaml").read_text())
    assert ctl == base
    assert not ctl.get("features")
    assert rules_of(ctl) == rules_of(base)
    for name, key, value in [("opus-critic", ("models", "critic"), "claude-opus-5"),
                             ("cap5", ("loop", "max_iterations"), 5)]:
        c = yaml.safe_load((CONFIGS / f"{name}.yaml").read_text())
        assert c[key[0]][key[1]] == value
        assert rules_of(c) == rules_of(base) and not c.get("features"), f"{name} changed more than its one knob"
        # everything else identical
        stripped = json.loads(json.dumps(c))
        stripped[key[0]][key[1]] = base[key[0]][key[1]]
        assert stripped == base
    allv3 = yaml.safe_load((CONFIGS / "all-v3.yaml").read_text())
    assert rules_of(allv3) - rules_of(base) == {"second_finding", "duplicate_insight",
                                                "duplicate_receipt", "critic_citation"}
    assert allv3["features"]["dissent_at_intake"] is True
    assert allv3["models"] == base["models"] and allv3["loop"] == base["loop"]


# ------------------------------------------------- (c) duplicate_receipt

def test_duplicate_receipt_fires_only_under_all_v3(corpus):
    ins = json.loads(json.dumps(GOOD_INSIGHTS))
    ins[0]["evidence"].append(dict(ins[0]["evidence"][0]))          # same turn cited twice
    ins = agents.normalise(corpus, ins)

    f = agents.deterministic_checks(corpus, ins, cfg("all-v3")["critic"]["rules"])
    dup = fired(f, "duplicate_receipt")
    assert len(dup) == 1 and dup[0]["insight_id"] == "I-01" and dup[0]["severity"] == "warn"
    assert "alice:0002" in dup[0]["detail"] and dup[0]["turns"] == ["alice:0002"]
    # warn does not block a pass
    assert not any(x["severity"] == "fail" for x in dup)

    assert fired(agents.deterministic_checks(corpus, ins, cfg("control")["critic"]["rules"]),
                 "duplicate_receipt") == []


def test_duplicate_receipt_silent_on_clean_insights(corpus):
    ins = agents.normalise(corpus, json.loads(json.dumps(GOOD_INSIGHTS)))
    assert fired(agents.deterministic_checks(corpus, ins, cfg("all-v3")["critic"]["rules"]),
                 "duplicate_receipt") == []


# --------------------------------------------------- dedupe / duplicate_insight

def test_duplicate_insight_flags_a_near_duplicate_pair(corpus):
    ins = json.loads(json.dumps(GOOD_INSIGHTS))
    ins.append({**json.loads(json.dumps(ins[0])), "id": "I-03",
                "title": "Anonymisation labour is unfunded",
                "claim": "Anonymising interview data is unfunded labour and takes weeks."})
    ins = agents.normalise(corpus, ins)

    dup = fired(agents.deterministic_checks(corpus, ins, cfg("all-v3")["critic"]["rules"]), "duplicate_insight")
    assert len(dup) == 1 and dup[0]["severity"] == "warn"
    assert "I-01" in dup[0]["detail"] and "I-03" in dup[0]["detail"]
    assert fired(agents.deterministic_checks(corpus, ins, cfg("control")["critic"]["rules"]),
                 "duplicate_insight") == []


def test_duplicate_insight_silent_on_distinct_insights(corpus):
    ins = agents.normalise(corpus, json.loads(json.dumps(GOOD_INSIGHTS)))
    assert fired(agents.deterministic_checks(corpus, ins, cfg("all-v3")["critic"]["rules"]),
                 "duplicate_insight") == []


# ------------------------------------------- (a) critic_citation, real critic path

def bad_critic(label):
    """A critic that objects while citing an interviewer turn and a turn that does not exist."""
    if label.startswith("critic"):
        return {"pass": False, "notes": "n",
                "failures": [{"insight_id": "I-01", "rule": "missing_counterexample", "severity": "fail",
                              "detail": "ignores the interviewer's summary",
                              "turns": ["alice:0001", "alice:0002", "nobody:0009"]}]}
    return happy(label)


def test_critic_citation_strips_bad_turns_before_revision(corpus, monkeypatch):
    """alice:0001 is an Interviewer turn and nobody:0009 does not exist; neither may reach the reviser."""
    monkeypatch.setattr(llm, "call", make_stub(bad_critic))
    ins = agents.normalise(corpus, json.loads(json.dumps(GOOD_INSIGHTS)))
    assert corpus.is_researcher("alice:0001") and not corpus.has("nobody:0009")

    v = agents.critique(corpus, cfg("all-v3"), None, "Q?", ins)
    obj = next(f for f in v["failures"] if f["rule"] == "missing_counterexample")
    assert obj["turns"] == ["alice:0002"]
    warn = fired(v["failures"], "critic_citation")
    assert len(warn) == 1 and warn[0]["severity"] == "warn"
    assert "alice:0001 (interviewer)" in warn[0]["detail"] and "nobody:0009 (no such turn)" in warn[0]["detail"]
    # the objection itself still stands: a stripped citation is not a dismissed objection
    assert v["pass"] is False

    under_control = agents.critique(corpus, cfg("control"), None, "Q?", ins)
    obj_c = next(f for f in under_control["failures"] if f["rule"] == "missing_counterexample")
    assert obj_c["turns"] == ["alice:0001", "alice:0002", "nobody:0009"]
    assert fired(under_control["failures"], "critic_citation") == []


def test_critic_citation_silent_when_the_critic_cites_well(corpus, monkeypatch):
    def good(label):
        if label.startswith("critic"):
            return {"pass": False, "notes": "n",
                    "failures": [{"insight_id": "I-01", "rule": "overconfident", "severity": "fail",
                                  "detail": "d", "turns": ["alice:0002"]}]}
        return happy(label)
    monkeypatch.setattr(llm, "call", make_stub(good))
    ins = agents.normalise(corpus, json.loads(json.dumps(GOOD_INSIGHTS)))
    v = agents.critique(corpus, cfg("all-v3"), None, "Q?", ins)
    assert fired(v["failures"], "critic_citation") == []


# ------------------------------------------------------- dissent_at_intake

def test_dissent_at_intake_changes_intake_and_critic_prompts(corpus, monkeypatch):
    captured = []
    monkeypatch.setattr(llm, "call", make_stub(happy, captured))
    notes = agents.intake(corpus, cfg("all-v3"), None)
    intake_prompt = next(c["user"] for c in captured if c["label"].startswith("intake_"))
    assert "most other researchers" in intake_prompt and "2-5 entries" in intake_prompt

    notes["alice"]["dissent_or_unusual"] = [
        {"point": "sharing raw data is safer than summaries", "turn": "alice:0004",
         "against": "raw data is the risky part"}]
    captured.clear()
    ins = agents.normalise(corpus, json.loads(json.dumps(GOOD_INSIGHTS)))
    agents.critique(corpus, cfg("all-v3"), None, "Q?", ins, intake_notes=notes)
    critic_prompt = next(c["user"] for c in captured if c["label"].startswith("critic"))
    assert "POSITIONS EACH PARTICIPANT HOLDS THAT MOST OTHERS DO NOT" in critic_prompt
    assert "sharing raw data is safer than summaries" in critic_prompt
    assert "against the majority view that raw data is the risky part" in critic_prompt


def test_control_keeps_the_v21_prompts(corpus, monkeypatch):
    captured = []
    monkeypatch.setattr(llm, "call", make_stub(happy, captured))
    notes = agents.intake(corpus, cfg("control"), None)
    intake_prompt = next(c["user"] for c in captured if c["label"].startswith("intake_"))
    assert intake_prompt == prompts.INTAKE_USER.format(
        name="alice", profile=f"; {corpus.meta['alice']['turns']} turns; {corpus.meta['alice']['words']} words",
        transcript=corpus.text["alice"])

    captured.clear()
    ins = agents.normalise(corpus, json.loads(json.dumps(GOOD_INSIGHTS)))
    agents.critique(corpus, cfg("control"), None, "Q?", ins, intake_notes=notes)
    critic_prompt = next(c["user"] for c in captured if c["label"].startswith("critic"))
    assert "POSITIONS EACH PARTICIPANT HOLDS" not in critic_prompt
    assert "second_finding" not in critic_prompt
    critic_system = next(c["system"] for c in captured if c["label"].startswith("critic"))
    assert "second_finding" not in critic_system


def test_second_finding_reaches_the_critic_only_under_all_v3(corpus, monkeypatch):
    captured = []
    monkeypatch.setattr(llm, "call", make_stub(happy, captured))
    ins = agents.normalise(corpus, json.loads(json.dumps(GOOD_INSIGHTS)))
    agents.critique(corpus, cfg("all-v3"), None, "Q?", ins)
    system = next(c["system"] for c in captured if c["label"].startswith("critic"))
    assert "second_finding" in system and "SECOND, distinct finding" in system
    # deterministic rules must not leak into the model's rule list
    assert "duplicate_insight" not in system and "critic_citation" not in system


# ------------------------------------------------- (b) unevaluated sections

DOC = """# Findings

## I-01 — Anonymisation is unfunded labour

**Claim:** Anonymising interview data takes weeks and is not budgeted.
**Confidence:** medium
**Sources:** alice, bob
**Evidence:** alice:0002, bob:0002
**Counter-evidence:** none
**Opportunity:** Budget it.

```
  receipt alice:0002: "the anonymisation work takes weeks and nobody funds it"
  receipt bob:0002: "Anonymisation takes weeks of work and the funder gave us no budget line"
```

## Key Opportunities

- Add an anonymisation budget line to the DMP template.
- Name a first point of contact on the repository page.
- Fund a shared anonymisation service.

## Next steps

Run a pilot with two teams next quarter.
"""


def test_unevaluated_sections_are_reported_not_absorbed(raw, tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "call", make_stub(happy))
    processed = engine.ingest(raw, tmp_path / "processed")
    out = engine.critique_document(DOC, processed, cfg=cfg("all-v3") | {"features": {"report_unevaluated_sections": True}},
                                   runs_root=tmp_path / "runs")
    secs = out["unevaluated_sections"]
    assert [s["heading"] for s in secs] == ["Key Opportunities", "Next steps"]
    assert secs[0]["items"] == 3 and secs[1]["items"] is None and secs[1]["lines"] == 1
    assert out["verdict"]["unevaluated_sections"] == secs
    assert "were not evaluated" in out["verdict"]["notes"] and "Key Opportunities (3 items)" in out["verdict"]["notes"]
    # the claim count is untouched: the section became neither a claim nor an opportunity field
    assert len(out["insights"]) == 1 and out["insights"][0]["id"] == "I-01"
    assert out["insights"][0]["opportunity"] == "Budget it."


def test_unevaluated_sections_off_by_default(raw, tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "call", make_stub(happy))
    processed = engine.ingest(raw, tmp_path / "processed")
    out = engine.critique_document(DOC, processed, cfg=cfg("control"), runs_root=tmp_path / "runs")
    assert "unevaluated_sections" not in out and "unevaluated_sections" not in out["verdict"]


def test_a_findings_only_document_reports_nothing_unevaluated(raw, tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "call", make_stub(happy))
    processed = engine.ingest(raw, tmp_path / "processed")
    doc = DOC.split("## Key Opportunities")[0]
    out = engine.critique_document(doc, processed, cfg=cfg("all-v3") | {"features": {"report_unevaluated_sections": True}},
                                   runs_root=tmp_path / "runs")
    assert "unevaluated_sections" not in out


# ------------------------------------------------------- the whole loop

def test_all_v3_config_runs_the_whole_loop(raw, tmp_path, monkeypatch):
    """The real loop on the real config: every new rule is wired and nothing crashes."""
    def critic_with_second_finding(label):
        if label.startswith("critic"):
            return {"pass": False, "notes": "n",
                    "failures": [{"insight_id": "*", "rule": "second_finding", "severity": "warn",
                                  "detail": "bob:0004 also says he did not know who to ask",
                                  "turns": ["bob:0004"]}]}
        return happy(label)
    monkeypatch.setattr(llm, "call", make_stub(critic_with_second_finding))
    processed = engine.ingest(raw, tmp_path / "processed")
    res = engine.synthesize(processed, question="Q?", config_path=CONFIGS / "all-v3.yaml",
                            runs_root=tmp_path / "runs")
    assert res.ok and res.insights
    # warn-only verdicts still pass, and the run records the warning
    v = res.verdicts[-1]
    assert v["pass"] is True and fired(v["failures"], "second_finding")
    assert json.load(open(res.run_dir / "meta.json"))["config"]["features"]["dissent_at_intake"] is True


def test_cap5_config_runs_five_iterations(raw, tmp_path, monkeypatch):
    """A loop that keeps making progress runs to the raised cap: 5 critics, 4 revises."""
    n = {"critic": 0}

    def never_satisfied(label):
        if label.startswith("critic"):
            n["critic"] += 1
            # a different objection each round, so `no_progress` does not fire
            return {"pass": False, "notes": "n",
                    "failures": [{"insight_id": f"I-0{n['critic']}", "rule": "overconfident",
                                  "severity": "fail", "detail": "d", "turns": []}]}
        if label == "revise":
            return {"insights": json.loads(json.dumps(GOOD_INSIGHTS)), "dropped": []}
        return happy(label)
    monkeypatch.setattr(llm, "call", make_stub(never_satisfied))
    processed = engine.ingest(raw, tmp_path / "processed")
    res = engine.synthesize(processed, question="Q?", config_path=CONFIGS / "cap5.yaml",
                            runs_root=tmp_path / "runs")
    assert res.iterations == 5 and res.stop_reason == "max_iterations"
    assert len(list((res.run_dir / "calls").glob("*critic*.json"))) == 5
    assert len(list((res.run_dir / "calls").glob("*revise*.json"))) == 4


def test_no_progress_still_stops_the_raised_cap(raw, tmp_path, monkeypatch):
    """The cap-5 condition keeps `no_progress`: a critic repeating itself stops the loop at 2, not 5.
    Found by the first version of the test above, whose stubbed revise changed nothing."""
    monkeypatch.setattr(llm, "call", make_stub(lambda label: (
        {"pass": False, "notes": "n", "failures": [{"insight_id": "I-01", "rule": "overconfident",
                                                    "severity": "fail", "detail": "d", "turns": []}]}
        if label.startswith("critic") else happy(label))))
    processed = engine.ingest(raw, tmp_path / "processed")
    res = engine.synthesize(processed, question="Q?", config_path=CONFIGS / "cap5.yaml",
                            runs_root=tmp_path / "runs")
    assert res.iterations == 2 and res.stop_reason == "no_progress"
