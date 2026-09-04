"""
Motif MCP server — one server, usable from Claude Code, Cursor, and any MCP host.

    motif-mcp                      # stdio transport; add to your host's MCP config
    MOTIF_REMOTE_URL=https://...   # remote mode: forward to the hosted service

Every tool is a thin call into synth.engine. Nothing here touches prompts,
models, or the loop. Progress from the engine is relayed as MCP log
notifications; stdout belongs to the protocol and the engine never writes
to it. A missing verdict, an empty result, or an unparseable document is a
tool error, never a success with empty content.

Environment:
    MOTIF_RUNS_DIR      where run logs go (default: ./runs)
    MOTIF_CONFIG        YAML config (default: config/synth.yaml in the repo)
    MOTIF_PROCESSED     fallback processed corpus for runs made before corpus snapshots
    MOTIF_REMOTE_URL    switch to remote mode
    ANTHROPIC_API_KEY   local mode only (also read from .env in the working directory)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

import anyio
from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from synth import engine
from surfaces.mcp import remote

log = logging.getLogger("motif.mcp")

RUNS_ROOT = Path(os.environ.get("MOTIF_RUNS_DIR") or (engine.ROOT / "runs"))
CONFIG = os.environ.get("MOTIF_CONFIG") or None
REMOTE = bool(os.environ.get("MOTIF_REMOTE_URL"))

server = MCPServer(
    "motif",
    instructions=(
        "Motif turns interview transcripts into a research synthesis where every insight carries "
        "cited, verified evidence, an honest confidence level, and counter-evidence. Tools: "
        "motif_synthesize (transcripts -> insights + report), motif_critique (check a synthesis, yours "
        "or anyone's, against the transcripts), motif_receipts (verbatim turn text for a citation), "
        "motif_board (a run as a FigJam layout plus use_figma scripts for the host to execute), "
        "motif_runs_get (a run's log and verdicts). Citations are turn ids like 'michelle:0042'."
    ),
    version="0.2.0",
)


class ToolFailure(ToolError):
    """Raised for any outcome the host must not mistake for success; the message reaches the host verbatim."""


def _emitter(ctx: Context, loop: asyncio.AbstractEventLoop):
    """An emit(msg) callable safe to use from the engine's worker thread."""
    count = {"n": 0}

    def emit(msg: str) -> None:
        count["n"] += 1
        # Both channels: log messages reach hosts that set a logging level; progress
        # notifications reach hosts that pass a progress token (Claude Code does).
        asyncio.run_coroutine_threadsafe(ctx.info(msg), loop)
        asyncio.run_coroutine_threadsafe(ctx.report_progress(count["n"], None, msg), loop)
    return emit


def _resolve_corpus(run_id: str | None, transcripts_dir: str | None, emit) -> tuple[Path, list[str] | None]:
    if run_id:
        return engine.corpus_for_run(run_id, RUNS_ROOT)
    if transcripts_dir:
        p = Path(transcripts_dir).expanduser()
        if (p / "manifest.json").exists():
            return p, None
        return engine.ingest(p, emit=emit), None
    raise ToolFailure("give either run_id (to reuse a run's corpus) or transcripts_dir")


async def _in_thread(fn, *args, **kw):
    try:
        return await anyio.to_thread.run_sync(lambda: fn(*args, **kw))
    except (ValueError, LookupError, RuntimeError, remote.RemoteUnavailable, ToolFailure) as e:
        raise ToolFailure(str(e)) from None


# ------------------------------------------------------------------- tools

