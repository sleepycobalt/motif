"""
Acceptance check for motif_critique against the eval2 human scoring.

Two paths, both through the MCP server (not the engine directly):
  1. JSON path: R1-R6 insights from runs/<id>/output.json (mapping in eval2/key.json),
     critiqued with run_id so the run's own intake notes are used.
  2. Markdown path: eval2/blind/R5.md as plain markdown, no key, no run output.
     Optionally repeated with structure_with_model=True (--model-path) to exercise
     the free-form structuring prompt as well.

Agreement targets are copied from eval2/scoring.md (per-report "Unsupported"
lines and the P-03 / P-05 trap rows). Two comparisons:
  - unsupported: for each insight the sheet checked, does the critic's
    `unsupported` rule agree with the sheet's finding?
  - dissent traps: P-03 (Penni's dissent missing from the quant-frame insight) and
    P-05 (positive support case missing from the guidance-gap insight) — does the
    critic raise `missing_counterexample` on that insight iff the sheet marked
    the trap failed?
Writes eval2/critique-acceptance.json and prints a table. Spends API budget
(one critic call per report).
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

from mcp.client import Client
from mcp.client.stdio import StdioServerParameters

ROOT = Path(__file__).resolve().parent.parent

# Copied from eval2/scoring.md ("Unsupported insights: ... checked (...)" lines; P-03/P-05 rows).
TARGETS = {
    "R1": {"checked": ["I-01", "I-03", "I-07", "I-09"], "unsupported": [],
           "P-03": ("I-05", True), "P-05": ("I-09", True)},
    "R2": {"checked": ["I-02", "I-08", "I-11", "I-12"], "unsupported": [],
           "P-03": ("I-05", True), "P-05": ("I-09", True)},
    "R3": {"checked": ["I-05", "I-06", "I-07", "I-13"], "unsupported": ["I-05", "I-13"],
           "P-03": ("I-07", False), "P-05": ("I-13", True)},
    "R4": {"checked": ["I-05", "I-08", "I-14", "I-17"], "unsupported": ["I-08", "I-17"],
           "P-03": ("I-04", True), "P-05": ("I-05", True)},
    "R5": {"checked": ["I-06", "I-09", "I-10", "I-12"], "unsupported": [],
           "P-03": ("I-02", True), "P-05": ("I-12", False)},
    "R6": {"checked": ["I-15", "I-05", "I-09", "I-10"], "unsupported": [],
           "P-03": ("I-06", True), "P-05": ("I-05", True)},
}
TRANSCRIPTS = ["michelle", "david", "bruce", "stephen", "penni"]


def compare(label, by_rule, target):
    unsup = set(by_rule.get("unsupported", []))
    mc = set(by_rule.get("missing_counterexample", []))
    rows = []
    for iid in target["checked"]:
        sheet = iid in target["unsupported"]
        rows.append({"report": label, "check": "unsupported", "insight": iid, "sheet": sheet,
                     "critic": iid in unsup, "agree": sheet == (iid in unsup)})
    for trap in ("P-03", "P-05"):
        iid, failed = target[trap]
        rows.append({"report": label, "check": trap, "insight": iid, "sheet": failed,
                     "critic": iid in mc, "agree": failed == (iid in mc)})
    return rows


async def run(args):
    key = json.load(open(ROOT / "eval2" / "key.json"))
    params = StdioServerParameters(command=sys.executable, args=["-m", "surfaces.mcp.server"], cwd=str(ROOT))
    results = {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "paths": {}, "rows": []}
    logs, progress = [], []

    async def on_log(msg):
        logs.append(str(getattr(msg, "data", msg)))

    async def on_progress(*a, **k):
        progress.append(a)

    # log_level is required for the server's log notifications to be delivered at all
    async with Client(params, logging_callback=on_log, log_level="info", read_timeout_seconds=3600) as client:
        tools = [t.name for t in (await client.list_tools()).tools]
        print("server tools:", tools)
        assert "motif_critique" in tools

        if not args.markdown_only:
            for label in sorted(TARGETS):
                run_id = key[label]["run_id"]
                out = json.load(open(ROOT / "runs" / run_id / "output.json"))
                insights = [{k: v for k, v in i.items() if k != "critic_flags"} for i in out["insights"]]
                t0 = time.time()
                res = await client.call_tool("motif_critique", {"insights": insights, "run_id": run_id},
                                             progress_callback=on_progress)
                if res.is_error:
                    raise SystemExit(f"{label}: tool error: {res.content}")
                data = res.structured_content or json.loads(res.content[0].text)
                data = data.get("result", data)
                by_rule = data["summary"]["by_rule"]
                results["paths"][f"{label}-json"] = {
                    "run_id": data["run_id"], "source_run": run_id, "pass": data["verdict"]["pass"],
                    "by_rule": by_rule, "skipped_rules": data["verdict"].get("skipped_rules"),
                    "seconds": round(time.time() - t0, 1)}
                results["rows"] += compare(f"{label}-json", by_rule, TARGETS[label])
                print(f"{label} json: pass={data['verdict']['pass']} rules={ {k: len(v) for k, v in by_rule.items()} } "
                      f"{round(time.time() - t0)}s")

        doc = (ROOT / "eval2" / "blind" / "R5.md").read_text(encoding="utf-8")
        variants = [("R5-markdown", False)] + ([("R5-markdown-model", True)] if args.model_path else [])
        for label, force in variants:
            t0 = time.time()
            res = await client.call_tool("motif_critique", {
                "document": doc, "transcripts_dir": str(ROOT / "data" / "processed"),
                "transcripts": TRANSCRIPTS, "structure_with_model": force}, progress_callback=on_progress)
            if res.is_error:
                raise SystemExit(f"{label}: tool error: {res.content}")
            data = res.structured_content or json.loads(res.content[0].text)
            data = data.get("result", data)
            by_rule = data["summary"]["by_rule"]
            ins = data["insights"]
            results["paths"][label] = {
                "run_id": data["run_id"], "source_format": data["source_format"], "n_insights": len(ins),
                "insight_ids": [i.get("id") for i in ins], "pass": data["verdict"]["pass"], "by_rule": by_rule,
                "skipped_rules": data["verdict"].get("skipped_rules"), "seconds": round(time.time() - t0, 1)}
            results["rows"] += compare(label, by_rule, TARGETS["R5"])
            print(f"{label}: format={data['source_format']} insights={len(ins)} pass={data['verdict']['pass']} "
                  f"rules={ {k: len(v) for k, v in by_rule.items()} } {round(time.time() - t0)}s")

    results["server_log_lines"] = len(logs)
    results["server_progress_events"] = len(progress)
    rows = results["rows"]
    summary = {}
    for check in ("unsupported", "P-03", "P-05"):
        rs = [r for r in rows if r["check"] == check]
        summary[check] = {"agree": sum(r["agree"] for r in rs), "of": len(rs)}
    results["summary"] = summary
    (ROOT / "eval2" / "critique-acceptance.json").write_text(json.dumps(results, indent=2))
    print("\n| report | check | insight | sheet | critic | agree |\n|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['report']} | {r['check']} | {r['insight']} | {r['sheet']} | {r['critic']} | {'yes' if r['agree'] else 'NO'} |")
    print("\nsummary:", json.dumps(summary))
    print("written eval2/critique-acceptance.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--markdown-only", action="store_true")
    ap.add_argument("--model-path", action="store_true", help="also run R5 through the model structurer")
    asyncio.run(run(ap.parse_args()))
