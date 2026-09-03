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
