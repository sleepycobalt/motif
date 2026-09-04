"""
The Motif engine service. Every surface — the CLI, the MCP server, the FigJam
plugin's service — calls these functions and nothing else. Nothing in here
prints, parses argv, or knows where it is running; progress goes through
`emit`, results come back as values, failures are exceptions or explicit
stop reasons. Silence is never approval: an empty synthesis, a missing verdict,
or an unparseable document is reported as a failure, never as an empty success.

    ingest(source, out_dir)                       transcripts -> processed corpus dir
    synthesize(processed_dir, ...)                ingest'd corpus -> RunResult (loop, logged under runs/)
    critique(insights, processed_dir, ...)        insights JSON -> verdict, logged as its own run
    critique_document(markdown, processed_dir)    prose/markdown synthesis -> structured -> verdict
    receipts(turn_ids, processed_dir)             verbatim turn text for citation checking
    corpus_for_run(run_id)                        the corpus snapshot a run cited
    load_run(run_id)                              a run's meta, notes, iterations, verdicts
"""

from __future__ import annotations

import copy
import json
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from core import llm
from core.config import load_config
from core.logger import RunLogger
from core.loop import run_loop
from synth import agents, prompts
from synth.corpus import Corpus
from synth.ingest import ingest as _ingest
from synth.report import to_markdown

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = Path(__file__).resolve().parent / "synth.yaml"  # ships in the wheel; config/synth.yaml symlinks to it
DEFAULT_QUESTION = (
    "What do these researchers tell us about the practical and epistemic barriers to making "
    "qualitative research data open, what tensions do they experience, and what would help?"
)
CONDITIONS = {
    "A": "single-prompt synthesis (baseline)",
    "B": "intake -> synthesis, critic disabled",
    "C": "intake -> synthesis -> critic -> revise (full loop)",
}

Emit = Callable[[str], None] | None


def load_cfg(config_path: str | Path | None = None, *, critic_model: str | None = None,
             max_iterations: int | None = None) -> dict:
    cfg = load_config(config_path or DEFAULT_CONFIG)
    if critic_model:
        cfg["models"]["critic"] = critic_model
    if max_iterations is not None:
        cfg["loop"]["max_iterations"] = max_iterations
    return cfg


# ------------------------------------------------------------------ ingest

def ingest(source, out_dir: str | Path | None = None, emit: Emit = None) -> Path:
    """Transcripts (folder or list of files) -> processed corpus dir. Returns the dir."""
    out = Path(out_dir) if out_dir else Path(tempfile.mkdtemp(prefix="motif-"))
    _ingest(source, out, emit=emit)
    return out


# -------------------------------------------------------------- synthesize

@dataclass
class RunResult:
    run_id: str
    run_dir: Path
    insights: list
    markdown: str
    iterations: int
    stop_reason: str
    meta: dict
    verdicts: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return bool(self.insights) and self.stop_reason != "synthesis_failed"


