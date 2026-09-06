# Eval 3 — v3 changes, Opus critic, iteration cap

**Question:** Do the v3 critic changes fix the "cited but not extracted" failure Eval 2 named, without costing coverage or precision — and does a stronger critic or a higher iteration cap buy anything?
**Tool versions:** `v2.1-eval` (commit `3675228`) as the frozen instrument. **control** = that tag unchanged. **all-v3** = control + `second_finding`, `duplicate_insight`, `duplicate_receipt`, `critic_citation`, `dissent_at_intake`. **opus-critic** = control with Opus 5 as critic. **cap5** = control with `max_iterations: 5`.
**Corpus and conditions:** same 5 transcripts (michelle, david, bruce, stephen, penni; 33,870 words), same ground truth, condition C only. Plan B run plan: 3 runs each for control and all-v3, 2 each for opus-critic and cap5 — 10 runs, $28.50 against a $30.80 budget.
**Runs:** 10 of 10 valid; none crashed, none re-run.
**Scoring:** AI-assisted rating reviewed by one human rater (Eric), blind to condition, in fixed order R1 → R10. Insight count (13–21) was again a partial tell — noted, not acted on. Four evidence spot-checks per report at **fixed positions 1, 4, 7, 10**, a rule chosen before scoring began. Conventions were recorded in `eval3/scoring.md` as they were needed and applied identically to every later report.

## Headline

`second_finding` fixed the failure it was built for, 3 of 3. Nothing else moved much, and one thing that looks like a win isn't.

| | v2 (Eval 2, n=3) | control (n=3) | all-v3 (n=3) | opus-critic (n=2) | cap5 (n=2) |
|---|---|---|---|---|---|
| Theme coverage (of 12) | 8.3 (69%) | 8.7 (72%) | **10.5 (88%)** | 10.3 (85%) | 9.3 (77%) |
| T-11 present (≥0.5) | 0/3 | 1/3 | **3/3** | 1/2 | 0/2 |
| T-15 present (≥0.5) | 0/3 | 1/3 | **3/3** | 2/2 | 2/2 |
| Unsupported (of 4 checked) | 0.7 | 0.0 | 0.0 | 0.0 | 0.0 |
| Miscalibrated confidence | 0.7 | 0.0 | 0.0 | 0.0 | 0.0 |
| Under-confidence (new count) | not tracked | 0.3 | 0.0 | 0.0 | 0.0 |
| Traps failed (raw) | 3.0 | 1.7 | 3.0 | 1.0 | 1.0 |
| Traps failed (the six applicable to every report) | — | 5/18 | 6/18 | 2/12 | 2/12 |
| Insights produced | 15.7 | 14.3 | 19.7 | 18.0 | 16.5 |
| Iterations | 3 (cap 3) | 3 (cap 3) | 3 (cap 3) | 3 (cap 3) | 5 (cap 5) |
| `critic_pass` reached | 0/3 | 0/3 | 0/3 | 0/2 | 0/2 |
| Wall time | 21.8 min | 21.1 min | 24.6 min | 20.7 min | 28.3 min |
| Cost | $2.28 | $2.23 | $2.51 | $3.83 | $3.31 |

## Per-report

| Report | Condition | Insights | Themes /12 | Traps | Unsupported /4 | Miscal. | Under | Iters | Cost |
|---|---|---|---|---|---|---|---|---|---|
| R1 | cap5 | 15 | 8.0 | 1 | 0 | 0 | 0 | 5 | $3.25 |
| R2 | all-v3 | 21 | 10.5 | 3 | 0 | 0 | 0 | 3 | $2.85 |
| R3 | control | 13 | 7.5 | 1 | 0 | 0 | 0 | 3 | $2.04 |
| R4 | all-v3 | 19 | 10.5 | 3 | 0 | 0 | 0 | 3 | $2.31 |
| R5 | opus-critic | 18 | 9.5 | 2 | 0 | 0 | 0 | 3 | $3.95 |
| R6 | control | 15 | 10.0 | 2 | 0 | 0 | 1 | 3 | $2.36 |
| R7 | cap5 | 18 | 10.5 | 1 | 0 | 0 | 0 | 5 | $3.36 |
| R8 | opus-critic | 18 | **11.0** | **0** | 0 | 0 | 0 | 3 | $3.71 |
| R9 | control | 15 | 8.5 | 2 | 0 | 0 | 0 | 3 | $2.30 |
| R10 | all-v3 | 19 | 10.5 | 3 | 0 | 0 | 0 | 3 | $2.36 |

R8 is the strongest report produced under any condition in any of the three evals: 11.0 of 12 themes and **zero traps failed**, including the first pass on P-10 in the 13 reports across Evals 2 and 3 where the trap applied.

## The pre-registered bars

Each bar as written in `docs/specs/motif-v3-eval.md`, with its result.

