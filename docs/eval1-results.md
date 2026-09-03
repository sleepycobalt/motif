# Eval 1 — Results

**Tool version:** v1.1-eval (A and B2/B3 ran under v1-eval; the changes between tags were an output-budget increase, an empty-output guard, and a rule-definition bug fix — none affect the synthesis method for A or B).
**Corpus:** 5 transcripts (Michelle, David, Bruce, Stephen, Penni), 33,870 words.
**Conditions:** A single-prompt synthesis; B intake → synthesis; C intake → synthesis → critic → revise, max 3 iterations.
**Runs:** 3 per condition, 9 valid (2 early runs discarded: synthesis hit its output cap and returned nothing — see notes).
**Scoring:** blind, AI-assisted rating reviewed by one human rater (Eric), against `docs/ground-truth.md`. Reports anonymised R1–R9 with headers and critic flags stripped. Four evidence spot-checks per report.

## Headline

The full loop reduced every error measure and reduced theme coverage. It traded recall for precision.

| | A | B | C |
|---|---|---|---|
| Theme coverage (of 12) | 9.0 (75%) | 8.7 (72%) | 6.8 (57%) |
| Traps failed | 2.3 | 2.0 | 1.3 |
| Unsupported insights (of 4 checked) | 1.7 | 1.7 | 0.7 |
| Miscalibrated confidence | 1.3 | 1.3 | 0.0 |
| Insights produced | 12.3 | 12.7 | 13.0 |
| Iterations | — | — | 3 (cap, every run) |
| Wall time | 3.9 min | 7.0 min | 14.9 min |
| Cost | $0.37 | $0.54 | $1.82 |
| Output tokens | 24K | 38K | 88K |

Manual baseline for the same corpus: 170 minutes, 11 insights, 9/11 matched the researchers' full-corpus findings.

## Per-report

| Report | Cond. | Themes /12 | Traps | Unsupported /4 | Miscal. |
|---|---|---|---|---|---|
| R1 | A | 8.5 | 1 | 2 | 1 |
| R5 | A | 9.0 | 3 | 1 | 2 |
| R8 | A | 9.5 | 3 | 2 | 1 |
| R4 | B | 8.5 | 2 | 2 | 1 |
| R7 | B | 8.5 | 1 | 2 | 1 |
| R9 | B | 9.0 | 3 | 1 | 2 |
| R2 | C | 7.5 | 3 | 1 | 0 |
| R3 | C | 6.0 | 0 | 1 | 0 |
| R6 | C | 7.0 | 1 | 0 | 0 |

## What the critic did

- **Confidence calibration went to zero errors** in C. The deterministic threshold (high = 4+ sources, no counter-evidence) is doing this, not the model.
- **Unsupported citations halved.** The remaining ones in C are subtle (a real quote from a turn whose overall meaning cuts the other way). Receipts stop fabrication; only the model-judged `unsupported` rule catches selective quotation, and it catches most.
- **Trap failures fell** from 2.3 to 1.3. P-01 (Penni single-source) and P-04 (external motivation overclaimed) were handled well by C. P-03 (Penni's pro-validation dissent) failed in 6 of 9 reports regardless of condition — the critic's `missing_counterexample` rule is not finding it reliably.
- **Coverage fell.** T-08 (reuse is aspirational) appears in 2/3 A, 3/3 B, 0/3 C. T-07 (time and money) and T-09 (open wanted as gated) were demoted to opportunity statements in two C runs. The reviser's cheapest response to a critic objection is to drop or shrink the insight, and nothing in the loop checks for what is missing.
- **Intake (B) made no measurable difference** to any content metric over A. It cost 80% more time. The intake notes may still be useful as the input to a recall check (below).
- **No run reached `critic_pass`.** Every C run stopped at the iteration cap with 2–3 model-judged objections outstanding, which the output now shows on the affected insights.

## Limitations

- Single rater, not fully blind: the rater had seen C outputs before scoring, though headers and critic flags were stripped.
- Five transcripts, three runs per condition. Differences of ~1 point in trap or unsupported counts are within run-to-run variance (see R2 vs R3).
- Spot-checks covered 4 of ~13 insights per report.
- Ground truth was built partly by the same rater.

## What v2 should do

1. **A recall check.** Use the intake topic maps: any topic present in ≥3 transcripts with no insight covering it is a `missing_theme` failure. This makes the critic look at the corpus, not just the page.
2. **"Fix or downgrade, never delete."** The revise prompt should require that an objected-to insight be repaired or reduced to low confidence, and that deletion be justified explicitly.
3. **Sharpen `missing_counterexample`.** P-03 failed across conditions; give the critic the participant profiles (sector, method) so it knows where to look for dissent.
4. Keep everything else. Confidence thresholds and receipts are solved problems.

## Open questions carried forward

- Does a stronger critic model (Opus 5) change the result, or is the gap structural?
- Does the same pattern hold on the full 15-transcript corpus, where the five report-only themes (T-12–T-14, T-16) become reachable?
