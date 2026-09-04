# Contributing to Motif

Motif is small on purpose. Most changes a team will want are config edits, not code. This file says where each kind of change goes.

## Change a critic rule (no code)

Rules live in `config/synth.yaml` under `critic.rules`. Each has:

```yaml
- id: missing_counterexample      # short snake_case name; appears in failure reports
  severity: fail                  # fail blocks a pass; warn is reported but doesn't block
  check: model                    # model = the critic reads for it; deterministic = checked in code
  description: >
    Plain-language instruction the critic follows. Write it the way you'd brief a
    careful colleague. Say what to look for and what counts as a failure.
```

To add a model-judged rule, add a block. To retire one, delete it. To make one stricter or looser, reword the description. Re-run and compare `runs/<id>/iterations/*_check.json` before and after.

Deterministic rules (`check: deterministic`) need a matching check in `synth/agents.py::deterministic_checks`; their config block still controls severity and any thresholds (see `confidence_threshold`).

## Change what "confidence" means (no code)

```yaml
- id: confidence_threshold
  high_min_sources: 4
  medium_min_sources: 2
  high_forbids_counter: true
```

These numbers are the definition. Change them here, not in prompts.

## Change models, budgets, or rounds (no code)

```yaml
models:  { intake: ..., synthesis: ..., critic: ... }
loop:    { max_iterations: 3 }
synthesis: { min_insights: 8, max_insights: 14, max_tokens: 64000 }
critic:  { max_tokens: 32000 }
```

If a run's synthesis or critic returns nothing, raise the relevant `max_tokens` first — thinking counts against it.

## Add a deterministic rule (code)

1. Add the config block with `check: deterministic`.
2. In `synth/agents.py::deterministic_checks`, add a branch keyed on the rule id that appends a failure dict: `{"insight_id", "rule", "severity", "detail", "turns"}`.
3. Test it offline with a stubbed model — see the pattern in the repo history for `quote_mismatch` — before spending API calls.

Rule of thumb: if it can be computed, compute it. Only ask the model what only a reader can answer.

## Change a prompt (code)

All prompts are in `synth/prompts.py`. The insight schema is shared by synthesis, revise, and critic; change it in one place. Any change to prompts is a change to the instrument — re-run the eval before trusting new outputs.

## Run the evaluation

```bash
# three conditions on a fixed transcript subset
for i in 1 2 3; do python -m synth.run --condition C --transcripts michelle,david,bruce,stephen,penni --tag mychange$i; done
python scripts/eval_pack.py runs/<...> --out eval3
```

Score blind against `docs/ground-truth.md` using the generated `scoring-template.md`. Don't open `key.json` until scoring is done. Method and prior results: `docs/eval1-results.md`, `docs/eval2-results.md`.

## Add a surface (code)

`core/` (loop controller, logger, LLM client, config) and `synth/` (agents, corpus, prompts, report) are the engine and know nothing about where they run. `synth/cli.py` is one surface. A FigJam plugin, an MCP server, or a web UI should call the same functions — ingest → intake → synthesise → critique → revise — and never re-implement the loop.

## Add a tool on the core

Another loop (design critique, accessibility audit) reuses `core/` unchanged: supply `produce`, `check`, and `revise` callables to `core.loop.run_loop`, log through `core.logger.RunLogger`, call models through `core.llm.call`. Keep tool-specific prompts, rules, and corpus handling in their own package beside `synth/`.

## Conventions

- Every citation is a turn id (`name:0042`) plus a verbatim receipt. No exceptions.
- Silence is never approval: a missing verdict, an empty result, or a parse failure is a hard failure.
- Bad runs are evidence. Keep them (they're gitignored, not deleted).
- Log durable decisions in `docs/log.md`; things worth writing up in `docs/case-study-notes.md`.

## Data

The sample corpus is CC-BY-NC (see `LICENSE`). Don't use it for commercial work, and don't commit your own transcripts unless you have the right to publish them.
