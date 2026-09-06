# Spec — Motif v3 evaluation

*For a build chat, after the FigJam plugin ships. Answers the open items from Evals 1 and 2, and the
items logged as "v3 eval item" during the part-2 and part-3 builds. Budget ≈ $25–40 API, one scoring
session. Revised 2026-09-06: change list extended, instrument frozen, success bars pre-registered,
run plan costed.*

## The instrument under test: v2.1-eval (frozen 2026-09-06)

Tag `v2.1-eval` = commit `3675228`. It is **v2-eval, as scored in Eval 2, plus exactly one
deterministic change**: the counter-receipt handling of 2026-09-05 (`ec58797`). `synth/report.py`
prints receipts for counter-evidence as well as evidence, and `quote_mismatch` treats a
counter-evidence entry with no receipt as absence rather than a mismatch; evidence without a receipt
still fails. That change was made because Motif's own report did not round-trip through its own
critic (six mechanical failures on a clean report; `docs/part3-notes.md`, 2026-09-05).

That it is the *only* change was verified, not assumed, by reading every commit touching the
instrument since the Eval 2 runs of 2026-09-03:

| Path | Change since Eval 2 | Affects the loop? |
|---|---|---|
| `synth/agents.py` | one hunk, `ec58797`, the counter-receipt handling | yes — the change above |
| `synth/prompts.py` | `STRUCTURE_SYSTEM` / `STRUCTURE_USER` added (`9605328`) | no — used only by the critique-document surface |
| `synth/synth.yaml` | header comment only (`synth-loop` → `Motif`); rules, thresholds, models, budgets byte-identical | no |
| `core/loop.py` | untouched | no |
| `synth/engine.py` | loop wiring moved out of `synth/run.py` (`9605328`) | no — refactor; ingest checked byte-for-byte, live regression in `docs/part2-notes.md` |

Every v3 change below is built on top of that tag and is off unless a condition's config turns it on.
The **control** condition therefore reproduces Eval 2's instrument with the one counter-receipt fix,
and any difference between control and Eval 2's v2 numbers is run-to-run variance plus that fix.

