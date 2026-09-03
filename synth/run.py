"""
Run the synthesis loop.

    python -m synth.run --condition C --transcripts michelle,david,bruce,stephen,penni
    python -m synth.run --condition A            # single prompt, all transcripts
    python -m synth.run --condition B            # intake + synthesis, no critic
    python -m synth.run --condition C --critic-model claude-opus-5 --tag opus-critic

Conditions:
    A  single-prompt synthesis (baseline)
    B  intake -> synthesis, critic disabled
    C  intake -> synthesis -> critic -> revise (full loop)
"""

import argparse

from core.config import load_config
from core.logger import RunLogger
from core.loop import run_loop
from synth import agents
from synth.corpus import Corpus
from synth.report import to_markdown

DEFAULT_QUESTION = (
    "What do these researchers tell us about the practical and epistemic barriers to making "
    "qualitative research data open, what tensions do they experience, and what would help?"
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", choices=["A", "B", "C"], default="C")
    ap.add_argument("--config", default="config/synth.yaml")
    ap.add_argument("--processed", default="data/processed")
    ap.add_argument("--transcripts", default="", help="comma-separated names; default all")
    ap.add_argument("--question", default=DEFAULT_QUESTION)
    ap.add_argument("--critic-model", default=None)
    ap.add_argument("--max-iterations", type=int, default=None)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.critic_model:
        cfg["models"]["critic"] = args.critic_model
    if args.max_iterations is not None:
        cfg["loop"]["max_iterations"] = args.max_iterations

    names = [n.strip() for n in args.transcripts.split(",") if n.strip()] or None
    corpus = Corpus(args.processed, names)
    logger = RunLogger(condition=args.condition, tag=args.tag,
                       config={**cfg, "transcripts": corpus.names, "question": args.question})
    print(f"run {logger.run_id}: condition {args.condition}, {len(corpus.names)} transcripts, "
          f"{corpus.words:,} words")

    q = args.question

    def synth_with_retry(**kw):
        for attempt in (1, 2):
            ins = agents.synthesise(corpus, cfg, logger, q, **kw)
            if ins:
                return ins
            logger.note(f"synthesis attempt {attempt} empty; {'retrying' if attempt == 1 else 'giving up'}")
        return []

    if args.condition == "A":
        insights = synth_with_retry(single_prompt=True)
        result_state, iterations, stop = {"insights": insights}, 0, ("single_prompt" if insights else "synthesis_failed")
    else:
        def produce(state):
            state["intake"] = agents.intake(corpus, cfg, logger)
            state["insights"] = synth_with_retry(intake_notes=state["intake"])
            return state

        def check(state):
            return agents.critique(corpus, cfg, logger, q, state["insights"])

        def revise(state, verdict):
            state["insights"] = agents.revise(corpus, cfg, logger, q, state["insights"], verdict)
            return state

        res = run_loop(
            state={}, produce=produce, check=check, revise=revise,
            max_iterations=cfg["loop"]["max_iterations"], logger=logger,
            critic_enabled=(args.condition == "C"),
        )
        result_state, iterations, stop = res.state, res.iterations, res.stop_reason
        result_state["verdicts"] = res.verdicts
        if not result_state.get("insights"):
            stop = "synthesis_failed"

    insights = result_state.get("insights", [])
    # Attach the critic's unresolved objections to the affected insights so the
    # reader sees where the reviewer still disagreed. Silence is not agreement.
    verdicts = result_state.get("verdicts") or []
    if verdicts and not verdicts[-1].get("pass"):
        by_id = {}
        for f in verdicts[-1].get("failures", []):
            by_id.setdefault(f.get("insight_id"), []).append(f"{f.get('rule')}: {f.get('detail')}")
        for ins in insights:
            if ins.get("id") in by_id:
                ins["critic_flags"] = by_id[ins["id"]]
    logger.meta.update({"iterations": iterations, "stop_reason": stop})
    md = to_markdown(insights, corpus, logger.meta)
    out_dir = logger.finish(result_state, md, stop_reason=stop, iterations=iterations)
    print(f"{len(insights)} insights -> {out_dir}/output.md")


if __name__ == "__main__":
    main()
