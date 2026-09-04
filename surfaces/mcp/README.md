# Motif MCP server

One server, usable from Claude Code, Cursor, and any MCP host. A designer or
researcher working in an agent environment can say "synthesise these
transcripts" and get the same cited, critic-checked result the CLI gives.
Every tool is a thin call into `synth/engine.py`; the loop, prompts, and
config are shared with the CLI and the FigJam plugin, never duplicated.

## Tools

| Tool | In | Out |
|---|---|---|
| `motif_synthesize` | `transcripts_dir` or `files`, `question`, `condition` (A/B/C), `max_iterations` | run id, insights JSON, report markdown, contested insight ids, cost |
| `motif_critique` | `insights` (JSON) **or** `document` (markdown/prose); `run_id` or `transcripts_dir`; optional `transcripts`, `question` | verdict JSON (`pass`, `failures`, `notes`, `skipped_rules`), summary by rule and by insight, the structured insights, its own run id |
| `motif_receipts` | `turn_ids`; `run_id` or `transcripts_dir` | verbatim turn text, speaker, whether the speaker was the interviewer; `missing` |
| `motif_board` | `run_id`, `columns` | FigJam layout JSON + one `use_figma` script per insight for the host to execute through Figma's MCP server |
| `motif_runs_get` | `run_id`, `include` | meta, notes, per-iteration verdicts; optionally insights, report, per-call token/timing |

Failure semantics: a missing verdict, an empty synthesis, an unparseable
document, a run that does not exist, or turn ids none of which exist all
return an MCP tool error. There is no empty success.

Progress: every engine progress line (each transcript ingested, each model
call, each critic iteration) is sent twice: as an MCP log notification, which
a host only receives if it has set a logging level, and as a progress
notification, which a host receives if it passed a progress token (Claude Code
does). stdout is the protocol; nothing else ever writes to it.

## Install (local mode)

From a Motif checkout with its virtualenv:

```bash
cd /path/to/motif
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[mcp]"
echo "ANTHROPIC_API_KEY=your-key-here" > .env
motif-mcp --help >/dev/null 2>&1 || true   # entry point exists once installed
```

The server reads `ANTHROPIC_API_KEY` from the environment or the repo's
`.env`, writes run logs to `runs/` in the repo (override with
`MOTIF_RUNS_DIR`), and uses `config/synth.yaml` (override with `MOTIF_CONFIG`).

### Claude Code

```bash
claude mcp add motif -- /path/to/motif/.venv/bin/motif-mcp
```

Then in a Claude Code session (start a new one after adding):

```
/mcp                                   # should list motif as connected
synthesise ./data/raw/Dataset-2 with motif and open the report
```

Claude Code calls `motif_synthesize`, streams the engine's progress, and can
then call `motif_receipts` to verify any citation or `motif_board` to push
the run onto a FigJam board via Figma's MCP server.

### Cursor

Add to `~/.cursor/mcp.json` (or the project's `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "motif": {
      "command": "/path/to/motif/.venv/bin/motif-mcp",
      "env": { "ANTHROPIC_API_KEY": "your-key-here" }
    }
  }
}
```

Restart Cursor; the five `motif_*` tools appear under MCP tools.

## Remote mode

Set `MOTIF_REMOTE_URL` (and `MOTIF_REMOTE_TOKEN`) and the same five tools
forward to the hosted Motif service instead of running the engine locally.
The contract is in `remote.py`. In remote mode this server logs only run ids
and timings; the hosted engine runs with the logger's `redact=True`, which
stores prompt bodies as length + SHA-256 and does not snapshot corpora.
**The hosted service is not live yet**; remote mode fails with a clear error
until it is.

## Board output through Figma's MCP server

`motif_board` returns a layout and scripts; it does not touch Figma. The
host (Claude Code with Figma's MCP server authenticated) runs each script
with `use_figma` against a FigJam board URL and reads the result back with
`get_figjam`. This was verified on a real board on 2026-09-04
(`docs/exhibits/step-zero/`, `docs/exhibits/board-r5/`).

## Tests

```bash
.venv/bin/python -m pytest -q tests          # offline: stubbed model, spawns the server over stdio
.venv/bin/python scripts/critique_acceptance.py   # spends API budget: critic vs eval2 human scoring
```