## Open items (from docs/eval2-results.md and the case study ledger)
1. **Cited but not extracted.** T-11 and T-15 were absent from every report while the turns containing them were cited in every report for something else. Also P-10 (Bruce's reanalysis nuance sits unused in a cited turn).
2. **Duplication.** `missing_theme` over-splits; R4 had near-duplicate pairs.
3. **Outlier dissent.** Penni's pro-validation view missed in 5/6 reports despite profiles.
4. **Stronger critic.** Research question 4: does Opus 5 as critic change outcomes, or is the gap structural?
5. **The loop never passes.** Is `max_iterations` with 2–3 outstanding objections a ceiling or a feature?

## Changes to test (each as its own rule or step, config-switchable)

From Eval 2:

- `second_finding`: a critic rule that, for each cited turn, asks whether the turn contains a distinct finding no insight uses; reports with insight_id "*". *(model rule; config only)*
- `dedupe`: flags insight pairs above a similarity threshold and asks the reviser to merge or differentiate. *(implemented as the deterministic rule `duplicate_insight`, warn — see the deviation note below)*
- `dissent_at_intake`: intake produces, per participant, "positions this person holds that most others don't"; the critic gets that list for `missing_counterexample`.
- Critic model swap: Sonnet 5 vs Opus 5, same rules. *(already supported: `models.critic`)*
- Iteration cap 3 vs 5, with `no_progress` retained. *(already supported: `loop.max_iterations`)*

Added 2026-09-06, from the "v3 eval item" lines in `docs/part2-notes.md` and `docs/part3-notes.md`:

- **(a) `critic_citation` — the critic citing an interviewer turn in its own evidence.** In
  `runs/20260904-165114-critique-doc/output.json` the I-06 `missing_counterexample` failure lists
  `sam:0068`, whose speaker `motif_receipts` reports as "Researcher 1", interviewer=true. The
  `interviewer_cited` rule runs in code against the *synthesis's* citations only; the model-judged
  rules' `turns` lists never pass through it. **Change:** after the verdict is assembled, run every
  model-judged failure's `turns` through the same existence-and-interviewer check the synthesis's
  citations get. A turn that fails is removed from that failure's `turns` list — so the reviser is
  never sent to an interviewer turn — and one warn-severity `critic_citation` failure records what
  was stripped, so the critic's error is reported rather than hidden. Deterministic, no model call.
- **(b) A pasted document's recommendations are absorbed, not checked.** The summary's "Key
  Opportunities" section (three bullets) was absorbed by the model structurer into the `opportunity`
  fields of the nine barrier claims (`runs/20260904-165114-critique-doc/output.json`,
  `source_format: model`), so nothing in it was checked for evidence and `vague_opportunity` saw only
  the redistributed text. **Decision: report as unevaluated, do not structure as claims.** Structuring
  a recommendations bullet as a claim would invent an evidence set the document never offered, and the
  critic would then fail it under `bad_citation` — noise, not signal. The honest output is to say what
  was not checked, which is what `skipped_rules` already does for `missing_theme`. **Change:**
  `critique_document` detects headed sections the structuring did not turn into claims (heading
  matching opportunities / recommendations / next steps / implications) and returns them under
  `unevaluated_sections`, which the verdict summary and the plugin's verdict screen state.
  Deterministic, no model call. Affects the critique surface only; the synthesis loop never runs it.
- **(c) `duplicate_receipt` — the same turn cited twice as two receipts.** I-06 cited `david:0026`
  twice in the user's Figma run of 2026-09-05; Eval 2's R1 scoring note records the same for I-04 and
  I-11 ("cite the same turn twice to pad the evidence line"). It inflates the receipt count without
  adding evidence. **Change:** a deterministic `duplicate_receipt` rule, severity **warn**, naming the
  repeated turns. Warn, not fail, because the claim is still supported — the padding is cosmetic, and
  a fail would send the reviser to rewrite a sound insight.
- **(d) Should `confidence_threshold` scale with corpus size? Proposal only — not tested here.**
  Observed in the Figma run: with two transcripts every insight is capped at "low", because `high`
  needs 4+ participants and `medium` needs 2+, so a two-transcript corpus can never reach high and
  reaches medium only when both participants back the claim. The proposal is to make the thresholds a
  fraction of the corpus rather than absolute, e.g. `high_min_sources = max(2, min(4, ceil(0.6 n)))`
  and `medium_min_sources = max(2, min(2, ceil(0.3 n)))`: for n=5 that is high 3, medium 2 (today: 4
  and 2); for n=15, high 4, medium 2 (unchanged); for n=2, high 2, medium 2. **Not tested in v3**,
  for a stated reason: it changes the meaning of every confidence level, so every prior
  miscalibration count and the whole trap set would need re-scoring against a new definition, which is
  a second scoring session and a second baseline — outside this budget. It is a v4 item. In the
  meantime the plugin's confidence chip says how many of the corpus back an insight ("low · 1 of 2"),
  which is the reading the threshold change would have made explicit.

**Deviation from the spec's `dedupe` wording, and why.** The original line asks for a
"deterministic-plus-model pass after revise". Implemented as a deterministic critic rule instead: it
flags the pair, and the *existing* reviser merges or differentiates it as it does for every other
failure. This costs no extra model call (an extra pass would be one Sonnet call per iteration, about
$0.09 each, ~$0.18 per run, ~$0.55 across the condition) and it reuses the loop that already exists.
If the rule fires and the reviser ignores it, that is the finding, and a dedicated pass becomes a v4
item.

## Design

- Same five transcripts (michelle, david, bruce, stephen, penni), same ground truth
  (`docs/ground-truth.md`), same rubric, same blind procedure.
- Four conditions at 3 runs each, 12 runs, per the spec's prioritisation:

| # | Condition | Config | What it answers |
|---|---|---|---|
| 1 | **control** — v2.1-eval unchanged | `eval3/configs/control.yaml` | the baseline these runs are measured against, on today's models |
| 2 | **all-v3** — `second_finding` + `duplicate_insight` + `dissent_at_intake` + (a) + (c) | `eval3/configs/all-v3.yaml` | open items 1, 2, 3 and the added items |
| 3 | **opus-critic** — control with Opus 5 as critic | `eval3/configs/opus-critic.yaml` | open item 4 |
| 4 | **cap5** — control with `max_iterations: 5` | `eval3/configs/cap5.yaml` | open item 5 |

  Condition 2 carries (a) and (c) as well as the spec's three, because they are v3 changes like the
  rest and both are critic-side. This confounds them with the three, so the report states each rule's
  **firing count per run** — if `critic_citation` and `duplicate_receipt` never fire, they cannot
  explain a difference; if they fire often, the confound is real and named.
- Blind pack via `scripts/eval_pack.py`; `key.json` stays closed until every sheet is filled.
- Report per the `docs/evalN-results.md` template.

## Pre-registered success bars

Written before the first paid run. Baselines are the three v2 runs of Eval 2 (R4, R5, R6), read from
`eval2/scoring.md` and `eval2/metrics.csv`; per-report values are given so the arithmetic can be
checked.

| # | Bar | Baseline (v2, n=3) | Passes if |
|---|---|---|---|
| 1 | **Second finding.** T-11 and T-15 each scored ≥ 0.5 | T-11: 0, 0, 0 → 0/3. T-15: 0, 0, 0 → 0/3 | each theme ≥ 0.5 in ≥ 2 of the 3 **all-v3** runs |
| 2 | **No coverage loss.** Mean theme sum over the other ten themes (T-01…T-10) | 8.0, 9.0, 8.0 → mean 8.33 of 10 | all-v3 mean ≥ **7.83** (baseline − 0.5) |
| 3 | **No precision loss.** Unsupported insights (of 4 checked) and miscalibrated confidence, per report | unsupported 2, 0, 0 → mean 0.67; miscalibrated 1, 0, 1 → mean 0.67 | all-v3 means each ≤ **1.00** (baseline + 0.33, i.e. at most one extra across the three runs) |
| 4 | **Dedupe.** Near-duplicate insight pairs at the rater's judgement | R4 had 2 (I-03/I-06, I-15/I-16); R5, R6 had 0 → 2 pairs across 3 runs | **0 pairs** across the 3 all-v3 runs |
| 5 | **Outlier dissent.** P-03 passes (scored 0) | failed 1, 1, 1 → passed 0/3 | passes in ≥ **2 of 3** all-v3 runs |
| 6 | **Opus critic.** Stated finding, with a decision rule | control, same 12-run session | **adopt** only if theme coverage improves by ≥ 1.0 point **or** unsupported + miscalibrated falls by ≥ 0.5, **and** cost per run stays under $5.00; otherwise report "no change worth the price" |
| 7 | **Iteration cap.** Stated finding, with a decision rule | at cap 3 the loop reached `critic_pass` in 0 of 3 runs (`eval2/metrics.csv`: all `max_iterations`) | **adopt cap 5** only if `critic_pass` is reached in ≥ 1 of 3 runs, **or** theme coverage improves ≥ 1.0 with bar 3 still met |

Mechanical bars, checked from the run logs rather than by the rater:

| # | Bar | Baseline | Passes if |
|---|---|---|---|
| 8 | **(a)** interviewer turns in the critic's own `turns` lists | 1 occurrence found (`runs/20260904-165114-critique-doc`, I-06 → `sam:0068`) | 0 reach the reviser in any all-v3 run; every strip is recorded as a `critic_citation` warn |
| 9 | **(c)** duplicate receipts in the final insight set | R1 note: I-04 and I-11 each cite a turn twice; I-06/`david:0026` in the Figma run | duplicate-receipt count in the final output of each all-v3 run is 0, or the rule fired and the reviser declined (reported either way) |
| 10 | **(b)** a document's recommendations section | absorbed silently into `opportunity` fields | the verdict names the section under `unevaluated_sections` and the count of claims is unchanged |

**Honest reading of n=3.** These are decision rules, not significance tests. With three runs and a
binary outcome, 2/3 against a 0/3 baseline is not significant at any conventional level (Fisher exact
on 2/3 vs 0/3 gives p ≈ 0.4); a one-point move in a theme sum is inside the rater consistency
recorded in Eval 2 (differences within one point). Bars 1, 4 and 5 are therefore worth acting on
because the baseline is **0 of 3** — a change from never to usually — while bars 2 and 3 are guard
rails against a recall change that costs precision, not claims of improvement.

## Run plan and cost

Cost model measured from the three Eval 2 v2 runs (`eval2/metrics.csv` totals $2.2584, $2.3120,
$2.2658; per-call figures from `runs/20260903-18*/calls/*.json`):

| Step | Calls | Model | Mean cost per run |
|---|---|---|---|
| intake | 5 | Haiku 4.5 | $0.118 |
| synthesis | 1 | Sonnet 5 | $0.411 |
| critic | 3 | Sonnet 5 | $1.180 ($0.393 each) |
| revise | 2 | Sonnet 5 | $0.570 ($0.285 each) |
| **total** | 11 | | **$2.279** (measured range $2.258–$2.312) |

Projected per condition:

| Condition | Arithmetic | Per run | × 3 |
|---|---|---|---|
| control | measured | $2.28 | **$6.84** |
| all-v3 | intake +30% output ($0.153) + synthesis ($0.411) + critic +25% ($1.475) + revise +15% ($0.656) | $2.70 | **$8.09** |
| opus-critic | critic × 2.5 (Opus 5 at $5/$25 per MTok vs Sonnet 5 at $2/$10) = $2.950; rest unchanged $1.099 | $4.05 | **$12.15** |
| cap5 | 5 critics ($1.967) + 4 revises ($1.140) + intake and synthesis ($0.529) | $3.64 | **$10.91** |
| | | **12 runs** | **$37.99** |

Items (a)–(c), costed separately:

| Item | How it is verified | Cost |
|---|---|---|
| (a) | offline, against the recorded verdict that exhibits it (`runs/20260904-165114-critique-doc/output.json`), plus firing counts from the all-v3 runs | $0.00 |
| (c) | offline, against recorded outputs containing duplicate receipts, plus firing counts from the all-v3 runs | $0.00 |
| (b) | one live `critique_document` pass on `runs/20260904-165114-critique-doc/input.md`, before-and-after the change | $0.50 (2 × ~$0.25; measured passes ran $0.155–$0.284, `docs/part3-notes.md` 2026-09-05/06) |

**Total: $38.49.** Inside the $25–40 band, with **$1.51 of margin** — which is less than one run of
any condition. A single crash and re-run breaks the band.

**Recommended alternative (Plan B): 10 runs, $31.00.** Conditions 1 and 2 keep 3 runs each, because
bars 1–5 are decided on them. Conditions 3 and 4 drop to 2 runs each, because bars 6 and 7 ask for a
*stated finding with a decision rule*, not a rate out of three: $6.84 + $8.09 + $8.10 + $7.27 +
$0.50 = **$30.80**, leaving ~$9 of margin — enough to re-run any crashed condition and still land
inside the band. The cost of Plan B is that a 2-run condition cannot report "2 of 3" for anything;
it reports both runs and says so.

The choice between Plan A (12 runs, no margin) and Plan B (10 runs, margin) is the user's, and is
taken before the first paid run.

## Procedure

1. Instrument frozen and tagged (`v2.1-eval`, done 2026-09-06).
2. Changes built behind config, offline tests green (done — see `tests/test_eval3_rules.py`).
3. **Ruling on Plan A vs Plan B, and on any bar.** ← nothing is spent before this.
4. Runs, condition by condition (Plan A shown; Plan B is `1 2` for the last two loops):

   ```bash
   cd /path/to/motif && source .venv/bin/activate
   for i in 1 2 3; do python -m synth.run --condition C --config eval3/configs/control.yaml \
       --transcripts michelle,david,bruce,stephen,penni --tag e3-control$i; done
   for i in 1 2 3; do python -m synth.run --condition C --config eval3/configs/all-v3.yaml \
       --transcripts michelle,david,bruce,stephen,penni --tag e3-allv3$i; done
   for i in 1 2 3; do python -m synth.run --condition C --config eval3/configs/opus-critic.yaml \
       --transcripts michelle,david,bruce,stephen,penni --tag e3-opus$i; done
   for i in 1 2 3; do python -m synth.run --condition C --config eval3/configs/cap5.yaml \
       --transcripts michelle,david,bruce,stephen,penni --tag e3-cap5$i; done
   ```

   Each run is 20–35 minutes; the four loops are about 5 hours of wall time in total. The corpus is
   already ingested (`data/processed`, all five names present). `runs/` is retained whatever the
   outcome. A crash after a fix means
   re-tagging and re-running **only the affected condition**, and the report says which condition was
   re-run on which tag and why.
5. `python scripts/eval_pack.py runs/<12 ids> --out eval3`; `key.json` closed.
6. Blind scoring against `docs/ground-truth.md` using the generated template.
7. Open the key; write `docs/eval3-results.md`; update the README table.

## Deliverables

- `docs/eval3-results.md`, updated README table, notes for the case study (a part-1 addendum in
  `docs/case-study-notes.md`).
- A decision on each of the seven scored bars and the three mechanical ones, and a stated ruling on
  whether items (a)–(c) ship in the default config.
