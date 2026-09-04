# Motif — listing copy for MCP directories

Use these verbatim (or trimmed to the directory's limits) wherever MCP
servers are indexed. Keep the numbers in sync with README.md.

## Name

Motif

## One line (≤ 100 chars — the official registry's `description` cap)

Research synthesis with receipts: cited, critic-checked insights from interview transcripts.

## Short description (≤ 300 chars)

Motif turns a folder of interview transcripts into 8–14 research insights, each with a claim, verbatim receipts from cited turns, a numerically defined confidence level, counter-evidence, and a design opportunity. A critic checks every insight against the transcripts; nothing passes by silence.

## Long description

Motif is an agentic loop for qualitative research synthesis, built for design
and research teams who need output they can trust and trace. Intake maps each
transcript; synthesis produces insights; a critic checks every one against the
transcripts using editable plain-language rules (unsupported claims, missing
dissent, overconfidence, merged findings, themes present in the corpus but
absent from the report); revision fixes what the critic flagged and may not
delete an insight to make an objection go away. Insights the critic still
objects to when the loop stops are marked as contested.

The MCP server exposes five tools: `motif_synthesize` (transcripts → insights
and report), `motif_critique` (check any synthesis, as JSON or as a markdown
document, against its transcripts), `motif_receipts` (verbatim turn text for
any citation), `motif_board` (a run laid out for FigJam, executed by the host
through Figma's MCP server), and `motif_runs_get` (a run's log and verdicts).
Runs locally with your Anthropic API key; every prompt, response, and
iteration is saved so you can see what the critic objected to and how the
synthesis changed.

Evaluated on 15 real research interviews against a human-built ground truth
with blind scoring: fewer unsupported insights and fewer overstated
confidence levels than a single-prompt synthesis, at the cost of time and
API spend (about 20 minutes and $2.50 for 15 transcripts).

## Tags

research, ux-research, qualitative, synthesis, interviews, transcripts,
citations, evaluation, figjam, design, anthropic, claude

## Category

Research & Data Analysis

## Links

- Repository: https://github.com/sleepycobalt/motif
- Install: https://github.com/sleepycobalt/motif/blob/main/surfaces/mcp/README.md
- Maker: https://etot.design
- Licence: MIT (code); sample corpus CC-BY-NC

## Requirements

Python 3.10+, an Anthropic API key. Local mode only until the hosted service
ships.