def synthesize(processed_dir: str | Path, *, question: str | None = None, condition: str = "C",
               max_iterations: int | None = None, names: list[str] | None = None,
               config_path: str | Path | None = None, cfg: dict | None = None,
               critic_model: str | None = None, tag: str = "", runs_root: str | Path = "runs",
               emit: Emit = None, redact: bool = False) -> RunResult:
    if condition not in CONDITIONS:
        raise ValueError(f"condition must be one of {sorted(CONDITIONS)}; got {condition!r}")
    cfg = copy.deepcopy(cfg) if cfg else load_cfg(config_path, critic_model=critic_model,
                                                   max_iterations=max_iterations)
    if cfg and critic_model:
        cfg["models"]["critic"] = critic_model
    if cfg and max_iterations is not None:
        cfg["loop"]["max_iterations"] = max_iterations
    q = question or DEFAULT_QUESTION

    corpus = Corpus(processed_dir, names)
    logger = RunLogger(root=runs_root, condition=condition, tag=tag,
                       config={**cfg, "transcripts": corpus.names, "question": q},
                       emit=emit, redact=redact)
    logger.snapshot_corpus(processed_dir, corpus.names)
    logger.emit(f"run {logger.run_id}: condition {condition}, {len(corpus.names)} transcripts, "
                f"{corpus.words:,} words")

    def synth_with_retry(**kw):
        for attempt in (1, 2):
            ins = agents.synthesise(corpus, cfg, logger, q, **kw)
            if ins:
                return ins
            logger.note(f"synthesis attempt {attempt} empty; {'retrying' if attempt == 1 else 'giving up'}")
        return []

    if condition == "A":
        insights = synth_with_retry(single_prompt=True)
        state, iterations = {"insights": insights}, 0
        stop = "single_prompt" if insights else "synthesis_failed"
    else:
        def produce(state):
            state["intake"] = agents.intake(corpus, cfg, logger)
            state["insights"] = synth_with_retry(intake_notes=state["intake"])
            return state

        def check(state):
            return agents.critique(corpus, cfg, logger, q, state["insights"],
                                   intake_notes=state.get("intake"),
                                   previous=state.get("previous_insights"),
                                   dropped=state.get("dropped"))

        def revise(state, verdict):
            state["previous_insights"] = state["insights"]
            state["insights"], state["dropped"] = agents.revise(
                corpus, cfg, logger, q, state["insights"], verdict)
            return state

        res = run_loop(state={}, produce=produce, check=check, revise=revise,
                       max_iterations=cfg["loop"]["max_iterations"], logger=logger,
                       critic_enabled=(condition == "C"))
        state, iterations, stop = res.state, res.iterations, res.stop_reason
        state["verdicts"] = res.verdicts
        if not state.get("insights"):
            stop = "synthesis_failed"

    insights = state.get("insights", [])
    # Attach the critic's unresolved objections to the affected insights so the
    # reader sees where the reviewer still disagreed. Silence is not agreement.
    verdicts = state.get("verdicts") or []
    if verdicts and not verdicts[-1].get("pass"):
        by_id: dict = {}
        for f in verdicts[-1].get("failures", []):
            by_id.setdefault(f.get("insight_id"), []).append(f"{f.get('rule')}: {f.get('detail')}")
        for ins in insights:
            if ins.get("id") in by_id:
                ins["critic_flags"] = by_id[ins["id"]]
    logger.meta.update({"iterations": iterations, "stop_reason": stop})
    md = to_markdown(insights, corpus, logger.meta)
    run_dir = logger.finish(state, md, stop_reason=stop, iterations=iterations)
    logger.emit(f"{len(insights)} insights -> {run_dir}/output.md")
    return RunResult(run_id=logger.run_id, run_dir=run_dir, insights=insights, markdown=md,
                     iterations=iterations, stop_reason=stop, meta=logger.meta, verdicts=verdicts)


# ---------------------------------------------------------------- critique

def _validate_insights(insights) -> list[dict]:
    if not isinstance(insights, list) or not insights:
        raise ValueError("insights must be a non-empty list of insight objects")
    bad = [i for i, x in enumerate(insights) if not isinstance(x, dict) or not x.get("claim")]
    if bad:
        raise ValueError(f"insight(s) at index {bad} are not objects with a 'claim'")
    return [dict(x) for x in insights]


def _critique(insights: list[dict], corpus: Corpus, cfg: dict, logger: RunLogger, question: str,
              intake_notes: dict | None, source_format: str, question_assumed: bool) -> dict:
    cfg = copy.deepcopy(cfg)
    skipped = []
    if not intake_notes:
        # missing_theme compares the page against the intake topic maps; without
        # maps it cannot be judged. Leave it out and say so, rather than let the
        # model guess.
        rules = cfg["critic"]["rules"]
        if any(r["id"] == "missing_theme" for r in rules):
            cfg["critic"]["rules"] = [r for r in rules if r["id"] != "missing_theme"]
            skipped.append("missing_theme")
    insights = agents.normalise(corpus, insights)
    verdict = agents.critique(corpus, cfg, logger, question, insights, intake_notes=intake_notes)
    verdict["skipped_rules"] = skipped
    verdict["question_assumed"] = question_assumed
    if skipped:
        verdict["notes"] = (verdict.get("notes") or "") + " [not checked: " + ", ".join(skipped) + \
                           " — no intake notes supplied]"
    summary = summarise_verdict(verdict)
    stop = "critique_pass" if verdict.get("pass") else "critique_fail"
    logger.finish({"insights": insights, "verdict": verdict, "source_format": source_format},
                  stop_reason=stop, iterations=1)
    return {"run_id": logger.run_id, "run_dir": str(logger.dir), "source_format": source_format,
            "insights": insights, "verdict": verdict, "summary": summary}