| # | Bar | Passes if | Result | Verdict |
|---|---|---|---|---|
| 1 | **Second finding.** T-11 and T-15 each scored ≥ 0.5 | each theme ≥ 0.5 in ≥ 2 of 3 all-v3 runs | T-11: 1.0, 1.0, 1.0. T-15: 1.0, 1.0, 1.0 — 3/3 each, at full credit, against an Eval 2 baseline of 0/3 | **PASS** |
| 2 | **No coverage loss.** Mean theme sum over T-01…T-10 | all-v3 mean ≥ 7.83 | 8.5, 8.0, 8.5 → **8.33**, identical to the v2 baseline of 8.33 | **PASS** |
| 3 | **No precision loss.** Unsupported and miscalibrated | all-v3 means each ≤ 1.00 | unsupported **0.0**, miscalibrated **0.0** | **PASS** |
| 4 | **Dedupe.** Near-duplicate insight pairs at the rater's judgement | 0 pairs across the 3 all-v3 runs | 0 pairs — but the `duplicate_insight` rule **never fired**, in any run, so the bar is met without evidence that the rule did it | **PASS, unattributed** |
| 5 | **Outlier dissent.** P-03 passes | passes in ≥ 2 of 3 all-v3 runs | 3/3 — but **control also passed 2/3**, and P-03 passed in 9 of the 10 reports overall against 1 of 6 in Eval 2 | **PASS, not attributable** |
| 6 | **Opus critic.** Adopt only if coverage +≥1.0 **or** unsupported+miscalibrated −≥0.5, **and** cost/run < $5.00 | decision rule | coverage 8.67 → 10.25 (**+1.58**); cost **$3.83**/run. Precision could not fall: it was already 0 | **Rule says adopt** (see caveat below) |
| 7 | **Iteration cap.** Adopt cap 5 only if `critic_pass` in ≥1 of 3 runs, **or** coverage +≥1.0 with bar 3 held | decision rule | `critic_pass` **0 of 2**; coverage 8.67 → 9.25 (**+0.58**) | **Do not adopt** |
| 8 | **(a) `critic_citation`** — interviewer turns in the critic's own objections | 0 reach the reviser; every strip recorded as a warn | fired once (R4), stripping `bruce:0026` and `michelle:0073` (interviewer) and `david:0049` from two objections before revision; warn recorded | **PASS** |
| 9 | **(c) `duplicate_receipt`** — the same turn cited twice in one field | 0 in each all-v3 final output, or the rule fired and the reviser declined | fired 1, 1, 3; final duplicate-receipt count **0, 0, 0**. For contrast, control finished with 1, 1, 0 and cap5's R1 with 3 | **PASS** |
| 10 | **(b) unevaluated recommendations sections** | the verdict names the section; claim count unchanged | **not run.** `report_unevaluated_sections` is false in all four configs and no live `critique_document` pass was made; the change is covered by offline tests only (`tests/test_eval3_rules.py`) | **NOT RUN** |

**The n=3 caveat, as pre-registered:** "These are decision rules, not significance tests. With three runs and a binary outcome, 2/3 against a 0/3 baseline is not significant at any conventional level (Fisher exact on 2/3 vs 0/3 gives p ≈ 0.4); a one-point move in a theme sum is inside the rater consistency recorded in Eval 2 (differences within one point). Bars 1, 4 and 5 are therefore worth acting on because the baseline is **0 of 3** — a change from never to usually — while bars 2 and 3 are guard rails against a recall change that costs precision, not claims of improvement." Bars 6 and 7 rest on **two** runs, not three, under Plan B, and cannot report a rate.

## What worked

- **`second_finding` did exactly what it was built to do.** It fired 8, 8 and 9 times across the three all-v3 runs and nowhere else. In **iteration 1 of all three runs** it named `david:0022` and `penni:0031` by turn id, saying what second finding each carried; both themes ended present as claims in all three reports. This is the tightest causal chain in the eval — the rule names the turn, the reviser adds the insight, the rater scores the theme without knowing either happened.
- **The "cited but not extracted" mechanism, per condition.** Eval 2's diagnosis was that both turns were cited in all six reports and neither finding was extracted. Eval 3 by condition:

  | Condition | `david:0022` cited | T-11 scored | `penni:0031` cited | T-15 scored |
  |---|---|---|---|---|
  | control (n=3) | 1 of 3 | 0, 0.5, 0 | 3 of 3 | 0, 0, 0.5 |
  | **all-v3** (n=3) | **3 of 3** | **1.0, 1.0, 1.0** | **3 of 3** | **1.0, 1.0, 1.0** |
  | opus-critic (n=2) | 2 of 2 | 0, 0.5 | 2 of 2 | 0.5, 0.5 |
  | cap5 (n=2) | 1 of 2 | 0, 0 | 2 of 2 | 0.5, 1.0 |

  The pattern holds outside all-v3: `penni:0031` was cited in **10 of 10** reports and T-15 reached a claim in only the three all-v3 ones; `david:0022` was cited in 7 of 10 and extracted into a deletion-as-waste claim in exactly **3** — the three all-v3 runs, and none of the four other reports that cited it (R5, R7, R8, R9). The two half-credits outside all-v3 (R6, R8) come from the theme's *other* half, unshared agency data, not from `david:0022` at all. R5 is the clean control case: it cites `david:0022` for the navigation barrier and leaves the deletion sentence in the same turn unused.
