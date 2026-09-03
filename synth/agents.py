"""The three agent roles plus deterministic checks, wired to core.llm."""

import json

from core import llm
from synth import prompts
from synth.corpus import Corpus


def _j(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------- intake

def intake(corpus: Corpus, cfg: dict, logger) -> dict[str, dict]:
    notes = {}
    for name in corpus.names:
        m = corpus.meta[name]
        profile = f"{m.get('naming', '')}; {m['turns']} turns; {m['words']} words"
        r = llm.call(
            model=cfg["models"]["intake"],
            system=prompts.INTAKE_SYSTEM,
            user=prompts.INTAKE_USER.format(name=name, profile=profile, transcript=corpus.text[name]),
            max_tokens=6000,
            logger=logger,
            label=f"intake_{name}",
        )
        notes[name] = r["data"] or {"name": name, "error": r.get("json_error", "no data")}
    return notes


# ------------------------------------------------------------- synthesis

def synthesise(corpus: Corpus, cfg: dict, logger, question: str,
               intake_notes: dict | None = None, single_prompt: bool = False) -> list[dict]:
    s = cfg["synthesis"]
    intake_block = ""
    if intake_notes:
        intake_block = prompts.INTAKE_BLOCK.format(notes=_j(intake_notes))
    r = llm.call(
        model=cfg["models"]["synthesis"],
        system=prompts.SINGLE_PROMPT_SYSTEM if single_prompt else prompts.SYNTHESIS_SYSTEM,
        user=prompts.SYNTHESIS_USER.format(
            question=question, n=len(corpus.names), words=corpus.words,
            intake_block=intake_block, min_insights=s["min_insights"],
            max_insights=s["max_insights"], transcripts=corpus.render_all(),
        ),
        max_tokens=cfg["synthesis"].get("max_tokens", 32000),
        logger=logger,
        label="synthesis_single" if single_prompt else "synthesis",
    )
    return (r["data"] or {}).get("insights", [])


def revise(corpus: Corpus, cfg: dict, logger, question: str,
           insights: list[dict], verdict: dict) -> list[dict]:
    r = llm.call(
        model=cfg["models"]["synthesis"],
        system=prompts.SYNTHESIS_SYSTEM,
        user=prompts.REVISE_USER.format(
            question=question, insights=_j(insights),
            failures=_j(verdict.get("failures", [])),
            notes=verdict.get("notes", ""), transcripts=corpus.render_all(),
        ),
        max_tokens=cfg["synthesis"].get("max_tokens", 32000),
        logger=logger,
        label="revise",
    )
    new = (r["data"] or {}).get("insights")
    return new if new else insights


# ---------------------------------------------------------------- critic

def deterministic_checks(corpus: Corpus, insights: list[dict], rules: list[dict]) -> list[dict]:
    """Rules that need no model: bad citations and single-source generalisation."""
    by_id = {r["id"]: r for r in rules}
    failures = []
    for ins in insights:
        iid = ins.get("id", "?")
        ev = ins.get("evidence", []) or []
        srcs = ins.get("sources", []) or []

        if "bad_citation" in by_id:
            bad = [t for t in ev + (ins.get("counter_evidence") or []) if not corpus.has(t)]
            cited_transcripts = {corpus.transcript_of(t) for t in ev if corpus.has(t)}
            orphan_sources = [s for s in srcs if s not in cited_transcripts]
            if bad or orphan_sources or not ev:
                failures.append({
                    "insight_id": iid, "rule": "bad_citation", "severity": "fail",
                    "detail": f"nonexistent turns={bad}; sources without cited turns={orphan_sources}; "
                              f"evidence_count={len(ev)}",
                    "turns": bad,
                })
                # normalise sources to what is actually cited
                ins["sources"] = sorted(cited_transcripts)

        if "interviewer_cited" in by_id:
            bad_ev = [t for t in ev if corpus.has(t) and corpus.is_researcher(t)]
            if bad_ev:
                failures.append({
                    "insight_id": iid, "rule": "interviewer_cited", "severity": "fail",
                    "detail": f"evidence cites the interviewer, not a participant: {bad_ev}; "
                              f"replace with the participant's own turns",
                    "turns": bad_ev,
                })

        if "single_source_generalisation" in by_id:
            n_sources = len({corpus.transcript_of(t) for t in ev if corpus.has(t)})
            if n_sources == 1 and ins.get("confidence", "").lower() in ("medium", "high"):
                failures.append({
                    "insight_id": iid, "rule": "single_source_generalisation", "severity": "fail",
                    "detail": f"only one source ({ev[0].split(':')[0] if ev else '?'}) but confidence is "
                              f"{ins.get('confidence')}; must be low and the claim must name the participant's context",
                    "turns": ev[:2],
                })
    return failures


def critique(corpus: Corpus, cfg: dict, logger, question: str, insights: list[dict]) -> dict:
    rules = cfg["critic"]["rules"]
    det = deterministic_checks(corpus, insights, rules)
    if logger:
        logger.note(f"deterministic checks: {len(det)} failure(s)")

    model_rules = [r for r in rules if r.get("check") == "model"]
    rules_text = "\n".join(f"- {r['id']} [{r['severity']}]: {r['description'].strip()}" for r in model_rules)
    cited_ids = []
    for ins in insights:
        cited_ids += (ins.get("evidence") or []) + (ins.get("counter_evidence") or [])
    cited = corpus.render_turns(sorted(set(cited_ids)))

    verdict = None
    for attempt in (1, 2):
        r = llm.call(
            model=cfg["models"]["critic"],
            system=prompts.CRITIC_SYSTEM.format(rules=rules_text),
            user=prompts.CRITIC_USER.format(
                question=question, insights=_j(insights), cited=cited, transcripts=corpus.render_all(),
            ),
            max_tokens=cfg["critic"].get("max_tokens", 32000),
            logger=logger,
            label=f"critic_attempt{attempt}" if attempt > 1 else "critic",
        )
        if isinstance(r["data"], dict) and "failures" in r["data"]:
            verdict = r["data"]
            break
        if logger:
            logger.note(f"critic attempt {attempt} returned no verdict "
                        f"(stop={r['stop_reason']}, blocks={r.get('block_types')}, err={r.get('json_error')})")

    if verdict is None:
        # A critic that says nothing must never count as approval.
        verdict = {
            "pass": False,
            "failures": [{"insight_id": "*", "rule": "critic_error", "severity": "fail",
                          "detail": "critic produced no parseable verdict after 2 attempts", "turns": []}],
            "notes": "critic error",
        }
    failures = det + list(verdict.get("failures", []))
    verdict["failures"] = failures
    verdict["pass"] = not any(f.get("severity", "fail") == "fail" for f in failures)
    return verdict
