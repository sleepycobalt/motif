# R&D Brief — Agentic Research Synthesis Loop

**Project:** motif
**Owner:** Eric Frye
**Started:** 2 Sep 2026
**Status:** Phase 0 — framing

## Problem

Synthesizing qualitative research is slow, lossy, and hard to audit. A designer or researcher with 15 interview transcripts spends days reading, coding, and clustering, and the output — a set of insights and opportunity statements — rarely carries a traceable line back to the evidence. Single-prompt AI summarization is fast but unreliable: it overgeneralizes from thin evidence, invents patterns, and gives no signal about which insights are well supported.

## What I'm building

An agentic loop that turns a folder of interview transcripts into a synthesis report where every insight carries cited evidence and a confidence score. The loop has four roles:

1. **Intake** — chunks and tags transcripts, writes a coverage plan.
2. **Synthesis** — clusters evidence into insights and opportunity statements.
3. **Critic** — checks every insight against the raw transcripts using explicit, configurable rules (unsupported claim, single-source generalization, missing counterexample, vague opportunity).
4. **Controller** — sends critic failures back to synthesis; stops when all insights pass or an iteration cap is reached.

The output is a report a design team could act on, and the tool is one they could run themselves.

## What "agentic" means here

A loop is agentic when the model plans, calls tools, evaluates its own output against criteria, and decides when to stop. This is distinct from a chain (fixed sequence of prompts) and from a node-graph pipeline (human-wired steps, no self-evaluation). The critic and controller are what make this project a loop rather than a chain.

## Research questions

1. Does a critic-driven loop reduce unsupported or overgeneralized insights compared to single-prompt synthesis?
2. What does the loop cost in time and tokens relative to the improvement?
3. What is the right stop condition — critic pass, iteration cap, or diminishing change between iterations?
4. Does a stronger critic model change outcomes enough to justify its cost?

## Hypothesis

The full loop (intake → synthesis → critic → revise) will produce fewer unsupported insights and better coverage of known themes than single-prompt synthesis, at a cost of 3–5× the tokens and wall time. The critic will catch most overgeneralizations within two iterations; a third iteration will show diminishing returns.

## Corpus

*Fostering cultures of open qualitative research*, Hanchard & San Roman Pineda, University of Sheffield, 2023. 15 semi-structured interviews with academic and professional researchers about open qualitative research practice, 38–73 minutes each, ~105,000 words total. CC-BY-NC. Chosen because it is real, ethically cleared, publicly redistributable with attribution, and accompanied by a final report from the original researchers that serves as insight-level ground truth.

Limitation: the codebook referenced in the dataset readme was never deposited. Ground truth is built from the researchers' final report plus a manual synthesis by me, done before reading the report in detail.

## Evaluation

Three conditions, same corpus, three runs each:

- **A** — single-prompt synthesis
- **B** — intake + synthesis, no critic
- **C** — full loop

Scored against a theme checklist (known themes any good synthesis must find) and a trap list (places where the corpus invites overgeneralization). Metrics: theme coverage, unsupported-insight rate, trap failures, iterations to stop, wall time, tokens, cost. A fourth condition swaps the critic to a stronger model if C shows the critic matters.

## Success criteria

- C beats A on unsupported-insight rate and theme coverage, with the difference visible in the numbers, not just my impression.
- The critic rejects real problems — at least one documented rejection that would have shipped in condition A.
- Someone with a Python environment can clone the repo and produce a report from their own transcripts in under 15 minutes.
- Every phase produces artifacts for the case study: brief, log, architecture diagram, iteration traces, eval table, honest findings.

## Out of scope

Figma integration, multi-modal inputs, a hosted UI, and Figma Weave. These belong to a second workflow (design critique loop) planned after this one ships.

## Stack

Python 3.10+, Anthropic API (`anthropic` SDK), YAML config for critic rules, JSON handoffs between roles, structured logs per run. Models: Haiku 4.5 for intake; Sonnet 5 for synthesis and critic; Opus 5 reserved for the strong-critic condition.

## Deliverables

1. Public repo with CLI, config, README, sample corpus and sample output.
2. Case study at ericfrye.info/ui/ux/ — problem, definition of agentic, architecture, one insight traced across iterations, eval results, what didn't work, what's next.
