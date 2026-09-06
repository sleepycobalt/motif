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
            user=(prompts.INTAKE_USER_DISSENT if cfg.get("features", {}).get("dissent_at_intake")
                  else prompts.INTAKE_USER).format(name=name, profile=profile, transcript=corpus.text[name]),
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
            for kind, items in (("evidence", ins.get("evidence") or []), ("counter", ins.get("counter_evidence") or [])):
                for item in items:
                    if not isinstance(item, dict):
                        bad_q.append(f"{item} (no quote given)")
                        continue
                    quote = item.get("quote", "") or ""
                    if kind == "counter" and not quote.strip():
                        # No receipt in the source is not a mismatched receipt: reports written before
                        # 2026-09-05 carried no counter quotes, and a structured document may not either.
                        continue
                    t = corpus.turns.get(item.get("turn", ""))
                    if t and not quote_matches(quote, t["text"]):
                        bad_q.append(f"{item['turn']}: \"{quote[:60]}\"")
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

        if "duplicate_receipt" in by_id:
            # v3 item (c). The same turn cited twice as two receipts inflates the evidence line
            # without adding evidence (I-06/david:0026, 2026-09-05; R1's I-04 and I-11 in Eval 2).
            # Warn, not fail: the claim is still supported, so a fail would send the reviser to
            # rewrite a sound insight.
            dupes = []
            for field, ids in (("evidence", ev), ("counter_evidence", ce)):
                seen, rep = set(), []
                for t in ids:
                    if t in seen and t not in rep:
                        rep.append(t)
                    seen.add(t)
                dupes += [f"{field}: {t}" for t in rep]
            if dupes:
                failures.append({
                    "insight_id": iid, "rule": "duplicate_receipt",
                    "severity": by_id["duplicate_receipt"].get("severity", "warn"),
                    "detail": "the same turn is cited more than once in one field (" + "; ".join(dupes)
                              + "); keep one receipt per turn, or cite a different turn that adds evidence",
                    "turns": [d.split(": ", 1)[1] for d in dupes][:4],
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

    if "duplicate_insight" in by_id:
        failures += _duplicate_insights(insights, by_id["duplicate_insight"])
    return failures


_STOP = {"the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for", "with", "as", "is",
         "are", "was", "were", "be", "been", "that", "this", "it", "its", "their", "they", "them",
         "from", "by", "at", "not", "no", "than", "then", "so", "if", "when", "what", "which", "who",
         "can", "do", "does", "did", "have", "has", "had", "would", "could", "should", "more", "most",
         "some", "any", "all", "own", "other", "others", "one", "two", "about", "into", "over"}


def _bag(ins: dict) -> set:
    words = _norm(f"{ins.get('title', '')} {ins.get('claim', '')}").split()
    return {w for w in words if w not in _STOP and len(w) > 2}


def _duplicate_insights(insights: list[dict], rule: dict) -> list[dict]:
    """v3 `dedupe`. Flag insight pairs whose title+claim vocabulary overlaps above a threshold, so the
    reviser merges or differentiates them. Jaccard over content words: symmetric, needs no model call,
    and catches the R4 pattern (I-03/I-06, I-15/I-16) where missing_theme pressure over-split a finding."""
    thr = float(rule.get("similarity_threshold", 0.55))
    bags = [(ins, _bag(ins)) for ins in insights]
    out = []
    for i, (a, ba) in enumerate(bags):
        for b, bb in bags[i + 1:]:
            union = ba | bb
            if not union:
                continue
            sim = len(ba & bb) / len(union)
            if sim >= thr:
                out.append({
                    "insight_id": a.get("id", "?"), "rule": "duplicate_insight",
                    "severity": rule.get("severity", "warn"),
                    "detail": f"{a.get('id', '?')} and {b.get('id', '?')} overlap {sim:.0%} on their "
                              f"title and claim vocabulary ({a.get('title', '')!r} vs {b.get('title', '')!r}); "
                              f"merge them into one insight, or sharpen each so they state different findings",
                    "turns": [],
                })
    return out


def check_critic_turns(corpus: Corpus, failures: list[dict], rule: dict) -> tuple[list[dict], list[dict]]:
    """v3 item (a). The critic's own `turns` lists never passed through the interviewer check, so a
    model-judged failure could send the reviser to an interviewer turn (sam:0068 in
    runs/20260904-165114-critique-doc). Run them through the same existence-and-interviewer check the
    synthesis's citations get: a bad turn is removed from the failure, and one warn records the strip
    so the critic's error is reported rather than hidden. Returns (cleaned failures, warnings)."""
    cleaned, stripped = [], []
    for f in failures:
        turns = f.get("turns") or []
        keep, bad = [], []
        for t in turns:
            if not isinstance(t, str):
                bad.append(f"{t!r} (not a turn id)")
            elif not corpus.has(t):
                bad.append(f"{t} (no such turn)")
            elif corpus.is_researcher(t):
                bad.append(f"{t} (interviewer)")
            else:
                keep.append(t)
        if bad:
            stripped.append(f"{f.get('rule', '?')} on {f.get('insight_id', '?')}: " + ", ".join(bad))
            f = {**f, "turns": keep}
        cleaned.append(f)
    warnings = []
    if stripped:
        warnings.append({
            "insight_id": "*", "rule": "critic_citation", "severity": rule.get("severity", "warn"),
            "detail": "the critic cited turns that are not usable evidence; they were removed from the "
                      "objections above before revision: " + "; ".join(stripped),
            "turns": [],
        })
    return cleaned, warnings


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


def _coverage_block(cfg: dict, intake_notes: dict | None) -> str:
    if not intake_notes:
        return ""
    notes, profiles = _topic_maps(intake_notes), _profiles(intake_notes)
    if cfg.get("features", {}).get("dissent_at_intake"):
        return prompts.COVERAGE_BLOCK_DISSENT.format(notes=notes, profiles=profiles,
                                                     dissent=_dissent(intake_notes))
    return prompts.COVERAGE_BLOCK.format(notes=notes, profiles=profiles)


def _dissent(intake_notes: dict | None) -> str:
    """v3 `dissent_at_intake`: the per-participant minority positions, as the critic's shortlist."""
    if not intake_notes:
        return "(none)"
    out = []
    for n, v in intake_notes.items():
        for d in v.get("dissent_or_unusual", []) or []:
            against = f" — against the majority view that {d['against']}" if d.get("against") else ""
            out.append(f"- [{n}] {d.get('point', '')} ({d.get('turn', '')}){against}")
    return "\n".join(out) or "(none reported)"


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
                coverage_block=_coverage_block(cfg, intake_notes),
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
    model_failures = list(verdict.get("failures", []))
    if "critic_citation" in {r["id"] for r in rules}:
        rule = next(r for r in rules if r["id"] == "critic_citation")
        model_failures, critic_warnings = check_critic_turns(corpus, model_failures, rule)
        if critic_warnings and logger:
            logger.note(critic_warnings[0]["detail"])
        model_failures += critic_warnings
    failures = det + model_failures
    verdict["failures"] = failures
    verdict["pass"] = not any(f.get("severity", "fail") == "fail" for f in failures)
    return verdict
