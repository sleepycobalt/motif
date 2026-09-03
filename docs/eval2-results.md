# Eval 2 — v1 vs v2 loop

**Question:** Did the recall check recover the coverage lost in Eval 1 without giving back the precision gains?
**Tool versions:** v1.1-eval (loop as scored in Eval 1) vs v2-eval (adds `missing_theme` recall check using intake topic maps, `silent_deletion` rule with a fix-or-downgrade revise prompt, and participant profiles for the critic's counter-evidence search).
**Corpus and conditions:** same 5 transcripts; condition C only, since v2 changes only the critic and reviser. A and B results from Eval 1 stand.
**Runs:** 3 per version. Three v2 runs crashed before the critic (code edit not applied) and were discarded; the three reported here ran on the corrected tag.
**Scoring:** AI-assisted rating reviewed by one human rater (Eric), blind to version, order R1 R4 R2 R5 R3 R6. Insight count (13–14 vs 15–17) was a partial tell. Four evidence spot-checks per report. Same ground truth as Eval 1.

## Headline

Coverage recovered; precision held.

| | A (Eval 1) | v1 loop | v2 loop |
|---|---|---|---|
| Theme coverage (of 12) | 9.0 (75%) | 6.2 (51%) | 8.3 (69%) |
| T-08 reuse present | 2/3 | 0/3 | 3/3 |
| T-02 process transparency present as a finding | 1/3 | 0/3 | 1/3 |
| Unsupported insights (of 4 checked) | 1.7 | 0.7 | 0.7 |
| Miscalibrated confidence | 1.3 | 1.0 | 0.7 |
| Traps failed (raw) | 2.3 | 2.0 | 3.0 |
| Insights produced | 12.3 | 13.3 | 15.7 |
| Wall time | 3.9 min | 14.9 min | 21.8 min |
| Cost | $0.37 | $1.82 | $2.28 |
| Critic output tokens per call | — | 7–12K | 13–25K |

## Per-report

| Report | Version | Insights | Themes /12 | Traps | Unsupported /4 | Miscal. |
|---|---|---|---|---|---|---|
| R1 | v1 (eval3b) | 13 | 6.5 | 2 | 0 | 1 |
| R2 | v1 (eval1b) | 13 | 7.0 | 3 | 0 | 1 |
| R3 | v1 (eval2b) | 14 | 5.0 | 1 | 2 | 1 |
| R4 | v2 (eval3) | 17 | 8.0 | 4 | 2 | 1 |
| R5 | v2 (eval2) | 15 | 9.0 | 2 | 0 | 0 |
| R6 | v2 (eval1) | 15 | 8.0 | 3 | 0 | 1 |

R5 is the strongest report produced under any condition in either eval.

## Reading the trap count

The raw rise from 2.0 to 3.0 is mostly denominator. P-10 (reuse stated without Bruce's own-data reanalysis nuance) can only be failed by a report that finds reuse; it was n/a for all three v1 runs and failed by all three v2 runs. P-11 (Stephen's historical material used for current claims) was applied for the first time this round and failed once. On the traps applicable to both versions (P-01, P-03, P-04, P-05, P-12), v1 failed 6/15 and v2 failed 5/15.

## What worked

- **`missing_theme`** fired 1–2 times per run and the reviser added the insight each time. Reuse went from 0/3 to 3/3. The intake step, which made no measurable difference in Eval 1, is now the input to the check that recovered coverage.
- **`silent_deletion`** never fired. The fix-or-downgrade instruction held: nothing was removed without a stated reason.
- **Precision held.** Unsupported and miscalibration counts did not move against v2 despite 18% more insights.

## What didn't

- **P-03 (Penni's pro-validation dissent) still fails in 5 of 6 reports.** The critic, given participant profiles and told to look at the outlier, surfaces Stephen as the counter to the quant-frame rejection instead of Penni. Penni's remark is in `penni:0031`, a turn every report cites for other purposes.
- **"Cited but not extracted."** T-11 (deletion as waste, `david:0022`) and T-15 (method hierarchy, `penni:0031`) were absent from all six reports while both turns were cited in all six. The model extracts one finding per turn and stops. A rule that checks whether a cited turn contains a second, unused finding would be the next recall improvement.
- **Every report that found reuse failed P-10.** The nuance is in the cited text (`bruce:0043`) and unused — the same pattern.
- **Cost.** v2's critic thinks 2–3× longer. A run is now 22 minutes and $2.28. Still ~8× faster than the 170-minute manual baseline.
- **Duplication.** R4 produced near-duplicate pairs (I-03/I-06, I-15/I-16). Adding insights under pressure from `missing_theme` can over-split; a dedupe pass would help.

## Rater consistency

The three v1 reports were scored in both evals. Theme sums moved 7.5→7.0, 6.0→5.0, 7.0→6.5 — the second round was slightly stricter (a T-09 convention was tightened), differences within one point. Unsupported and miscalibration counts matched or moved by one.

## Limitations

Single rater, AI-assisted, partial tell from insight count, three runs per version, five transcripts. Differences of one point are within variance; the coverage and reuse shifts are larger than that, the trap shift is not.

## Decision

v2 is the version to package and write up. Open items for v3: a second-finding check on cited turns, a dedupe pass, and a targeted fix for Penni-type dissent (perhaps a per-participant "what does this person disagree with?" pass at intake).
