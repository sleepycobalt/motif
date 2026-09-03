"""The three agent roles plus deterministic checks, wired to core.llm."""

import json
import re

from core import llm
from synth import prompts
from synth.corpus import Corpus


def _j(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


def turn_ids(items) -> list[str]:
    """Evidence items may be plain IDs or {turn, quote} objects."""
    out = []
    for x in items or []:
        if isinstance(x, dict):
            if x.get("turn"):
                out.append(x["turn"])
        elif isinstance(x, str):
            out.append(x)
    return out


def normalise(corpus: Corpus, insights: list[dict]) -> list[dict]:
    """Derive fields the model should not be asked for. `sources` = transcripts
    cited as evidence (counter-evidence participants are not sources)."""
    for ins in insights:
        ins["sources"] = sorted({corpus.transcript_of(t) for t in turn_ids(ins.get("evidence")) if corpus.has(t)})
    return insights


def _norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[\u2018\u2019\u201c\u201d]", "'", s)
    s = re.sub(r"[^a-z0-9' ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def quote_matches(quote: str, text: str) -> bool:
    q, t = _norm(quote), _norm(text)
    return len(q.split()) >= 5 and q in t


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
        max_tokens=cfg["synthesis"].get("max_tokens", 64000),
        logger=logger,
        label="synthesis_single" if single_prompt else "synthesis",
    )
    insights = (r["data"] or {}).get("insights") or []
    if not insights and logger:
        logger.note(f"synthesis returned no insights (stop={r['stop_reason']}, err={r.get('json_error')})")
    return normalise(corpus, insights)


def revise(corpus: Corpus, cfg: dict, logger, question: str,
           insights: list[dict], verdict: dict) -> tuple[list[dict], list[dict]]:
    r = llm.call(
        model=cfg["models"]["synthesis"],
        system=prompts.SYNTHESIS_SYSTEM,
        user=prompts.REVISE_USER.format(
            question=question, insights=_j(insights),
            failures=_j(verdict.get("failures", [])),
            notes=verdict.get("notes", ""), transcripts=corpus.render_all(),
        ),
        max_tokens=cfg["synthesis"].get("max_tokens", 64000),
        logger=logger,
        label="revise",
    )
    data = r["data"] or {}
    new = data.get("insights")
    dropped = data.get("dropped") or []
    if not new and logger:
        logger.note(f"revise returned no insights (stop={r['stop_reason']}); keeping previous set")
    if dropped and logger:
        logger.note("dropped: " + "; ".join(f"{d.get('id')} ({d.get('reason', '')[:60]})" for d in dropped))
    return normalise(corpus, new if new else insights), dropped


# ---------------------------------------------------------------- critic

def deterministic_checks(corpus: Corpus, insights: list[dict], rules: list[dict]) -> list[dict]:
    """Rules that need no model: bad citations and single-source generalisation."""
    by_id = {r["id"]: r for r in rules}
    failures = []
    for ins in insights:
        iid = ins.get("id", "?")
        ev = turn_ids(ins.get("evidence"))
        ce = turn_ids(ins.get("counter_evidence"))
        srcs = ins.get("sources", []) or []

        if "quote_mismatch" in by_id:
            bad_q = []
            for item in (ins.get("evidence") or []) + (ins.get("counter_evidence") or []):
                if not isinstance(item, dict):
                    bad_q.append(f"{item} (no quote given)")
                    continue
                t = corpus.turns.get(item.get("turn", ""))
                if t and not quote_matches(item.get("quote", ""), t["text"]):
                    bad_q.append(f"{item['turn']}: \"{item.get('quote', '')[:60]}\"")
            if bad_q:
                failures.append({
                    "insight_id": iid, "rule": "quote_mismatch", "severity": "fail",
                    "detail": "receipt does not match transcript (quote not found verbatim in the cited turn, "
                              "or missing): " + "; ".join(bad_q),
                    "turns": [b.split(":")[0] + ":" + b.split(":")[1][:4] for b in bad_q if ":" in b][:4],
                })

        if "bad_citation" in by_id:
            bad = [t for t in ev + ce if not corpus.has(t)]
            if bad or not ev:
                failures.append({
                    "insight_id": iid, "rule": "bad_citation", "severity": "fail",
                    "detail": f"nonexistent turns={bad}; evidence_count={len(ev)}",
                    "turns": bad,
                })

        if "interviewer_cited" in by_id:
            bad_ev = [t for t in ev if corpus.has(t) and corpus.is_researcher(t)]
            if bad_ev:
                failures.append({
                    "insight_id": iid, "rule": "interviewer_cited", "severity": "fail",
                    "detail": f"evidence cites the interviewer, not a participant: {bad_ev}; "
                              f"replace with the participant's own turns",
                    "turns": bad_ev,
                })

        if "confidence_threshold" in by_id:
            thr = by_id["confidence_threshold"]
            n_sources = len({corpus.transcript_of(t) for t in ev if corpus.has(t)})
            conf = (ins.get("confidence") or "").lower()
            has_counter = bool(ce)
            need = {"high": thr.get("high_min_sources", 4), "medium": thr.get("medium_min_sources", 2)}
            problem = None
            if conf == "high" and (n_sources < need["high"] or (has_counter and thr.get("high_forbids_counter", True))):
                problem = (f"'high' requires >= {need['high']} sources"
                           + (" and no counter-evidence" if thr.get("high_forbids_counter", True) else "")
                           + f"; has {n_sources} source(s), counter-evidence={'yes' if has_counter else 'no'}")
            elif conf == "medium" and n_sources < need["medium"]:
                problem = f"'medium' requires >= {need['medium']} sources; has {n_sources}"
            elif conf not in ("high", "medium", "low"):
                problem = f"confidence must be high/medium/low, got {conf!r}"
            if problem:
                failures.append({
                    "insight_id": iid, "rule": "confidence_threshold", "severity": "fail",
                    "detail": problem + " — lower the confidence or add sources",
                    "turns": ev[:2],
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


def _profiles(intake_notes: dict | None) -> str:
    if not intake_notes:
        return "(none)"
    return "\n".join(f"- {n}: {v.get('profile_summary', '')}" for n, v in intake_notes.items())


def _topic_maps(intake_notes: dict | None) -> str:
    if not intake_notes:
        return "(none)"
    out = []
    for n, v in intake_notes.items():
        for t in v.get("topics", []) or []:
            turns = ", ".join((t.get("turns") or [])[:3])
            out.append(f"- [{n}] {t.get('topic', '')}: {t.get('note', '')} ({turns})")
    return "\n".join(out)


def critique(corpus: Corpus, cfg: dict, logger, question: str, insights: list[dict],
             intake_notes: dict | None = None, previous: list[dict] | None = None,
             dropped: list[dict] | None = None) -> dict:
    rules = cfg["critic"]["rules"]
    if not insights:
        # Nothing to check is not the same as nothing wrong.
        return {"pass": False, "notes": "no insights to review",
                "failures": [{"insight_id": "*", "rule": "empty_synthesis", "severity": "fail",
                              "detail": "synthesis produced no insights", "turns": []}]}
    det = deterministic_checks(corpus, insights, rules)
    if previous is not None and any(r["id"] == "silent_deletion" for r in rules):
        before = {i.get("id") for i in previous}
        after = {i.get("id") for i in insights}
        justified = {d.get("id") for d in (dropped or [])}
        for missing in sorted(before - after - justified):
            det.append({"insight_id": missing, "rule": "silent_deletion", "severity": "fail",
                        "detail": f"{missing} was removed in revision without a listed reason; "
                                  f"restore it (fixed or downgraded to low) or justify dropping it",
                        "turns": []})
    if logger:
        logger.note(f"deterministic checks: {len(det)} failure(s)")

    model_rules = [r for r in rules if r.get("check") == "model"]
    rules_text = "\n".join(f"- {r['id']} [{r['severity']}]: {r['description'].strip()}" for r in model_rules)
    cited_ids = []
    for ins in insights:
        cited_ids += turn_ids(ins.get("evidence")) + turn_ids(ins.get("counter_evidence"))
    cited = corpus.render_turns(sorted(set(cited_ids)))

    verdict = None
    for attempt in (1, 2):
        r = llm.call(
            model=cfg["models"]["critic"],
            system=prompts.CRITIC_SYSTEM.format(rules=rules_text),
            user=prompts.CRITIC_USER.format(
                question=question, insights=_j(insights), cited=cited, transcripts=corpus.render_all(),
                coverage_block=prompts.COVERAGE_BLOCK.format(
                    notes=_topic_maps(intake_notes), profiles=_profiles(intake_notes)) if intake_notes else "",
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
