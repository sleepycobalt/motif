"""
Run the synthesis loop from the command line (research/eval entry point).

    python -m synth.run --condition C --transcripts michelle,david,bruce,stephen,penni
    python -m synth.run --condition A            # single prompt, all transcripts
    python -m synth.run --condition B            # intake + synthesis, no critic
    python -m synth.run --condition C --critic-model claude-opus-5 --tag opus-critic

Conditions:
    A  single-prompt synthesis (baseline)
    B  intake -> synthesis, critic disabled
    C  intake -> synthesis -> critic -> revise (full loop)

This is a thin surface over synth.engine.synthesize; the loop lives there.
"""

import argparse
import sys

from synth import engine


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", choices=sorted(engine.CONDITIONS), default="C")
    ap.add_argument("--config", default=str(engine.DEFAULT_CONFIG))
    ap.add_argument("--processed", default="data/processed")
    ap.add_argument("--transcripts", default="", help="comma-separated names; default all")
    ap.add_argument("--question", default=engine.DEFAULT_QUESTION)
    ap.add_argument("--critic-model", default=None)
    ap.add_argument("--max-iterations", type=int, default=None)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    names = [n.strip() for n in args.transcripts.split(",") if n.strip()] or None
    try:
        res = engine.synthesize(
            args.processed, question=args.question, condition=args.condition, names=names,
            config_path=args.config, critic_model=args.critic_model,
            max_iterations=args.max_iterations, tag=args.tag, emit=print,
        )
    except ValueError as e:
        sys.exit(str(e))
    if not res.ok:
        sys.exit(f"synthesis failed (stop={res.stop_reason}); logs in {res.run_dir}/")


if __name__ == "__main__":
    main()