def summarise_verdict(verdict: dict) -> dict:
    by_rule: dict = {}
    by_insight: dict = {}
    for f in verdict.get("failures", []):
        by_rule.setdefault(f.get("rule"), []).append(f.get("insight_id"))
        by_insight.setdefault(f.get("insight_id"), []).append(f.get("rule"))
    return {"pass": bool(verdict.get("pass")),
            "n_fail": sum(1 for f in verdict.get("failures", []) if f.get("severity", "fail") == "fail"),
            "n_warn": sum(1 for f in verdict.get("failures", []) if f.get("severity") == "warn"),
            "by_rule": by_rule, "by_insight": by_insight}


def critique(insights: list, processed_dir: str | Path, *, question: str | None = None,
             intake_notes: dict | None = None, names: list[str] | None = None,
             config_path: str | Path | None = None, cfg: dict | None = None, tag: str = "",
             runs_root: str | Path = "runs", emit: Emit = None, redact: bool = False) -> dict:
    """Run the critic alone over insights JSON. Logged as its own run (condition 'critique')."""
    insights = _validate_insights(insights)
    cfg = cfg or load_cfg(config_path)
    q = question or DEFAULT_QUESTION
    corpus = Corpus(processed_dir, names)
    logger = RunLogger(root=runs_root, condition="critique", tag=tag,
                       config={**cfg, "transcripts": corpus.names, "question": q}, emit=emit, redact=redact)
    logger.snapshot_corpus(processed_dir, corpus.names)
    logger.note(f"critique of {len(insights)} insight(s) from JSON against {len(corpus.names)} transcripts")
    return _critique(insights, corpus, cfg, logger, q, intake_notes, "json", question is None)


MOTIF_HEADING = re.compile(r"^## (?P<id>\S+) — (?P<title>.*?)\s*$", re.M)
TURN_ID = re.compile(r"\b[a-z0-9][a-z0-9-]*:\d{4}\b")
RECEIPT = re.compile(r'^\s*receipt (\S+:\d{4}): "(.*)"\s*$', re.M)


def _field(body: str, name: str) -> str:
    m = re.search(r"^\*\*" + re.escape(name) + r":\*\*\s*(.*?)\s*$", body, re.M)
    return m.group(1).strip() if m else ""


def parse_motif_markdown(document: str) -> list[dict]:
    """Deterministic parser for Motif's own report format (synth/report.py).
    Returns [] if the document is not in that format."""
    parts = MOTIF_HEADING.split(document)
    if len(parts) < 4:
        return []
    insights = []
    for i in range(1, len(parts), 3):
        iid, title, body = parts[i], parts[i + 1], parts[i + 2]
        claim = _field(body, "Claim")
        if not claim:
            continue
        receipts = dict(RECEIPT.findall(body))
        ev_ids = TURN_ID.findall(_field(body, "Evidence"))
        ce_raw = _field(body, "Counter-evidence")
        ce_ids, ce_note = [], ""
        if ce_raw and not ce_raw.lower().startswith("none"):
            head, _, ce_note = ce_raw.partition(" — ")
            ce_ids = TURN_ID.findall(head)
        elif ce_raw.lower().startswith("none"):
            _, _, ce_note = ce_raw.partition(" — ")
        insights.append({
            "id": iid, "title": title.strip(), "claim": claim,
            "evidence": [{"turn": t, "quote": receipts.get(t, "")} for t in ev_ids],
            "confidence": _field(body, "Confidence").lower(),
            "counter_evidence": [{"turn": t, "quote": receipts.get(t, "")} for t in ce_ids],
            "counter_note": ce_note.strip(),
            "opportunity": _field(body, "Opportunity"),
        })
    return insights


