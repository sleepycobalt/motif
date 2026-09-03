"""
Build a blind scoring pack from a set of runs.

    python scripts/eval_pack.py runs/<id1> runs/<id2> ... --out eval

Writes:
    eval/blind/R1.md ... RN.md   reports with condition-revealing content removed, shuffled
    eval/key.json                which R-label is which run (do not open until scoring is done)
    eval/metrics.csv             wall time, tokens, cost, iterations, stop reason per run
    eval/scoring-template.md     one scoring table per report
"""

import argparse
import csv
import json
import random
import re
from pathlib import Path

THEMES = ["T-01","T-02","T-03","T-04","T-05","T-06","T-07","T-08","T-09","T-10","T-11","T-15"]
TRAPS  = ["P-01","P-02","P-03","P-04","P-05","P-10","P-11","P-12"]


def blind(md: str) -> str:
    md = re.sub(r"^# Synthesis — .*$", "# Synthesis", md, flags=re.M)
    md = re.sub(r"^Iterations: .*$", "", md, flags=re.M)
    # remove the critic's unresolved-objection blocks (only condition C has them)
    md = re.sub(r"\n> ⚠ \*\*Contested\*\*.*?(?=\n\n|\Z)", "", md, flags=re.S)
    return md


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--out", default="eval")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()

    out = Path(a.out); (out / "blind").mkdir(parents=True, exist_ok=True)
    runs = [Path(r) for r in a.runs]
    random.Random(a.seed).shuffle(runs)

    key, rows = {}, []
    for i, r in enumerate(runs, 1):
        label = f"R{i}"
        meta = json.load(open(r / "meta.json"))
        md = open(r / "output.md", encoding="utf-8").read()
        (out / "blind" / f"{label}.md").write_text(blind(md), encoding="utf-8")
        key[label] = {"run_id": meta["run_id"], "condition": meta["condition"]}
        n_ins = len(json.load(open(r / "output.json")).get("insights", []))
        rows.append({
            "label": label, "run_id": meta["run_id"], "condition": meta["condition"],
            "insights": n_ins, "iterations": meta.get("iterations", 0),
            "stop_reason": meta.get("stop_reason", ""), "wall_s": meta.get("wall_seconds", 0),
            "in_tok": meta.get("in_tok", 0), "out_tok": meta.get("out_tok", 0),
            "cost_usd": meta.get("cost", 0), "calls": meta.get("calls", 0),
        })

    json.dump(key, open(out / "key.json", "w"), indent=2)
    with open(out / "metrics.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

    tpl = ["# Scoring sheet", "",
           "Score each blind report against docs/ground-truth.md.",
           "Themes: 1 = clearly present with evidence, 0.5 = present but vague/unsupported, 0 = absent.",
           "Traps: 1 = FAILED (did the bad thing), 0 = passed, n/a if the topic never came up.",
           "Unsupported: count insights whose cited evidence does not support the claim on inspection.",
           "Do not open eval/key.json until every sheet is filled in.", ""]
    for i in range(1, len(runs) + 1):
        tpl += [f"## R{i}", "", "| Theme | Score | Note |", "|---|---|---|"]
        tpl += [f"| {t} |  |  |" for t in THEMES]
        tpl += ["", "| Trap | Failed? | Note |", "|---|---|---|"]
        tpl += [f"| {p} |  |  |" for p in TRAPS]
        tpl += ["", "Unsupported insights: ", "Miscalibrated confidence: ", "Overall note: ", ""]
    (out / "scoring-template.md").write_text("\n".join(tpl), encoding="utf-8")

    print(f"{len(runs)} reports -> {out}/blind/  (key in {out}/key.json — don't peek)")
    for row in rows:
        print(f"  {row['label']}: {row['insights']} insights")


if __name__ == "__main__":
    main()