- **Coverage rose without precision falling.** all-v3 gained 1.8 theme points over control (8.7 → 10.5) and 2.2 over Eval 2's v2, on 5.3 more insights per report, with unsupported and miscalibrated both at zero.
- **Both deterministic v3 rules earned their place.** `duplicate_receipt` fired 5 times across the three all-v3 runs and every instance was fixed before the final output; the untreated conditions finished with 5 duplicate receipts between them. `critic_citation` caught the exact failure it was written for — the critic sending the reviser to an interviewer turn — and stripped it silently but reported it.
- **P-10 was passed for the first time in three evals.** R8 (opus-critic) quoted the nuance itself as counter-evidence to its own reuse insight: "the stuff on Istanbul was in essence, might be analysis of somebody else's data". P-10 applied in 13 reports across Evals 2 and 3 — the three v2 runs and all ten here — and was failed in 12 of them; every one of those 12 cites `bruce:0043` and leaves that line unused.

## What didn't

- **Bar 5 passes and proves nothing.** P-03 — Penni's pro-validation dissent — passed in 3 of 3 all-v3 runs, but also in 2 of 3 control runs and 4 of 4 opus/cap5 runs: **9 of 10 reports overall**, against 1 of 6 in Eval 2. Whatever fixed it, `dissent_at_intake` cannot be credited, because the condition without it fixed it too. The likely cause is the one deterministic change in `v2.1-eval` (counter-evidence receipts now print, so counter-evidence is cheaper to state correctly) or model drift between 2026-09-03 and 2026-09-06. Either way the honest reading is that the Eval 2 open item closed on its own.
- **Bar 4 passes and proves nothing.** `duplicate_insight` never fired in any run at its 0.55 threshold, and the rater found no near-duplicate pairs to fire on. The rule is untested in the wild: Eval 2's R4 duplication was not reproduced, so there was nothing to catch.
- **The trap count rose for all-v3 (1.7 → 3.0) and it is again a denominator.** P-02 can only be failed by a report that finds T-11. all-v3 found T-11 in 3 of 3 and failed P-02 in 3 of 3, because none of the three attached Michelle's deletion-as-integrity dissent to the insight `second_finding` had just prompted. On the **six traps applicable to every report** (P-01, P-03, P-05, P-10, P-11, P-12) the conditions are flat: control 5/18, all-v3 6/18, opus 2/12, cap5 2/12. This is the same reading Eval 2 gave for P-10, one trap along.
- **A new rule creates a new trap exposure.** The insight `second_finding` adds arrives without counter-evidence, and `missing_counterexample` did not catch it in any of the three runs. A recall rule that adds a finding should hand that finding to the counter-evidence search on the next iteration; it currently does not. **v4 item.**
- **P-05 failed in 5 of 10 reports**, and in all three all-v3 runs: the guidance-gap insight stated at high confidence with `Counter-evidence: none`, while the positive case (Michelle's "they were absolutely brilliant" about her library's DMP service, `michelle:0081`/`0083`) sits in the same corpus and is often cited elsewhere in the same report. R6, R7 and R10 show it is avoidable — R6's I-11 makes the positive cases the claim and the near-zero-awareness cases the counter.
- **The loop still never passes.** `critic_pass` was reached in **0 of 10 runs**, at cap 3 and at cap 5, and `no_progress` never fired. Every run stopped on `max_iterations` with objections outstanding. Open item 5 from Eval 2 is answered in the negative: the cap is a ceiling, not a stopping rule the loop reaches.
- **Cost.** all-v3 is $2.51 a run against control's $2.23 (+13%) for +1.8 themes; opus-critic is $3.83 (+72%); cap5 is $3.31 (+48%) for +0.58 themes. Measured costs came in under every projection in the spec (projected $2.28 / $2.70 / $4.05 / $3.64).
- **Bar 10 was never exercised.** Item (b) shipped behind a flag that is off in all four conditions, and the $0.50 live `critique_document` pass the spec costed was not run. It remains verified by offline tests only.

## The cap-5 finding

