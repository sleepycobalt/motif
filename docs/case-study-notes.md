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
