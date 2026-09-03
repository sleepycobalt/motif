# Case study notes

Running list of moments, decisions, and findings to draw on when writing the case study.

- 2026-09-02 — Codebook promised in the dataset readme was never deposited; built ground truth from the researchers' final report plus my own manual synthesis instead. R&D has gaps; show how one was handled.
- 2026-09-02 — Setup friction (git identity, pasted commands, curly quotes, pager) — first data point on what "adoptable by a design team" actually costs. I am the first user.
- 2026-09-03 — Manual synthesis: 2h50 for 5 transcripts; 9 of 11 insights matched the researchers' full-corpus findings. Baseline and validation in one.
- 2026-09-03 — Filenames lost their "Dataset-2_" prefix between download and repo; script had to be made forgiving. Product requirement discovered by hitting it.
- 2026-09-03 — Turn ID as the unit of citation: makes "unsupported insight" a mechanical check, not a judgement.
- 2026-09-03 — Loop stop conditions: critic pass, no progress, max iterations. "No progress" is the interesting one — without it the loop burns iterations on failures it can't fix.
- 2026-09-03 — Critic rules split into deterministic (code) and model-judged. Anything checkable mechanically should be: free, instant, can't hallucinate.
- 2026-09-03 — Architecture: core/ (reusable) vs synth/ (tool). Framework-plus-tools is the story, and the ETOT product.
- 2026-09-03 — First real run: critic spent its entire 8K output budget thinking, returned no verdict, and the fallback treated "no failures" as a pass. The loop approved a synthesis nobody had checked. Fix: critic silence is a hard fail, retry once, budget raised to 32K. Lesson: a checker's absence must never read as approval.
- 2026-09-03 — Run one's I-02 cited the interviewer's summary of Penni's barriers as evidence of Penni's view. Added a deterministic rule: evidence must be the participant's own turns. A rule discovered from an output, not designed in advance.
- 2026-09-03 — Raising the critic's budget hit an SDK guardrail: requests that could exceed 10 minutes must stream. Fixed in one place (core/llm.py) because every agent goes through the same client — the architecture paid for itself on day two.
- 2026-09-03 — Run three: loop converged 9 → 4 → 2 failures over three rounds; both survivors were real mis-citations. Confidence and structure errors fix in one round; citation accuracy does not — the reviser swaps a wrong turn for another wrong turn. Fixing by substitution without verification.
- 2026-09-03 — Design response: citations with receipts. Evidence = turn ID + verbatim excerpt; a deterministic check confirms the excerpt exists in the turn. Makes the dominant failure partly mechanical.
- 2026-09-03 — Logger bug: check and revise for the same iteration overwrote each other. Every call was still saved separately, which is why nothing was lost. Redundant logging earned its keep.
- 2026-09-03 — Receipts implemented as rule quote_mismatch. The first thing to watch in run four: does the synthesis agent's own accuracy improve just because it knows the check exists? If deterministic failures drop to near zero on round one, the receipt is doing its work before the critic runs.
- 2026-09-03 — Run four: receipts took deterministic failures on round one from 3 to 0, at the cost of ~3× synthesis output tokens. Critic caught a quote lifted from a turn whose overall meaning contradicts the claim. Receipts stop fabrication; only a reader stops selective quotation. Each layer has a job.
- 2026-09-03 — "Overconfident" was whack-a-mole because confidence was never defined. Now numeric in config (high = 4+ sources, no counter-evidence). The critic and the synthesiser were arguing over a threshold neither could see.
- 2026-09-03 — Four runs, zero critic passes. Decision: show the unresolved objections on the affected insights rather than hide them. A synthesis that admits where its reviewer disagreed is worth more than one that pretends consensus.
- 2026-09-03 — Tool frozen as v1-eval. Stop tuning; measure.
- 2026-09-03 — First eval matrix: two of nine runs invalid. Synthesis hit the 32K output cap twice (receipts + thinking), returned truncated JSON, zero insights — and in C-eval1 the critic passed the empty list in five seconds. The loop approved nothing. Same bug class as run one, one layer up: silence must never read as approval, at every layer.
- 2026-09-03 — C-eval3 deterministic failures never converged (11 → 5 → 6). Every persistent one was "source listed without cited turns": the model counted counter-evidence participants as sources, my rule didn't. Three rounds arguing about a definition. Fix: compute sources in code and stop asking. A rule the fixer can't satisfy is a bug in the rule; anything you can compute, don't ask the model for.
- 2026-09-03 — Model-judged catches in the same run were exactly right: a finding titled "agency-based researchers" citing an academic; "never encountered guidance" overstating what was said. The critic earns its cost on overreach.
- 2026-09-03 — Re-tagged v1.1-eval. A and B2/B3 stand (unaffected by the changes); B1 and all three C runs re-run under v1.1.
- 2026-09-03 — Eval 1 scored blind, 9 reports. The loop halved unsupported citations, zeroed confidence miscalibration, cut trap failures 2.3 → 1.3 — and dropped theme coverage from 75% to 57%. Reuse absent in every C run, present in 5 of 6 others. The critic checks what's on the page; the reviser's cheapest fix is deletion; nothing watches for what went missing. Precision bought with recall.
- 2026-09-03 — Intake alone (B) changed nothing measurable over single-prompt. The map isn't the value; the checking is.
- 2026-09-03 — v2 named by the data: a recall check from the intake topic maps, and "fix or downgrade, never delete" in the revise prompt.
- 2026-09-03 — Case study framing: a null result on coverage is the most credible thing in this project. It shows the eval could have said no.