Both cap5 runs went the full five rounds — `20260906-203138-C-e3-cap51` and `-cap52`, five iterations each, `stop_reason: max_iterations` — without ever reaching `critic_pass` or triggering `no_progress`. Rounds 4 and 5 cost about $1.10 and 7 minutes per run and bought +0.58 theme points on average, inside rater noise; R1 came out at 8.0 and R7 at 10.5, a 2.5-point spread within a two-run condition. The critic keeps finding objections because there are always objections to find: `missing_counterexample` alone fired 6 times in R1 and 5 in R7 across five rounds. Raising the cap does not converge the loop, it buys more rounds of the same. **Cap 3 stays.**

## Rater consistency

No Eval 2 report was re-scored in this round — all ten reports in the blind pack are new v3-session runs — so there is no direct rater-consistency measurement for Eval 3. Two things stand in its place, and both cut towards caution:

- **Convention drift is documented rather than measured.** Seven scoring conventions were added during this session (recorded, dated and user-ruled at the top of `eval3/scoring.md`) and applied identically to every report scored after each was set: P-05 is insight-level; a theme is scored on its stated claim; P-03 turns on consensus framing in the claim text; a theme is scored once and a missing counter charged once, at the matching trap; a thin source is a calibration question, not an unsupported insight; counter-note/opportunity = 0.5 while title or claim text = 1; miscalibration stays overclaiming-only with under-confidence counted separately.
- **Control is therefore not a like-for-like re-score of v2.** Control's 8.67 against Eval 2's v2 8.33 is within the one-point band Eval 2 recorded for the same rater on the same reports, and the conventions behind the two numbers are not identical. The comparison that carries weight in this eval is **within-session, between conditions**, all scored blind under the same conventions on the same day.

## Limitations

Single rater, AI-assisted, blind to condition but not to insight count (13–21, a partial tell as in Eval 2). Three runs for control and all-v3, **two** for opus-critic and cap5 — those two conditions report both runs and no rate. Five transcripts of fifteen. Differences of one theme point are inside rater variance; the T-11/T-15 result (0/3 → 3/3, with the rule naming the turn in iteration 1 of each run) and the `critic_pass` result (0/10) are larger than that, the trap and coverage shifts are not. all-v3 bundles five changes, so a difference cannot be assigned to one of them except where a rule's firing count says so — `second_finding` fired 25 times and `duplicate_insight` zero, which is why the first is credited and the fourth bar is not.

**Unsupported came out 0 of 40 across all ten reports** (four spot-checks each), against 0.7 per report in Eval 2. That number is *zero in a fixed sample*, not zero. The sampling rule — insights at **positions 1, 4, 7, 10**, fewer if the report is shorter — was fixed before scoring began and applied unchanged, including where a report's insight labels ran out of order (R5, R7), so it cannot have been steered towards clean insights. But it checks four insights out of 13–21, and one out-of-sample defect was found and recorded while reading around a sampled insight: R10's I-09 counter-evidence characterises David as having "only ever done a cursory literature/dataset check", where `david:0064` is him describing a hypothetical workflow — the turn does not carry that characterisation. A sample of four will not catch that class reliably. The honest statement is that spot-checked citations were verbatim and on-point in 40 of 40 checks, and that the true unsupported rate is unmeasured.

## Decision

- **Ship `second_finding` in the default config.** It closed the open item it was built for, 3 of 3, with a named causal chain, no coverage loss (bar 2 exactly at baseline), no precision loss, and +13% cost.
- **Ship `duplicate_receipt` and `critic_citation`.** Both are deterministic, cost nothing, fired on real defects, and were fixed or reported in every instance.
- **Ship `duplicate_insight`, on its merits, not on its evidence.** It never fired; it is cheap and deterministic, and the failure it guards (over-splitting under `missing_theme` pressure) is a live risk with `second_finding` now adding insights. Recorded as untested.
- **Do not ship `dissent_at_intake` yet.** Its bar passed, but control passed it too. Re-test it against the closed baseline, or drop it — it costs intake output tokens for an effect this eval cannot see.
- **Do not raise the iteration cap.** Cap 3 stays.
- **Opus critic: the rule says adopt, and the rule is running on two runs.** Coverage +1.58 and $3.83 a run both clear the bar, and R8 is the best report in three evals. But opus-critic's two-run range (9.5–11.0) overlaps control's three-run range (7.5–10.0), and the precision half of the bar could not move because precision was already zero. **Make it the documented option for a high-stakes run, not the default**, and re-test at n=3 if it is ever proposed as the default.
- **v4 items:** hand a `second_finding`-added insight to the counter-evidence search on the next iteration (P-02 failed 3/3 on exactly those insights); count a source only when its turn carries the claim, not merely mentions the topic; a stopping rule the loop can actually reach, since `critic_pass` is 0 of 10 at both caps; run bar 10's live pass; and `confidence_threshold` scaling with corpus size, deferred from this spec with its reason.
