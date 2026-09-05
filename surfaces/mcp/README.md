# Motif MCP server

One server, usable from Claude Code, Cursor, Claude Desktop, and any MCP host.
A designer or researcher working in an agent environment can say "synthesise
these transcripts" and get the same cited, critic-checked result the CLI
gives. Every tool is a thin call into `synth/engine.py`; the loop, prompts,
and config are shared with the CLI and the FigJam plugin, never duplicated.

## Tools

| Tool | In | Out |
|---|---|---|
| `motif_synthesize` | `transcripts_dir` or `files`, `question`, `condition` (A/B/C), `max_iterations` | run id, insights JSON, report markdown, contested insight ids, cost |
| `motif_critique` | `insights` (JSON) **or** `document` (markdown/prose); `run_id` or `transcripts_dir`; optional `transcripts`, `question` | verdict JSON (`pass`, `failures`, `notes`, `skipped_rules`), summary by rule and by insight, the structured insights, its own run id |
| `motif_receipts` | `turn_ids`; `run_id` or `transcripts_dir` | verbatim turn text, speaker, whether the speaker was the interviewer; `missing` |
| `motif_board` | `run_id`, `columns`, `origin_x`, `origin_y` | FigJam layout JSON + one `use_figma` script per insight for the host to execute through Figma's MCP server |
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

From PyPI, into any Python 3.10+ environment:

```bash
pip install "etot-motif[mcp]"
which motif-mcp                # the server entry point; hosts need this absolute path
```

Or with no install step, if you have [uv](https://docs.astral.sh/uv/): the
command is `uvx --from "etot-motif[mcp]" motif-mcp`. Installed this way the
server uses the packaged config and writes run logs to `~/.motif/runs`
(override with `MOTIF_RUNS_DIR`).

From a Motif checkout:

```bash
git clone https://github.com/sleepycobalt/motif.git
cd motif
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[mcp]"
echo "ANTHROPIC_API_KEY=your-key-here" > .env
ls .venv/bin/motif-mcp        # the server entry point
```

The server reads `ANTHROPIC_API_KEY` from the environment or the repo's
`.env`, writes run logs to `runs/` in the repo (override with
`MOTIF_RUNS_DIR`), and uses `config/synth.yaml`, a symlink to the packaged `synth/synth.yaml` (override with `MOTIF_CONFIG`).
Every host below needs the **absolute** path to `.venv/bin/motif-mcp`; hosts
spawn servers without your shell's PATH.

### Claude Code

```bash
claude mcp add motif -- /ABSOLUTE/PATH/TO/motif/.venv/bin/motif-mcp
```

Optionally install the skill so Claude Code knows the workflow (verify
citations with receipts, mind contested insights, push to FigJam):

```bash
mkdir -p ~/.claude/skills/motif
cp /ABSOLUTE/PATH/TO/motif/surfaces/mcp/skills/motif/SKILL.md ~/.claude/skills/motif/SKILL.md
```

Then in a new Claude Code session:

```
/mcp                                   # motif should show as connected
synthesise ./data/raw/Dataset-2 with motif and open the report
```

Claude Code calls `motif_synthesize`, streams the engine's progress, and can
then call `motif_receipts` to verify any citation or `motif_board` to push
the run onto a FigJam board via Figma's MCP server.

### Cursor

Add to `~/.cursor/mcp.json` (all projects) or `.cursor/mcp.json` (one project):

```json
{
  "mcpServers": {
    "motif": {
      "command": "/ABSOLUTE/PATH/TO/motif/.venv/bin/motif-mcp",
      "env": { "ANTHROPIC_API_KEY": "your-key-here" }
    }
  }
}
```

Restart Cursor; the five `motif_*` tools appear under MCP tools.

### Claude Desktop

Open the config file (Claude menu → Settings → Developer → Edit Config), or
edit it directly:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "motif": {
      "command": "/ABSOLUTE/PATH/TO/motif/.venv/bin/motif-mcp",
      "env": {
        "ANTHROPIC_API_KEY": "your-key-here",
        "MOTIF_RUNS_DIR": "/ABSOLUTE/PATH/TO/motif/runs"
      }
    }
  }
}
```

Quit and reopen Claude Desktop; the tools appear under the tools icon in the
chat box. Claude Desktop cannot open files on your disk, so ask for the
report markdown in the reply, or read it from the run directory.

## Remote mode

Set `MOTIF_REMOTE_URL` and the same five tools forward to the hosted Motif
service (`surfaces/hosted/`) instead of running the engine locally: no Python
dependencies beyond the server itself, and the same results. Your
`ANTHROPIC_API_KEY` is forwarded with each job and used for that job only.
In remote mode a tool's `run_id` is the hosted job id, valid for an hour after
the job finishes; `motif_receipts`, `motif_board`, and `motif_runs_get` take
it. The hosted engine runs with the logger's `redact=True`: prompt and
response bodies are stored as length + SHA-256, corpora are never snapshotted,
and the job's uploads are deleted at expiry. `MOTIF_REMOTE_TOKEN` selects the
paid tier, which is not switched on yet.

```bash
claude mcp add motif -e MOTIF_REMOTE_URL=https://motif-hosted.fly.dev -e ANTHROPIC_API_KEY=your-key-here -- motif-mcp
```

## Board output through Figma's MCP server

`motif_board` returns a layout and scripts; it does not touch Figma. The
host (Claude Code with Figma's MCP server authenticated) runs each script
with `use_figma` against a FigJam board URL and reads the result back with
`get_figjam`. Verified on a real board on 2026-09-04
(`docs/exhibits/step-zero/`, `docs/exhibits/board-r5/`).

## Listing

`listing.md` holds the descriptions for directories that index MCP servers;
`server.json` is the manifest for the official MCP registry (publish after
the package is on PyPI).

## Tests

```bash
.venv/bin/python -m pytest -q tests               # offline: stubbed model, spawns the server over stdio
.venv/bin/python scripts/critique_acceptance.py   # spends API budget: critic vs eval2 human scoring
```