@server.tool(
    name="motif_synthesize",
    description=(
        "Synthesise a folder of interview transcripts (.docx/.txt/.md, one speaker turn per line, "
        "'Name: text'; label the interviewer 'Interviewer' or 'Researcher') into 8-14 insights, each with a "
        "claim, cited turns with verbatim receipts, confidence, counter-evidence, and a design opportunity. "
        "Condition C (default) runs intake -> synthesis -> critic -> revise until the critic passes or "
        "max_iterations; B skips the critic; A is a single-prompt baseline. Takes minutes and spends API "
        "budget (about $2.50 for 15 transcripts). Returns the run id, the insights JSON, and the report "
        "markdown; full logs are under the run directory. Insights the critic still objected to when the "
        "loop stopped are listed in 'contested'."
    ),
)
async def motif_synthesize(
    ctx: Context,
    transcripts_dir: str | None = None,
    files: list[str] | None = None,
    question: str | None = None,
    condition: str = "C",
    max_iterations: int = 3,
) -> dict[str, Any]:
    if not transcripts_dir and not files:
        raise ToolFailure("give transcripts_dir (a folder) or files (a list of transcript paths)")
    loop = asyncio.get_running_loop()
    emit = _emitter(ctx, loop)
    if REMOTE:
        source = files or transcripts_dir
        processed = await _in_thread(engine.ingest, source, None, None)
        manifest = json.load(open(processed / "manifest.json"))
        transcripts = [{"name": m["name"], "text": (processed / f"{m['name']}.txt").read_text()} for m in manifest]
        return await _in_thread(remote.synthesize, transcripts, question=question, condition=condition,
                                max_iterations=max_iterations)

    source = files or transcripts_dir
    processed = await _in_thread(engine.ingest, source, None, emit)
    res = await _in_thread(engine.synthesize, processed, question=question, condition=condition,
                           max_iterations=max_iterations, config_path=CONFIG, runs_root=RUNS_ROOT, emit=emit)
    if not res.ok:
        raise ToolFailure(f"synthesis failed (stop={res.stop_reason}); logs in {res.run_dir}")
    return {
        "run_id": res.run_id,
        "run_dir": str(res.run_dir),
        "stop_reason": res.stop_reason,
        "iterations": res.iterations,
        "n_insights": len(res.insights),
        "contested": [i["id"] for i in res.insights if i.get("critic_flags")],
        "cost_usd": res.meta.get("cost"),
        "wall_seconds": res.meta.get("wall_seconds"),
        "insights": res.insights,
        "report_markdown": res.markdown,
    }


@server.tool(
    name="motif_critique",
    description=(
        "Run Motif's critic alone over an existing synthesis and return its verdict. Give the synthesis "
        "either as `insights` (Motif's insight JSON) or as `document` (a report in markdown or prose; it is "
        "structured into claims first, with turn ids and quotes copied from the document only). Give the "
        "transcripts either as `run_id` (reuse a Motif run's corpus and intake notes) or `transcripts_dir` "
        "(raw transcripts or a processed corpus); `transcripts` optionally restricts to named transcripts. "
        "Deterministic rules (citation exists, quote matches the turn, interviewer not cited, confidence "
        "threshold) run in code; the rest are judged by the model against the full transcripts. Without "
        "intake notes the missing_theme rule is skipped and the verdict says so. A synthesis with no turn "
        "citations fails bad_citation on every insight: the critic can only check what it can trace."
    ),
)
async def motif_critique(
    ctx: Context,
    insights: list[dict[str, Any]] | None = None,
    document: str | None = None,
    run_id: str | None = None,
    transcripts_dir: str | None = None,
    transcripts: list[str] | None = None,
    question: str | None = None,
    structure_with_model: bool = False,
) -> dict[str, Any]:
    if (insights is None) == (document is None):
        raise ToolFailure("give exactly one of insights (JSON) or document (markdown/prose)")
    loop = asyncio.get_running_loop()
    emit = _emitter(ctx, loop)
    if REMOTE:
        return await _in_thread(remote.critique, insights=insights, document=document, run_id=run_id,
                                transcripts_dir=transcripts_dir, question=question)

    processed, names = await _in_thread(_resolve_corpus, run_id, transcripts_dir, emit)
    names = transcripts or names
    intake_notes, q = None, question
    if run_id:
        run = await _in_thread(engine.load_run, run_id, RUNS_ROOT, ("meta",))
        q = q or run["meta"].get("config", {}).get("question")
        out_json = Path(run["run_dir"]) / "output.json"
        if out_json.exists():
            intake_notes = json.load(open(out_json, encoding="utf-8")).get("intake") or None
    if insights is not None:
        insights = [{k: v for k, v in i.items() if k != "critic_flags"} for i in insights]
        out = await _in_thread(engine.critique, insights, processed, question=q, intake_notes=intake_notes,
                               names=names, config_path=CONFIG, runs_root=RUNS_ROOT, emit=emit)
    else:
        out = await _in_thread(engine.critique_document, document, processed, question=q, names=names,
                               config_path=CONFIG, runs_root=RUNS_ROOT, emit=emit,
                               force_model=structure_with_model)
    return out


