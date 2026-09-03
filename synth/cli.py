"""
One-command synthesis: transcripts in, report out.

    synth-loop ./transcripts --out report.md
    synth-loop ./transcripts --out report.md --question "What frustrates users about onboarding?"
    synth-loop ./transcripts --out report.md --condition A      # single-prompt baseline, no loop

Runs ingest -> intake -> synthesis -> critic -> revise, and writes the final
report to --out. Full logs (every prompt, response, iteration) land in runs/.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(prog="synth-loop", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcripts", help="folder of .docx/.txt/.md transcripts (one speaker turn per line)")
    ap.add_argument("--out", default="report.md", help="where to write the report")
    ap.add_argument("--question", default=None, help="research question to synthesise against")
    ap.add_argument("--config", default=None, help="YAML config (default: config/synth.yaml)")
    ap.add_argument("--condition", choices=["A", "B", "C"], default="C")
    ap.add_argument("--max-iterations", type=int, default=None)
    ap.add_argument("--critic-model", default=None)
    ap.add_argument("--keep-processed", default=None, help="folder to keep the processed transcripts in")
    args = ap.parse_args()

    root = Path(__file__).resolve().parent.parent
    ingest = root / "scripts" / "ingest.py"
    config = Path(args.config) if args.config else root / "config" / "synth.yaml"
    processed = Path(args.keep_processed) if args.keep_processed else Path(tempfile.mkdtemp(prefix="synth-"))

    print(f"ingesting {args.transcripts} -> {processed}")
    r = subprocess.run([sys.executable, str(ingest), args.transcripts, str(processed)])
    if r.returncode != 0:
        sys.exit("ingest failed")

    cmd = [sys.executable, "-m", "synth.run", "--condition", args.condition,
           "--config", str(config), "--processed", str(processed)]
    if args.question:
        cmd += ["--question", args.question]
    if args.max_iterations is not None:
        cmd += ["--max-iterations", str(args.max_iterations)]
    if args.critic_model:
        cmd += ["--critic-model", args.critic_model]

    r = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        sys.exit("synthesis failed")

    # find the run dir from the last line of output
    run_dir = None
    for line in r.stdout.splitlines():
        if "-> " in line and "output.md" in line:
            run_dir = Path(line.split("-> ", 1)[1].strip()).parent
    if not run_dir or not (run_dir / "output.md").exists():
        sys.exit("could not locate run output")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(run_dir / "output.md", out)
    print(f"\nreport written to {out}   (full logs: {run_dir}/)")


if __name__ == "__main__":
    main()