def structure_document(document: str, corpus_names: list[str], *, cfg: dict, logger: RunLogger,
                       question: str | None = None, force_model: bool = False) -> tuple[list[dict], str]:
    """Prose/markdown synthesis -> insights in the shared schema. Motif's own format is
    parsed in code; anything else is structured by the model, which may only copy."""
    if not document or not document.strip():
        raise ValueError("document is empty")
    if not force_model:
        parsed = parse_motif_markdown(document)
        if parsed:
            logger.note(f"structured {len(parsed)} insight(s) from Motif-format markdown (deterministic)")
            return parsed, "motif_markdown"
    r = llm.call(
        model=cfg["models"]["synthesis"],
        system=prompts.STRUCTURE_SYSTEM,
        user=prompts.STRUCTURE_USER.format(question=question or DEFAULT_QUESTION,
                                           names=", ".join(corpus_names), document=document),
        max_tokens=cfg["synthesis"].get("max_tokens", 64000),
        logger=logger, label="structure",
    )
    ins = (r["data"] or {}).get("insights") or []
    if not ins:
        raise ValueError(f"could not structure the document into insights "
                         f"(stop={r['stop_reason']}, err={r.get('json_error')})")
    logger.note(f"structured {len(ins)} insight(s) from free-form document (model)")
    return ins, "model"


def critique_document(document: str, processed_dir: str | Path, *, question: str | None = None,
                      names: list[str] | None = None, config_path: str | Path | None = None,
                      cfg: dict | None = None, tag: str = "", runs_root: str | Path = "runs",
                      emit: Emit = None, redact: bool = False, force_model: bool = False) -> dict:
    """Critique a synthesis given as markdown or prose: structure it, then run the critic."""
    cfg = cfg or load_cfg(config_path)
    q = question or DEFAULT_QUESTION
    corpus = Corpus(processed_dir, names)
    logger = RunLogger(root=runs_root, condition="critique", tag=tag or "doc",
                       config={**cfg, "transcripts": corpus.names, "question": q}, emit=emit, redact=redact)
    logger.snapshot_corpus(processed_dir, corpus.names)
    (logger.dir / "input.md").write_text(document, encoding="utf-8")
    insights, fmt = structure_document(document, corpus.names, cfg=cfg, logger=logger,
                                       question=question, force_model=force_model)
    insights = _validate_insights(insights)
    logger.record_iteration(0, {"stage": "structure", "source_format": fmt, "insights": insights})
    return _critique(insights, corpus, cfg, logger, q, None, fmt, question is None)


# ---------------------------------------------------------------- receipts

def receipts(turn_ids: list[str], processed_dir: str | Path, names: list[str] | None = None) -> dict:
    if not turn_ids:
        raise ValueError("no turn ids given")
    corpus = Corpus(processed_dir, names)
    out, missing = [], []
    for t in turn_ids:
        if corpus.has(t):
            turn = corpus.turns[t]
            out.append({"turn": t, "found": True, "transcript": corpus.transcript_of(t),
                        "speaker": turn["speaker"], "interviewer": corpus.is_researcher(t),
                        "words": turn.get("words"), "text": turn["text"]})
        else:
            out.append({"turn": t, "found": False})
            missing.append(t)
    if len(missing) == len(turn_ids):
        raise LookupError(f"none of the {len(turn_ids)} turn id(s) exist in this corpus "
                          f"(transcripts: {', '.join(corpus.names)})")
    return {"receipts": out, "missing": missing, "transcripts": corpus.names}


# -------------------------------------------------------------------- runs