@server.tool(
    name="motif_receipts",
    description=(
        "Return the verbatim transcript text for turn ids (e.g. ['michelle:0042', 'david:0017']) so a "
        "citation can be verified. Give `run_id` to look up against the corpus that run cited, or "
        "`transcripts_dir`. Each receipt says who spoke and whether the speaker was the interviewer "
        "(interviewer turns are never evidence). Ids that do not exist are listed under 'missing'; if none "
        "exist the call fails."
    ),
)
async def motif_receipts(
    ctx: Context,
    turn_ids: list[str],
    run_id: str | None = None,
    transcripts_dir: str | None = None,
    transcripts: list[str] | None = None,
) -> dict[str, Any]:
    loop = asyncio.get_running_loop()
    emit = _emitter(ctx, loop)
    if REMOTE:
        return await _in_thread(remote.receipts, turn_ids=turn_ids, run_id=run_id)
    processed, names = await _in_thread(_resolve_corpus, run_id, transcripts_dir, emit)
    return await _in_thread(engine.receipts, turn_ids, processed, transcripts or names)


@server.tool(
    name="motif_runs_get",
    description=(
        "Return a Motif run's record: meta (condition, transcripts, iterations, stop reason, tokens, cost), "
        "notes, per-iteration critic verdicts with every failure (insight id, rule, detail), and the final "
        "verdicts. `include` may add 'insights', 'report' (the markdown), or 'calls' (per-call model, tokens "
        "and timing; never prompt bodies)."
    ),
)
async def motif_runs_get(
    ctx: Context,
    run_id: str,
    include: list[str] | None = None,
) -> dict[str, Any]:
    if REMOTE:
        return await _in_thread(remote.get_run, run_id)
    inc = tuple(include) if include else ("meta", "notes", "iterations", "verdicts")
    inc = tuple(sorted(set(inc) | {"meta"}))
    return await _in_thread(engine.load_run, run_id, RUNS_ROOT, inc)


@server.tool(
    name="motif_board",
    description=(
        "Lay out a Motif run on a FigJam board: one section per insight with a claim sticky (colour = "
        "confidence: green high, yellow medium, orange low), white receipt stickies with the verbatim quotes, "
        "pink counter-evidence stickies wired to the claim by 'contested by' connectors, a blue opportunity "
        "sticky, and a violet sticky for any critic objection still open. origin_x/origin_y place the grid away "
        "from existing content. Returns the layout as JSON and one "
        "ready-to-run `use_figma` script per section. Motif holds no Figma credentials: the host runs the "
        "scripts through Figma's MCP server (skills figma-use and figma-use-figjam) against a board URL, then "
        "reads the board back with get_figjam. A script that returns no node ids has failed."
    ),
)
async def motif_board(ctx: Context, run_id: str, columns: int = 2, origin_x: float = 0, origin_y: float = 0) -> dict[str, Any]:
    if REMOTE:
        return await _in_thread(remote.get_run, run_id)
    return await _in_thread(engine.board, run_id, RUNS_ROOT, max(1, columns), (origin_x, origin_y))


def main() -> None:
    logging.basicConfig(level=logging.WARNING, stream=__import__("sys").stderr,
                        format="%(name)s %(levelname)s %(message)s")
    log.setLevel(logging.INFO)
    log.info("motif-mcp starting (%s mode, runs -> %s)", "remote" if REMOTE else "local", RUNS_ROOT)
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
