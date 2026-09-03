"""
Run logger. One directory per run:

    runs/<run_id>/
        meta.json          config, condition, corpus, start/end, totals
        calls/NNN_label.json   every prompt + response + usage
        iterations/NN.json     loop state after each iteration
        output.json        final result
        output.md          human-readable report

Nothing is ever overwritten; failed and bad runs are kept — they are
evidence for the case study.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path


class RunLogger:
    def __init__(self, root: str | Path = "runs", condition: str = "C",
                 tag: str = "", config: dict | None = None):
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        self.run_id = f"{ts}-{condition}{('-' + tag) if tag else ''}"
        self.dir = Path(root) / self.run_id
        (self.dir / "calls").mkdir(parents=True, exist_ok=True)
        (self.dir / "iterations").mkdir(exist_ok=True)
        self.t0 = time.time()
        self.n_calls = 0
        self.totals = {"in_tok": 0, "out_tok": 0, "cost": 0.0, "calls": 0}
        self.meta = {
            "run_id": self.run_id,
            "condition": condition,
            "tag": tag,
            "started": datetime.now(timezone.utc).isoformat(),
            "config": config or {},
        }
        self._write("meta.json", self.meta)

    def _write(self, rel: str, obj):
        with open(self.dir / rel, "w", encoding="utf-8") as fh:
            if isinstance(obj, str):
                fh.write(obj)
            else:
                json.dump(obj, fh, indent=2, ensure_ascii=False)

    def record_call(self, label: str, system: str, user: str, result: dict):
        self.n_calls += 1
        self.totals["calls"] += 1
        self.totals["in_tok"] += result["in_tok"]
        self.totals["out_tok"] += result["out_tok"]
        self.totals["cost"] += result["cost"]
        self._write(
            f"calls/{self.n_calls:03d}_{label}.json",
            {"label": label, "system": system, "user": user, **result},
        )
        print(f"  [{label}] {result['model']}  {result['in_tok']}→{result['out_tok']} tok  "
              f"{result['seconds']}s  ${result['cost']:.4f}")

    def record_iteration(self, n: int, state: dict):
        stage = state.get("stage", "state")
        self._write(f"iterations/{n:02d}_{stage}.json", state)

    def note(self, msg: str):
        print(f"  · {msg}")
        with open(self.dir / "notes.txt", "a", encoding="utf-8") as fh:
            fh.write(msg + "\n")

    def finish(self, output: dict, markdown: str | None = None,
               stop_reason: str = "", iterations: int = 0):
        self.meta.update(
            {
                "finished": datetime.now(timezone.utc).isoformat(),
                "wall_seconds": round(time.time() - self.t0, 1),
                "iterations": iterations,
                "stop_reason": stop_reason,
                **self.totals,
                "cost": round(self.totals["cost"], 4),
            }
        )
        self._write("meta.json", self.meta)
        self._write("output.json", output)
        if markdown:
            self._write("output.md", markdown)
        print(f"\nrun {self.run_id}: {iterations} iteration(s), stop={stop_reason}, "
              f"{self.meta['wall_seconds']}s, {self.totals['in_tok']:,}→{self.totals['out_tok']:,} tok, "
              f"${self.meta['cost']}")
        return self.dir
