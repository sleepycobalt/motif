"""
One-command synthesis: transcripts in, report out.

    motif ./transcripts --out report.md
    motif ./transcripts --out report.md --question "What frustrates users about onboarding?"
    motif ./transcripts --out report.md --condition A      # single-prompt baseline, no loop

Runs ingest -> intake -> synthesis -> critic -> revise, and writes the final
report to --out. Full logs (every prompt, response, iteration) land in runs/.
One surface over synth.engine; the MCP server is another.
"""

import argparse
import shutil
import sys
from pathlib import Path

from synth import engine


def main():
    ap = argparse.ArgumentParser(prog="motif", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcripts", help="folder of .docx/.txt/.md transcripts (one speaker turn per line)")
    ap.add_argument("--out", default="report.md", help="where to write the report")
    ap.add_argument("--question", default=None, help="research question to synthesise against")
    ap.add_argument("--config", default=None, help="YAML config (default: config/synth.yaml)")
    ap.add_argument("--condition", choices=sorted(engine.CONDITIONS), default="C")
    ap.add_argument("--max-iterations", type=int, default=None)
    ap.add_argument("--critic-model", default=None)
    ap.add_argument("--keep-processed", default=None, help="folder to keep the processed transcripts in")
    args = ap.parse_args()

    try:
        print(f"ingesting {args.transcripts}")
        processed = engine.ingest(args.transcripts, args.keep_processed, emit=print)
        res = engine.synthesize(
            processed, question=args.question, condition=args.condition,
            max_iterations=args.max_iterations, critic_model=args.critic_model,
            config_path=args.config, emit=print,
        )
    except (ValueError, RuntimeError) as e:
        sys.exit(str(e))
    if not res.ok:
        sys.exit(f"synthesis failed (stop={res.stop_reason}); full logs: {res.run_dir}/")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(res.run_dir / "output.md", out)
    print(f"\nreport written to {out}   (full logs: {res.run_dir}/)")


if __name__ == "__main__":
    main()
