# synth-loop

An agentic loop that turns a folder of interview transcripts into a research synthesis where every insight carries cited, verified evidence, an honest confidence level, and the counter-evidence against it.

Built for design and research teams who synthesise qualitative interviews and need output they can trust and trace. Built as an R&D project; the [case study](https://ericfrye.info/ui/ux/synth-loop) tells the story.

## What it does

```
transcripts/  →  intake  →  synthesis  →  critic  →  revise  →  report.md
                                            ↑            │
                                            └────────────┘  until the critic passes or 3 rounds
```

- **Intake** (one call per transcript) maps topics and notable positions with turn references.
- **Synthesis** produces 8–14 insights. Each has a claim, cited turns with verbatim receipts, sources, confidence, counter-evidence, and a design opportunity.
- **Critic** checks every insight against the transcripts using rules you can edit — unsupported claims, missing dissent, overconfidence, merged findings, themes present in the corpus but absent from the report. Some rules run in code (citations exist, quotes match, confidence thresholds); the rest are judged by the model.
- **Revise** fixes what the critic flagged. It may not delete an insight to make an objection go away.
- **Report** shows every insight with its evidence expanded, and marks any insight the critic still objected to when the loop stopped. Silence is never treated as agreement.

Sample output: [docs/exhibits/best-report-v2/output.md](docs/exhibits/best-report-v2/output.md).

## Install (about 5 minutes)

You need Python 3.10+ and an Anthropic API key ([console.anthropic.com](https://console.anthropic.com)).

```bash
git clone https://github.com/sleepycobalt/synth-loop.git
cd synth-loop
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
echo "ANTHROPIC_API_KEY=your-key-here" > .env
```

## Run

Put your transcripts in a folder, one speaker turn per paragraph or line, each starting with the speaker's name and a colon. Label the interviewer `Researcher`, `Interviewer`, or `Moderator` so their turns are never cited as evidence.

```
Interviewer: Can you tell me about the last time you used the app?
Priya: Sure. I opened it on the train and it logged me out again, which...
```

Then:

```bash
synth-loop ./transcripts --out report.md --question "What frustrates users about onboarding?"
```

Fifteen transcripts of ~45 minutes each take about 20 minutes and cost about $2.50 in API usage. Every prompt, response, and iteration is saved under `runs/` so you can see exactly what the critic objected to and how the synthesis changed.

Try the sample corpus first:

```bash
synth-loop data/raw/Dataset-2 --out report.md
```

## Tune it

Everything a team might want to change lives in [`config/synth.yaml`](config/synth.yaml):

- which model plays which role
- how many revision rounds
- what "high confidence" requires (default: 4+ participants and no counter-evidence)
- the critic's rules, in plain language — add, remove, or reword them

## What the evaluation found

Tested on 15 real research interviews (University of Sheffield, CC-BY-NC) against a human-built ground truth of 16 themes and 12 traps, with blind scoring:

| | Single prompt | This loop |
|---|---|---|
| Insights whose cited evidence doesn't support them | 1.7 of 4 checked | 0.7 |
| Insights with overstated confidence | 1.3 | 0.7 |
| Themes found | 75% | 69% |
| Time | 4 min | 22 min |
| Cost | $0.37 | $2.28 |

The loop makes fewer errors and finds slightly less. Its first version found much less (51%) — the critic only checked what was on the page, and the reviser's cheapest fix was deletion. A recall check that compares the report against the intake topic maps recovered most of the gap. Full results: [docs/eval1-results.md](docs/eval1-results.md), [docs/eval2-results.md](docs/eval2-results.md).

Known gaps: the critic still misses some dissent from outlier participants, and when a turn contains two findings the synthesis tends to extract only one.

## Repo layout

```
core/       reusable: loop controller, run logger, LLM client, config loader
synth/      this tool: agents, prompts, corpus loader, report renderer, CLI
config/     synth.yaml — models, thresholds, critic rules
scripts/    ingest.py (transcripts → citable text), eval_pack.py (blind scoring packs)
data/       sample corpus (CC-BY-NC, see LICENSE) and its processed form
docs/       R&D brief, working log, ground truth, eval results, exhibits, case-study notes
eval/       blind scoring packs and completed sheets
```

`core/` is written to be reused by other loops; the synthesis tool is the first built on it.

## Data attribution

Sample transcripts: Hanchard, M. and San Roman Pineda, I. (2023). *Fostering cultures of open qualitative research: Dataset 2 – Interview Transcripts.* University of Sheffield. [doi:10.15131/shef.data.23567223.v2](https://doi.org/10.15131/shef.data.23567223.v2). CC-BY-NC 4.0. Non-commercial use only.

## License

MIT for the code. See [LICENSE](LICENSE).
