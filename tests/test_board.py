import json

from synth import board

INS = [
    {"id": "I-01", "title": "Anonymisation is unfunded labour", "claim": "It takes weeks.", "confidence": "medium",
     "evidence": [{"turn": "alice:0002", "quote": "takes weeks"}, {"turn": "bob:0002", "quote": "no budget line"}],
     "counter_evidence": [{"turn": "alice:0004", "quote": "library were brilliant"}], "counter_note": "Alice had help.",
     "opportunity": "Budget for it.", "sources": ["alice", "bob"]},
    {"id": "I-02", "title": "Guidance is hard to find", "claim": "Bob never found guidance.", "confidence": "low",
     "evidence": ["bob:0004"], "counter_evidence": [], "opportunity": "", "critic_flags": ["unsupported: too strong"]},
]


def test_layout_shape():
    lay = board.layout(INS, {"run_id": "r1"}, columns=2)
    assert lay["n_sections"] == 2 and lay["run_id"] == "r1"
    s0, s1 = lay["sections"]
    roles = [s["role"] for s in s0["stickies"]]
    assert roles == ["claim", "receipt", "receipt", "counter", "opportunity"]
    assert s0["stickies"][0]["color"] == board.STICKY["claim_medium"] and s0["stickies"][0]["wide"]
    assert s0["connectors"] == [{"from": "claim", "to": "counter0", "label": "contested by"}]
    assert "Alice had help." in s0["stickies"][3]["text"] and "“takes weeks”" in s0["stickies"][1]["text"]
    assert s0["turns"] == ["alice:0002", "bob:0002", "alice:0004"]
    # second section: low confidence colour, plain-id evidence, contested sticky, no opportunity, next column
    assert s1["stickies"][0]["color"] == board.STICKY["claim_low"]
    assert "(no receipt)" in s1["stickies"][1]["text"]
    assert [s["role"] for s in s1["stickies"]] == ["claim", "receipt", "contested"]
    assert s1["x"] == board.SECTION_W + board.GAP and s1["y"] == 0 and s1["connectors"] == []


def test_scripts_are_self_contained_js():
    lay = board.layout(INS, {"run_id": "r1"})
    sc = board.scripts(lay)
    assert [s["insight_id"] for s in sc] == ["I-01", "I-02"]
    code = sc[0]["code"]
    assert code.startswith("// Motif board section I-01")
    assert "figma.createSection()" in code and "figma.createConnector()" in code and "return {" in code
    assert "figma.createPage" not in code and "console.log" not in code and "closePlugin" not in code
    spec = json.loads(code.split("const S = ", 1)[1].split(";\n", 1)[0])
    assert spec["insight_id"] == "I-01" and len(spec["stickies"]) == 5
    assert all(s["chars"] < 50000 for s in sc)


def test_verdict_layout_shape():
    from synth import board
    insights = [{"id": "I-01", "title": "A", "claim": "a", "evidence": [{"turn": "x:0001", "quote": "q"}]},
                {"id": "I-02", "title": "B", "claim": "b", "evidence": []}]
    verdict = {"pass": False, "failures": [
        {"insight_id": "I-01", "rule": "unsupported", "severity": "fail", "detail": "no", "turns": ["x:0001"]},
        {"insight_id": "I-01", "rule": "vague_opportunity", "severity": "warn", "detail": "meh"},
        {"insight_id": "*", "rule": "missing_theme", "severity": "fail", "detail": "topic T", "turns": ["y:0002"]}],
        "skipped_rules": []}
    lay = board.verdict_layout(insights, verdict, {"run_id": "r1", "config": {"question": "Q?"}})
    assert lay["kind"] == "verdict" and lay["n_sections"] == 3
    s1, s2, s3 = lay["sections"]
    assert s1["stickies"][0]["color"] == board.VERDICT_STICKY["claim_fail"] and len(s1["stickies"]) == 3
    assert [s["row"] for s in s1["stickies"]] == [1, 2, 2]
    assert s2["stickies"][0]["color"] == board.VERDICT_STICKY["claim_pass"] and len(s2["stickies"]) == 1
    assert s3["insight_id"] == "*" and "MISSING_THEME" in s3["stickies"][0]["text"]
    assert lay["card"] == {"run_id": "r1", "question": "Q?", "transcripts": [], "words": None, "condition": None,
                           "iterations": None, "stop_reason": None, "cost": None, "wall_seconds": None,
                           "started": None, "claims": 2, "pass": False, "fails": 2, "warns": 1, "skipped_rules": []}
    # scripts honour explicit rows
    assert "rowOf" in board.scripts(lay)[0]["code"]


def test_synthesis_layout_has_card():
    from synth import board
    lay = board.layout([{"id": "I-01", "title": "A", "claim": "a", "confidence": "low", "evidence": [], "critic_flags": ["x"]}],
                       {"run_id": "r2", "config": {"question": "Q", "transcripts": ["a", "b"]}, "iterations": 2,
                        "stop_reason": "critic_pass", "cost": 1.5, "wall_seconds": 60.0})
    assert lay["kind"] == "synthesis" and lay["card"]["insights"] == 1 and lay["card"]["contested"] == ["I-01"]
    assert lay["card"]["transcripts"] == ["a", "b"] and lay["card"]["cost"] == 1.5