def corpus_for_run(run_id: str, runs_root: str | Path = "runs") -> tuple[Path, list[str] | None]:
    """The processed corpus a run cited: its snapshot if present, else the recorded source."""
    run_dir = Path(runs_root) / run_id
    if not run_dir.is_dir():
        raise LookupError(f"no such run: {run_id}")
    snap = run_dir / "corpus"
    if (snap / "manifest.json").exists():
        return snap, None
    meta = json.load(open(run_dir / "meta.json", encoding="utf-8"))
    src = meta.get("corpus", {}).get("source")
    names = meta.get("corpus", {}).get("transcripts") or meta.get("config", {}).get("transcripts")
    if src and Path(src, "manifest.json").exists():
        return Path(src), names
    # Runs made before corpus snapshots: fall back to the default processed corpus
    # if it holds every transcript the run named.
    import os
    fallback = Path(os.environ.get("MOTIF_PROCESSED", "data/processed"))
    if names and (fallback / "manifest.json").exists():
        have = {m["name"] for m in json.load(open(fallback / "manifest.json", encoding="utf-8"))}
        if set(names) <= have:
            return fallback, names
    raise LookupError(f"run {run_id} has no corpus snapshot and its source corpus is not available")


def load_run(run_id: str, runs_root: str | Path = "runs",
             include: tuple[str, ...] = ("meta", "notes", "iterations", "verdicts")) -> dict:
    run_dir = Path(runs_root) / run_id
    if not run_dir.is_dir():
        raise LookupError(f"no such run: {run_id}")
    out = {"run_id": run_id, "run_dir": str(run_dir)}
    meta = json.load(open(run_dir / "meta.json", encoding="utf-8"))
    out["meta"] = meta
    if "notes" in include and (run_dir / "notes.txt").exists():
        out["notes"] = (run_dir / "notes.txt").read_text(encoding="utf-8").splitlines()
    if "iterations" in include:
        its = []
        for f in sorted((run_dir / "iterations").glob("*.json")):
            st = json.load(open(f, encoding="utf-8"))
            entry = {"file": f.name, "stage": st.get("stage"),
                     "n_insights": len(st.get("state", st).get("insights", []) or [])}
            if st.get("stage") == "check":
                v = st.get("verdict", {})
                entry["pass"] = v.get("pass")
                entry["failures"] = [{k: f_.get(k) for k in ("insight_id", "rule", "severity", "detail")}
                                     for f_ in v.get("failures", [])]
            its.append(entry)
        out["iterations"] = its
    output = None
    if (run_dir / "output.json").exists():
        output = json.load(open(run_dir / "output.json", encoding="utf-8"))
    if "verdicts" in include and output is not None:
        out["verdicts"] = output.get("verdicts") or ([output["verdict"]] if "verdict" in output else [])
    if "insights" in include and output is not None:
        out["insights"] = output.get("insights", [])
    if "report" in include and (run_dir / "output.md").exists():
        out["report_markdown"] = (run_dir / "output.md").read_text(encoding="utf-8")
    if "calls" in include:
        calls = []
        for f in sorted((run_dir / "calls").glob("*.json")):
            c = json.load(open(f, encoding="utf-8"))
            calls.append({k: c.get(k) for k in ("label", "model", "in_tok", "out_tok", "seconds",
                                                "cost", "stop_reason", "json_error")})
        out["calls"] = calls
    return out


# ------------------------------------------------------------------- board

def board(run_id: str, runs_root: str | Path = "runs", columns: int = 2,
          origin: tuple[float, float] = (0, 0)) -> dict:
    """A run's insights as a FigJam layout plus one use_figma script per section."""
    from synth import board as _board
    run = load_run(run_id, runs_root, include=("meta", "insights"))
    insights = run.get("insights") or []
    if not insights:
        raise LookupError(f"run {run_id} has no insights to put on a board")
    lay = _board.layout(insights, run["meta"], columns=columns, origin=origin)
    return {"run_id": run_id, "board": lay, "scripts": _board.scripts(lay),
            "instructions": _board.HOST_INSTRUCTIONS}
