# Spec — Motif v3 evaluation

*For a build chat, after the FigJam plugin ships. Answers the open items from Evals 1 and 2. Budget ≈ $25–40 API, one scoring session.*

## Open items (from docs/eval2-results.md and the case study ledger)
1. **Cited but not extracted.** T-11 and T-15 were absent from every report while the turns containing them were cited in every report for something else. Also P-10 (Bruce's reanalysis nuance sits unused in a cited turn).
2. **Duplication.** `missing_theme` over-splits; R4 had near-duplicate pairs.
3. **Outlier dissent.** Penni's pro-validation view missed in 5/6 reports despite profiles.
4. **Stronger critic.** Research question 4: does Opus 5 as critic change outcomes, or is the gap structural?
5. **The loop never passes.** Is `max_iterations` with 2–3 outstanding objections a ceiling or a feature?

## Changes to test (each as its own rule or step, config-switchable)
- `second_finding`: a critic rule that, for each cited turn, asks whether the turn contains a distinct finding no insight uses; reports with insight_id "*".
- `dedupe`: a deterministic-plus-model pass after revise that flags insight pairs above a similarity threshold and asks the reviser to merge or differentiate.
- `dissent_at_intake`: intake produces, per participant, "positions this person holds that most others don't"; the critic gets that list for `missing_counterexample`.
- Critic model swap: Sonnet 5 vs Opus 5, same rules.
- Iteration cap 3 vs 5, with `no_progress` retained.

## Design
- Same five transcripts, same ground truth, same rubric. Conditions: v2 (control), v2+second_finding, v2+dedupe, v2+dissent, v2 all three, v2 with Opus critic, v2 with cap 5. Three runs each is 21 runs — too many; use 2 runs each and accept wider variance, or prioritise: control, all-three, Opus critic, cap 5 at 3 runs each (12 runs).
- Blind pack; scoring method stated.
- Report per docs/evalN-results.md template.

## Success criteria
- T-11/T-15 found in ≥2 of 3 "all-three" runs without coverage or precision loss.
- Duplicate pairs eliminated.
- P-03 passes in ≥2 of 3.
- A clear statement on Opus and on the iteration cap.

## Deliverables
- `docs/eval3-results.md`, updated README table, notes for the case study (a part-1 addendum or a part-2 section).
