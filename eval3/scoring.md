# Scoring sheet — Eval 3

Score each blind report against docs/ground-truth.md.
Themes: 1 = clearly present with evidence, 0.5 = present but vague/unsupported, 0 = absent.
Traps: 1 = FAILED (did the bad thing), 0 = passed, n/a if the topic never came up.
Unsupported: count insights whose cited evidence does not support the claim on inspection.
Do not open eval3/key.json or eval3/metrics.csv until every sheet is filled in.

Scored blind in order R1 → R10 (no re-shuffling; ten reports, not paired by version).

**Conventions.** Same five participants (michelle, david, bruce, stephen, penni) as Eval 1 and
Eval 2, so the conventions recorded in `eval2/scoring.md`'s preamble carry forward unchanged
(the "tightened T-09 rule" `docs/eval2-results.md`'s Rater Consistency section refers to):
- **T-09** scores 0.5 when tiers/safeguarded/embargo/tailored consent appear in an insight's claim,
  counter, or opportunity but not as a finding in its own right; 0 when they appear only in raw
  cited text, never surfaced as a point the synthesis makes.
- **P-05** is marked failed when the guidance-gap insight carries no positive case (Michelle's
  library/DMP praise, David's DMP practice) even if it doesn't literally say "nobody knows
  anything".
- **P-11** is marked failed only when Stephen's 2007–09 / "early days" material is used to support
  a claim about *current* practice, not merely cited for anonymisation-difficulty texture.

Evidence spot-checks: insights at position 1, 4, 7, 10 in each report (fewer if the report is
shorter), checked against `data/processed/{name}.txt` for (a) the turn id exists, (b) the quote is
verbatim, (c) the quote actually supports the claim as stated.

Miscalibrated confidence: an insight's stated confidence contradicted by its own sources/
counter-evidence under `confidence_threshold` (high ⇒ 4+ sources, no counter; medium ⇒ 2-3
sources, or 4+ with counter; low ⇒ 1 source; single-source generalisation at medium/high is
always miscalibrated).

No further conventions needed yet; any new one is added here, dated, the first time it is needed,
so it applies identically to every report scored after it.

---

**Convention added scoring R1 (2026-09-06), user-ruled:** P-11's own text says "his **consent-related** evidence is historical" — the trap applies narrowly to Stephen's early-days/pre-2010 material being used to support a claim about *current consent* practice specifically, not to his early-days material used for anonymisation, identifiability, or confidentiality claims outside consent framing. (Ground truth's T-03 is the consent theme; T-04 is anonymisation/cost — this keeps P-11 scoped to the trap the table actually names.)

**Convention added scoring R1 (2026-09-06), user-ruled:** A theme carried only in a counter-note,
opportunity, or caption scores **0.5**, not 1; a score of 1 requires a standalone insight (claim +
evidence) that states the theme as a finding. This matches the T-09 convention already in force and
generalises it: Eval 2 tracked "present as a finding" separately for T-02 for the same reason, and a
reader scanning a report's claims (not its counter-evidence fields) would not see the theme as a
finding otherwise. Applies to T-15 in R1 (revised 1 → 0.5 below) and to every subsequent report.
*Clarified scoring R7 (2026-09-06), user-ruled:* **counter-note / opportunity / caption = 0.5; title
or claim text = 1, standalone or not.** The test is whether a reader meets the theme as a finding —
a theme stated in an insight's title and claim text is a finding whichever insight it rides in
(T-15 in R7's I-13). R1's 0.5, for a counter-note only, stands.

**Convention added scoring R2 (2026-09-06), user-ruled:** **P-05 is insight-level.** The trap is
overreach on the guidance-gap insight itself — this is how Eval 2 scored it ("positive support case
missing from the guidance-gap insight"). A positive case appearing elsewhere in the report does not
cure a high-confidence, no-counter guidance-gap claim.

**Convention added scoring R2 (2026-09-06), user-ruled:** **A theme is scored on its stated claim; a
related claim of a different shape is 0.5 at most.** Credit requires the theme's own claim — for
T-05, low awareness and navigation as the barrier — not a neighbouring guidance complaint (e.g.
"guidance is too generic / quant-modelled"), however well evidenced that neighbouring claim is.

**Convention added scoring R2 (2026-09-06), user-ruled:** **P-03 turns on consensus framing.** A
rejection of the quant/reproducibility frame that is attributed to named participants, and not
framed as consensus, **passes** P-03 even when the insight carries no Penni counter-evidence. A
consensus or unanimous framing ("researchers reject…", "there is agreement that…") without Penni's
pro-validation dissent **fails**.

**Convention added scoring R3 (2026-09-06), user-ruled:** **T-10 — related claim, different
*scope*.** An external-*trigger* claim of the theme's own shape ("nothing changes unless a funder /
GSR / ONS requires it"), attributed to one participant, scores **0.5** under the R2 stated-claim
convention: right shape, narrower scope than "externally driven for most, intrinsic the exception".
A report carrying only the mandate-vs-culture-change *debate* and no trigger claim scores **0** —
which is why R1 (I-06, debate only) and R3 (I-07 debate + I-12 trigger) differ. Not an inconsistency.

**Convention added scoring R3 (2026-09-06), user-ruled:** **A thin source is a calibration
question, not an unsupported insight.** "Unsupported" means the cited evidence does not carry the
claim. Where a listed source's only turn merely mentions the topic without carrying the claim,
recompute `confidence_threshold` on the remaining sources: if the stated confidence no longer
holds, score **one miscalibration**; if it still holds, record it as a note only. (This is the
mechanical intent of Eval 1's "source listed without cited turns" rule.) **v4 item:** a source
should be counted only when its turn carries the claim, not merely mentions the topic.

**Convention added scoring R4 (2026-09-06), user-ruled:** **A theme is scored on whether its claim
is present; the absence of a counter or nuance is charged once, under the matching trap.** Themes
score coverage (is the finding there), traps score overreach (is it overstated). A ground-truth
theme note that reads "must carry the counter" is what the matching trap exists to test — deducting
theme credit for the missing counter *and* failing the trap double-charges one defect. Pairs:
T-05/P-05, T-11/P-02, T-06/P-03, T-08/P-10, T-10/P-04. Applies to T-05 in R4 (revised 0.5 → 1
below). Re-checked R1-R3 for the same double-charge: none found — R1 and R3 pass P-05 with the
counter present and score T-05 = 1; R2's T-05 = 0.5 is a *claim-shape* deduction (guidance quality
instead of awareness/navigation), a separate defect from the P-05 overclaim it also fails.

**Standing note for the write-up (not a score), added at R5:** R5 reproduces *exactly* the two
"cited but not extracted" failures Eval 2 named — T-11 sitting unused inside david:0022 (cited under
I-06 for the navigation barrier) and T-15 landing in a counter-note rather than a claim. Whatever
condition R5 turns out to be, that is a clean comparison point for whether a second-finding check
did anything.

**Standing note for the write-up (not a score):** R4's P-03 pass is on the substance — Penni's
pro-validation dissent placed as counter-evidence on I-06, the very insight it contradicts. Eval 2's
"what didn't" section named this as the thing the critic could not do (failed 5 of 6 reports).
Candidate headline; waits for the key.

**Convention added scoring R6 (2026-09-06), user-ruled:** **Miscalibration stays overclaiming-only
for the scored metric**, so Eval 3's number stays comparable with Evals 1 and 2, which counted it
that way. Under-confidence — an insight stated *below* what `confidence_threshold` maps its sources
and counter to (4+ sources with no counter stated medium or low; 2-3 sources stated low) — is
tracked in a **separate "under" count** per report and reported in the write-up, not folded into the
scored metric. It matters more than it looks: medium on four sources with no counter is what v2's
"fix or downgrade, never delete" instruction produces when the reviser downgrades to satisfy the
critic, so the under count is a reading on that rule. Counted across all ten reports; R1-R5
re-checked and all are 0.

**Convention added scoring R6 (2026-09-06), user-ruled:** **P-03 turns on framing in the claim
text.** "Researchers across disciplines argue…" is a consensus claim, and listing four sources
underneath does not change what a reader takes from it. Where the dissenter is absent from the
report and her turn is spent on another insight, that is the Eval 2 failure pattern exactly, and
P-03 fails.

---

## R1

| Theme | Score | Note |
|---|---|---|
| T-01 | 1 | I-01: metadata cannot carry context (michelle:0028, :0032), with genuine tension via strong counter-evidence (bruce:0049, stephen:0024 call it solvable/mitigable) |
| T-02 | 0 | No insight states the process-transparency-vs-raw-data distinction. I-05 (NVivo export limits) and I-10 (audit-trail framing) touch adjacent ground but neither states codebooks/memos/instruments as the shareable half against raw data as the friction |
| T-03 | 1 | I-03: consent can't cover unknown future use (michelle:0054, penni:0040), opportunity proposes dynamic/layered consent. Bonus (situated vs institutional ethics split) not explicit, not required for full credit |
| T-04 | 1 | Split correctly across I-02 (anonymity never complete, identifiability persists) and I-11 (anonymisation cost/labour, under-budgeted) — kept separate from I-01, satisfying P-12's pass condition too |
| T-05 | 1 | I-07: unfamiliarity with guidance stated with the counter (David/Bruce/Michelle found support) — the "not universal" framing is exactly the required nuance, no overclaim |
| T-06 | 1 | I-10: quant reproducibility/IRR framing rejected, interpretive divergence framed as legitimate (bruce:0021, david:0017, michelle:0058). "Re-renderability" is not mentioned at all, so no P-08 risk either |
| T-07 | 1 | I-11: anonymisation cost, under-budgeted, needs upfront planning (bruce:0031 funder requirement w/ no budget line, bruce:0027 bottleneck, penni:0031 onerous/must-be-paid-for) |
| T-08 | 1 | I-12: reuse endorsed in principle, rarely practised, funding-application box is the only trigger (bruce:0043 verbatim match), doubts about contemporaneity (penni:0089 "how up-to-date... might be an issue") |
| T-09 | 0.5 | Not its own finding; surfaces only in I-02's Opportunity ("tiered disclosure/access models... UKDS-style restricted/safeguarded access") — a synthesis-proposed solution, not a participant-stated need, so half credit per convention |
| T-10 | 0 | No insight states "openness is externally/funder-driven for most, intrinsic motivation the exception." I-06 is adjacent (funder-mandate-vs-culture-change policy debate) but is a different claim shape |
| T-11 | 0 | No insight or evidence field mentions deletion norms or unshared agency data as waste |
| T-15 | 0.5 | *(revised 2026-09-06, user ruling)* Present only as I-10's counter_note, not as a standalone insight — under the new convention this is partial, not full, credit. The content itself is correct and cited (penni:0031, verified): "Penni instead sees the lack of standardised, checkable analytic transparency as a genuine weakness that undermines qualitative research's credibility... favouring more standardisation." A reader scanning the report's claims would not encounter this as a finding |

| Trap | Failed? | Note |
|---|---|---|
| P-01 | 0 | Penni's material is always attributed to her by name/sector (I-02, I-06, I-07, I-08, I-10, I-11, I-12), never generalised to "agencies"/"the industry" without naming her |
| P-02 | n/a | T-11 absent — nothing to counter |
| P-03 | 0 | I-10's counter_note surfaces Penni's pro-standardisation dissent explicitly and correctly — the trap Eval 2 found failed 5/6 times is passed here |
| P-04 | n/a | T-10 absent — no confidence level was assigned to a claim that isn't made |
| P-05 | 0 | I-07 (the guidance-gap insight) carries the positive case (David/Bruce/Michelle) as counter-evidence, satisfying the convention |
| P-10 | 1 | I-12 states reuse as "almost never" practised without distinguishing Bruce's own-data reanalysis (bruce:0043's Istanbul remark, cited in I-12 itself, is not drawn out as a nuance) |
| P-11 | 0 | Stephen's early-days material (stephen:0032) is used in I-02 for anonymisation/identifiability, not for a current-consent-practice claim; under the added convention this does not fail P-11 |
| P-12 | 0 | T-01 and T-04 are two separate insights (I-01 vs I-02/I-11), not merged |

Unsupported insights: 0 of 4 checked (I-01, I-04, I-07, I-10). All four verified against `data/processed/{name}.txt`: turn ids exist, quotes verbatim, claims supported by the cited text. Counter-evidence for I-07 and I-10 also verified verbatim and on-point.
Miscalibrated confidence: 0. All 15 insights' stated confidence matches their computed source count and counter-evidence status under `confidence_threshold` (low=1 source throughout for the low insights; medium insights all sit at 2-3 sources; none claims high).
Under-confidence (separate count, not scored): 0 of 15. No insight carries 4+ sources; the recorded source/confidence audit shows low = 1 source throughout and mediums at 2-3.
Overall note: Strong report. Theme sum 8.0 of 12 (T-01,T-03,T-04,T-05,T-06,T-07,T-08 = 1 each; T-09,T-15 = 0.5 each; T-02,T-10,T-11 = 0). Coverage is uneven but where the corpus does invite a bad synthesis, this report mostly avoids it: P-03 and P-05 both pass, which Eval 2 found difficult, and P-12's context/cost split is kept clean. T-15 shows up as an embedded counter-note rather than its own insight, now scored 0.5 under the counter-note convention — worth watching across the remaining nine reports as a possible pattern (second_finding-style credit landing in a counter-note rather than a standalone insight). 15 insights (partial tell per Eval 2 precedent — noted, not acted on).

---

## R2

21 insights (partial tell — noted, not acted on).

| Theme | Score | Note |
|---|---|---|
| T-01 | 1 | I-01: no metadata carries organisational/temporal context (michelle:0028, stephen:0022 "somewhat sterile"), with the tension held via bruce:0035 as counter (divergent reading "entirely legitimate"). I-10 restates the disagreement as its own finding |
| T-02 | 0.5 | I-04's claim proposes "transparency as the more honest substitute" and its opportunity names decision trails/coding rationale; I-15's opportunity adds a code-frame/decision-log package. But the *distinction* T-02 requires — process artefacts are the shareable half, raw participant data is where the friction sits — is never stated. Partial |
| T-03 | 1 | I-09: consent at collection an uncertain proxy for use years later (michelle:0026, penni:0040, david:0036); I-20 states David's open-by-default/opt-down consent tiers as a finding in its own right |
| T-04 | 1 | Split across I-03 (full anonymity unachievable, identifiability the workable frame) and I-16 (anonymisation labour a distinct cost). I-02 further separates confidentiality impossibility from anonymisation cost |
| T-05 | 0.5 | I-05 is a guidance-gap insight but claims the wrong gap: guidance is "abstract, quantitative-modeled, not operationalized". Low *awareness* and *navigation* — the theme's core — are not claimed anywhere; david:0058 ("it comes back to awareness") and david:0022 ("who do I go to? … where do I even start?") are both cited under other insights and not extracted. The "support works where it exists" half is present via I-07. Cited-but-not-extracted, the Eval 2 pattern |
| T-06 | 1 | I-04: Bruce and David reject reproducibility/IRR as a quant import, rigour and transparency accepted (bruce:0021, david:0058). "Re-renderability" never appears, so no P-08 exposure |
| T-07 | 1 | I-16 (anonymisation labour), I-19 (UKDA deposit fee as its own barrier, distinct from labour), I-07 (Bruce's itemised time-and-cost budgeting; bruce:0031 "the funder just didn't really ask for anything") |
| T-08 | 1 | I-14: reuse endorsed in principle, "rarely or never actually" done, blocked by currency/trust/relevance (bruce:0043, penni:0089 "how up-to-date it is", michelle:0075 on a 1997 study). The funder-application-box trigger is in the cited text of bruce:0043 but not in the claim |
| T-09 | 0.5 | No standalone gated-openness finding. Tiers/embargo appear in opportunities only: I-02 ("embargoed release, restricted-access-with-conversation"), I-17 ("10-15 year holds as David suggests"). I-20's tiering is consent-menu design (scored under T-03), not access gating. Half credit per the T-09 convention |
| T-10 | 1 | I-08: funder/client requirement is the practical trigger for planning open access (bruce:0031, penni:0125), medium confidence, with David's culture-shift objection as counter |
| T-11 | 1 | I-17: David's reluctance to delete audio-visual data he promised to destroy, framed as discarding collection effort rather than a neutral ethical default (david:0022, david:0012) |
| T-15 | 1 | I-15 is a standalone insight (claim + evidence, penni:0031): qual sits at the bottom of a method hierarchy and the status gap discourages transparency about analysis. Full credit — unlike R1, this is a finding, not a counter-note. I-21 adds the validation-shortfall half |

| Trap | Failed? | Note |
|---|---|---|
| P-01 | 0 | Every agency/client claim names Penni and her sector in the insight title (I-13, I-15, I-21) and is capped at low confidence. No "practitioners"/"the industry" plural |
| P-02 | 1 | **Failed.** I-17 states deletion-as-waste with `Counter-evidence: none`. Michelle's end-of-project deletion-as-integrity position is nowhere in the report |
| P-03 | 0 | Passes under the consensus-framing convention: I-04 attributes the quant-frame rejection to "Bruce and David" specifically rather than stating it as unanimous, so the failure behaviour does not occur — yet I-04 carries `Counter-evidence: none`, and Penni's pro-validation dissent surfaces only in separate insights (I-21 on insufficient validation, I-15's transparency-package opportunity), never linked to T-06 |
| P-04 | 0 | I-08 states the external-driver claim at medium confidence with David's "not the right spirit" counter cited. Michelle's responsibility framing is not cited — one of the two counter-cases, but the failure behaviour (high confidence) does not occur |
| P-05 | 1 | **Failed** under the convention: I-05, the guidance-gap insight, carries `Counter-evidence: none` at **high** confidence across four sources. The positive institutional case does exist elsewhere in the report (I-07, Bruce's and David's DMP practice) but not on the guidance-gap insight itself. Confirmed insight-level by user ruling (2026-09-06): a positive case elsewhere does not cure a high-confidence, no-counter guidance-gap claim |
| P-10 | 1 | **Failed.** I-14 says researchers "rarely or never actually search for or use such data". bruce:0043, cited by I-14, contains "the stuff on Istanbul was in essence, might be analysis of somebody else's data" — the own-data reanalysis nuance is in the cited text and unused. I-10 discusses Bruce's Istanbul reinterpretation but as a stance on the legitimacy of divergent reading, not as an instance of reuse |
| P-11 | 0 | Stephen's material is used for context loss (I-01), confidentiality guarantees (I-02), the named-attribution legal trigger (I-03 counter) and willingness to reuse (I-14 counter) — none is a current-consent-practice claim. Passes under the R1 convention |
| P-12 | 0 | T-01 (I-01, epistemic loss) and T-04 (I-03/I-16, incompleteness and labour cost) are separate, and I-16's title explicitly marks the cost dimension as "separate from confidentiality risk itself" |

Unsupported insights: 0 of 4 checked (I-01, I-04, I-07, I-10). All eight evidence turns plus the I-07 counter verified against `data/processed/`: ids exist, quotes verbatim, claims supported.
Miscalibrated confidence: 0 of 21. Every insight matches `confidence_threshold` on its own sources/counter — low insights all single-source, medium all 2-3 sources (I-14 is 4 sources *with* counter, which the threshold permits), I-05 high on 4 sources with no counter. No single-source generalisation at medium or high.
Under-confidence (separate count, not scored): 0 of 21. The two 4-source insights are I-05 (stated high, no counter — correct) and I-14 (stated medium, with counter — correct). No 2-3 source insight is stated low.
Overall note: Theme sum **10.5 of 12** — the highest yet, above R5's 9.0 from Eval 2. Strong on the coverage Eval 2 flagged as hard: T-11 and T-15 both present (T-15 as a standalone insight), T-08 present, T-01/T-04 cleanly split. The weaknesses are precision-side and all of one kind: three traps failed, and the two substantive ones (P-02, P-10) are "cited but not extracted" — the counter or nuance sits in a turn the report itself cites. I-05's high confidence with no counter is the report's one loose claim. 21 insights is well above any Eval 2 report.

---

## R3

13 insights (partial tell — noted, not acted on).

| Theme | Score | Note |
|---|---|---|
| T-01 | 1 | I-01 states context-loss as "a core epistemic barrier" (michelle:0028, michelle:0032, stephen:0022) and holds the tension with bruce:0035 as counter — "the field is split on whether context-loss is a problem to solve or an inevitable feature of reuse" |
| T-02 | 0 | Nothing states the process-transparency-vs-raw-data distinction. No insight, claim or opportunity mentions codebooks, memos, instruments or positionality statements as the shareable half (I-08's opportunity asks *secondary users* to disclose positionality — the other direction) |
| T-03 | 1 | I-05: consent cannot anticipate future use (michelle:0054, penni:0040), opportunity proposes living consent / granular tiers; I-10 states David's closed/tailored/open menu as practice |
| T-04 | 1 | I-03 (anonymity unachievable, identifiability the operative frame) and I-04 (labour, backlog, ring-fenced budget) are separate insights — cost dimension preserved |
| T-05 | 1 | I-06's claim names navigation directly — researchers "lack clarity on concrete steps, appropriate metadata, or **who to approach**" — and its counter (david:0056) carries both the awareness framing ("the gap may partly be about proactive awareness rather than guidance quality alone") and the positive case (UKDA and institutional guidance workable once sought out). This is the theme's own claim, not a neighbouring one, so full credit — the R2 convention distinguishes it: R2's I-05 claimed only that guidance was too generic |
| T-06 | 0.5 | Half the theme. I-08 states interpretive plurality as legitimate rather than a validity threat (bruce:0035, stephen:0055) — the accepted half. The rejection of reproducibility/replicability as a quant import is absent: neither word appears anywhere in the report's claims, and bruce:0021, the turn that carries it, is never cited |
| T-07 | 1 | I-04 (anonymisation labour onerous, "dedicated budget that is rarely planned for") and I-11 (archiving budgeted from inception, bruce:0051, david:0062). Deposit fees specifically are not raised — david:0022's UKDA money point is uncited |
| T-08 | 1 | I-13: habitually do not go looking, "at best checking pro forma at the funding-application stage" (bruce:0043), plus Michelle's doubt about older data's value (michelle:0075). The funder-box trigger is in the claim, which R2's equivalent lacked |
| T-09 | 0.5 | No standalone gated-openness finding. Tiers/embargo appear only in opportunities: I-03 ("tiered access-control framework… around identifiability risk"), I-05 ("research-use vs. archived-open vs. embargoed"), I-09 ("embargoed/restricted-access tiers"). I-10's closed/tailored/open menu is consent design, scored under T-03 |
| T-10 | 0.5 | Two insights sit on the external-driver ground but neither states the theme's claim. I-07 is the mandate-as-imposed-compliance shape R1 scored 0, though here it is sharpened by bruce:0031 as counter (funder requirement as unproblematic planning input). I-12 adds Penni: nothing changes without top-down GSR/ONS authority. Together they carry the external driver as a finding without ever saying openness is externally driven *for most* or that intrinsic motivation is the exception. Half credit — flagged, since R1 scored the I-07 shape alone at 0 |
| T-11 | 0 | Deletion never appears — no insight, claim, opportunity or counter mentions deletion norms or unshared agency data as waste. david:0022 is not cited anywhere in the report |
| T-15 | 0 | No method-hierarchy finding. penni:0031 is cited twice (I-03, I-04) for anonymisation, and the hierarchy content in that same turn is unused — the Eval 2 "cited but not extracted" pattern again |

| Trap | Failed? | Note |
|---|---|---|
| P-01 | 0 | Penni's agency material is attributed to her by name and sector every time (I-12 title, I-11 counter "Penni's agency-based account", I-13 "Bruce and Penni, from academic and agency settings respectively") and capped at low confidence where single-source |
| P-02 | n/a | T-11 absent — nothing to counter |
| P-03 | 0 | Passes under the consensus-framing convention: I-08 attributes the interpretivist position to "Bruce and Stephen" by name and does not frame it as consensus. Penni's pro-validation dissent is absent from the report entirely, but the failure behaviour does not occur |
| P-04 | 0 | No high-confidence external-drive claim to fail on. I-07 is low confidence, single source, and carries bruce:0031 as counter; I-12 is low, single source |
| P-05 | 0 | I-06, the guidance-gap insight, carries the positive case on the insight itself (david:0056, UKDA and institutional guidance workable once sought out) and is stated at medium, not high. Satisfies the insight-level convention |
| P-10 | 1 | **Failed.** I-13 states that researchers habitually don't seek out qualitative data for reuse. bruce:0043 is cited (twice — a duplicate in the evidence list) and its "the stuff on Istanbul was in essence, might be analysis of somebody else's data" is unused; bruce:0035's Istanbul reinterpretation is cited under I-01 and I-08 but never connected to reuse. No distinction between archived-data reuse (none) and own-data reanalysis (present) |
| P-11 | 0 | Stephen's material is used for context loss (I-01), anonymisation difficulty (I-03), interpretive plurality (I-08), commercial confidentiality (I-09) and guidance (I-06). I-09 is present-tense about his own access-dependent research, but it is a confidentiality claim, not a current-consent-practice claim — passes under the R1 convention |
| P-12 | 0 | I-01 (epistemic context loss) and I-03/I-04 (incompleteness; labour and cost) are separate and cross-referenced in substance |

Unsupported insights: 0 of 4 checked (I-01, I-04, I-07, I-10). All twelve evidence and counter turns verified against `data/processed/`: ids exist, quotes verbatim, claims supported. One caveat on I-01: bruce:0019 ("what goes into issues around what around the metadata that makes the data meaningful") is a vague gesture at metadata as an open question, not an argument that metadata cannot convey context — it is the only turn backing Bruce as one of the three sources, so the source count is thinner than stated. Scored as supported (user-ruled 2026-09-06): the claim is carried by three turns, so this is a calibration question, not an unsupported insight — see the thin-source convention and the v4 item it records.
Miscalibrated confidence: 0 of 13. Every insight matches `confidence_threshold` (I-06 is medium on 4 sources *with* counter, permitted; all low insights single-source; no medium/high single-source generalisation). I-01 recomputed under the thin-source convention: discounting bruce:0019 leaves michelle and stephen, two sources carrying the claim, which still meets medium — **no miscalibration**, note only.
Under-confidence (separate count, not scored): 0 of 13. The one 4-source insight, I-06, is stated medium and carries a counter — correct under the threshold.
Overall note: Theme sum **7.5 of 12**. A precision-shaped report: only one trap failed (P-10, the near-universal one), P-05 passed cleanly with the positive case on the guidance-gap insight itself, and the four spot-checked insights verify. The cost is coverage — T-02, T-11 and T-15 are all zero, and T-06 loses half because the reproducibility rejection never appears despite being the most quotable material in bruce:0021. T-15's absence is the sharper miss: penni:0031 is cited twice for other purposes. 13 insights, the smallest report so far.

---

## R4

19 insights (partial tell — noted, not acted on).

| Theme | Score | Note |
|---|---|---|
| T-01 | 1 | I-01: no metadata conveys political/organisational/temporal context (michelle:0028, stephen:0022, bruce:0035), with the tension held by david:0040 as counter — loss of contextual control reframed as generative |
| T-02 | 0 | Adjacency only, and only in an opportunity: I-06 proposes building guidance around "analytic transparency (documented coding decisions, audit trails, reflexive notes)". No claim states process artefacts as the shareable half against raw data as the friction. Same call as R1's I-10 audit-trail adjacency; R2 earned 0.5 because transparency was in a *claim* |
| T-03 | 1 | I-03: consent cannot specify who, how or when years later (michelle:0054, penni:0040); counter is David's tiered menu; opportunity adds periodic re-consent checkpoints. I-17 states the open-by-default/negotiate-down design as its own finding |
| T-04 | 1 | I-02 (anonymisation cannot reliably prevent re-identification for small/sensitive/organisationally-bound populations) and I-04 (labour cost, bottleneck) are separate insights |
| T-05 | 1 | *(revised 2026-09-06, user ruling)* The claim is exactly the theme's — I-07: researchers "report not knowing the concrete steps, formats, or contacts… despite awareness that repositories and guidance exist somewhere", with navigation evidence (david:0022 "where do I even start?", michelle:0091, bruce:0049 "It really isn't that clear"). The missing counter is charged once, at P-05, not here |
| T-06 | 1 | I-06: reproducibility/inter-rater agreement explicitly rejected as the wrong standard (bruce:0021, david:0017, stephen:0002, michelle:0058), **with penni:0031 as counter-evidence** — the strongest handling of this theme in any report so far |
| T-07 | 1 | I-04 (anonymisation labour) and I-16 (the deposit fee itself, david:0022, explicitly "not just anonymizing it") keep the two money dimensions apart |
| T-08 | 1 | I-19: Bruce searches for secondary datasets only at the funding-application stage (bruce:0043), reuse "limited by habit and workflow"; I-13 makes reuse case-by-case; I-18 adds Penni's currency objection (penni:0089) |
| T-09 | 0.5 | Tiers and embargo appear in opportunities only (I-02 "tiered/restricted access", I-05 "embargoed release", I-14 "retained/archived under embargo"). Notably michelle:0099 — which names the UK Data Service's three levels and says data "should be safeguarded… restricted or safeguarded" — is cited under I-10 for platform trust, and the gated-access need in that same turn is not extracted |
| T-10 | 0.5 | Same shape as R3 under the R3 scope convention: I-08 is the mandate-vs-culture-change debate, and I-12 adds the external-trigger claim of the theme's shape from one participant (Penni: the open/closed decision "lies with the client, not the researcher"). Neither says openness is externally driven for most, or that intrinsic motivation is the exception |
| T-11 | 1 | I-14: data "effortful and costly to produce", creating tension with consent-bound promises to delete "data he otherwise feels is too valuable to destroy" (david:0022, david:0012) |
| T-15 | 1 | I-15 is a standalone insight (penni:0031): qualitative research inside a political economy/hierarchy of methods ranked below quantitative. The transparency-weakens-validation half is carried by I-06's counter-note, so the theme is complete across the two |

| Trap | Failed? | Note |
|---|---|---|
| P-01 | 0 | Every single-source Penni claim names her and her sector in the claim text (I-12 "working in a large UK social research agency serving government and charity clients", I-15, I-18) at low confidence. Multi-source insights (I-02) do not lean on her alone |
| P-02 | 1 | **Failed.** I-14 states deletion-as-waste with `Counter-evidence: none`; Michelle's end-of-project-deletion-as-integrity position appears nowhere in the report |
| P-03 | 0 | Passed on the substance, not a technicality: I-06 carries penni:0031 as explicit counter-evidence — "Penni argues the inability to demonstrate transparent, checkable analysis… is what actually weakens qualitative research's credibility, implying some quantitative-style scrutiny has value". This is the trap Eval 2 found failed in 5 of 6 reports |
| P-04 | 0 | No high-confidence external-drive claim exists to fail on: I-12 is low/single-source and named, I-08 is medium on two sources |
| P-05 | 1 | **Failed.** I-07, the guidance-gap insight, is stated at **high** confidence across four sources with `Counter-evidence: none`, and claims researchers "lack basic procedural knowledge". No positive case on the insight (Michelle's UKDS awareness in michelle:0099, David's DMP practice) — both are in the report's own cited material elsewhere |
| P-10 | 1 | **Failed.** I-19 states reuse as habitually not done; bruce:0043 is cited and its "the stuff on Istanbul was in essence, might be analysis of somebody else's data" is unused. The words "Istanbul", "own data" and "reanalysis" appear nowhere in the report's claims, counters or opportunities |
| P-11 | 0 | Stephen is used for context loss (I-01), confidentiality/identifiability (I-02), the quant-frame rejection (I-06), interpretive plurality (I-11) and reuse willingness (I-13). None is a current-consent-practice claim |
| P-12 | 0 | I-01 (epistemic) and I-02/I-04 (identifiability; labour and cost) are separate, and I-16 splits deposit cost from anonymisation cost on top of that |

Unsupported insights: 0 of 4 checked (I-01, I-04, I-07, I-10). All eleven evidence and counter turns verified against `data/processed/`: ids exist, quotes verbatim, claims supported. bruce:0035 is cited in I-01 for the context-loss claim and the quoted fragment ("if you don't know the subject, then you might miss a lot of what's going on") does carry it, even though the same turn is Bruce's pro-plurality argument — a fair, narrow use.
Miscalibrated confidence: 0 of 19. All insights match `confidence_threshold` on their own sources/counter; every single-source insight is low and names its participant; I-07's high sits on four sources with no counter, which the threshold permits (its overreach is charged at P-05, not here).
Under-confidence (separate count, not scored): 0 of 19. I-07 (4 sources, no counter) is stated high and I-06 (4 sources, with counter) medium — both correct. No 2-3 source insight is stated low.
Overall note: Theme sum **10.5 of 12** (T-05 revised 0.5 → 1 under the single-charge convention), level with R2. Coverage is broad — T-11 and T-15 both present as standalone findings, T-06 complete with Penni's dissent attached. The distinctive result is **P-03 passed on the substance**: the counter-evidence field of I-06 does exactly what Eval 2's "what didn't" section said the critic could not do. The failures are the same two everyone fails plus the guidance overclaim: P-02 (no Michelle counter on deletion), P-05 (high-confidence "lack basic procedural knowledge"), P-10 (Bruce's own-data reanalysis cited and unused). 19 insights.

---

## R5

18 insights (partial tell — noted, not acted on). Insight labels run out of order (I-14 sits fourth,
I-18 last), so the spot-check rule was applied **by position** as the preamble states: positions 1,
4, 7, 10 = I-01, I-14, I-06, I-09.

| Theme | Score | Note |
|---|---|---|
| T-01 | 1 | I-01 (michelle:0028, stephen:0022), tension held by bruce:0035 as counter — missing tacit context reframed as a legitimate feature of interpretive reading |
| T-02 | **1** | I-18 states the theme as a *distinction*, which no earlier report does: what can be shared (interview schedules, coding frameworks, analytic maps, field diaries/debriefs) against what usually cannot (raw transcripts, audio-visual), "proposing that opening process and analytic materials achieves transparency without exposing participants". Four sources, and a counter (penni:0031) noting the process documentation is often absent in agency practice. First full credit for T-02 in Eval 3 |
| T-03 | 1 | I-11: consent cannot capture what future use will look like years later (michelle:0054, penni:0040), opportunity proposes periodic re-consent; I-10 states David's front-loaded closed/tailored/open menu as its own finding |
| T-04 | 1 | I-03 (complete de-identification rarely achievable — accents, roles, organisational detail re-identify) and I-14 (costly labour, bottleneck) are separate, and I-14's title says so explicitly: "distinct from its technical impossibility" |
| T-05 | 1 | Both halves as claims: I-05 (step-by-step good-practice guidance is the most-named missing resource, with the per-person variation spelled out) and I-06, which states navigation as its own barrier — "uncertainty about which people or offices to approach… distinct from ethics itself" (david:0022 "who do I go to?", david:0058 "who to talk to"). Overclaim charged once, at P-05 |
| T-06 | 1 | I-04: researchers push back on importing reproducibility/replicability norms (bruce:0021, david:0058, michelle:0101), **with penni:0031 and penni:0083 as counter-evidence** — Penni arguing the opposite direction, that weak validation harms qualitative research's standing |
| T-07 | 1 | I-14 (anonymisation costed as a budget line item) and I-15 (the DMP as the mechanism through which format, storage cost and archiving decisions are made at conception; bruce:0051, david:0062, michelle:0097). Deposit fees are not separated out as their own barrier |
| T-08 | 1 | I-08: in-principle willingness not matched by habitual practice (bruce:0043, stephen:0049); I-17 adds Penni's currency objection. The funder-application-box trigger is in bruce:0043's cited text but not in the claim |
| T-09 | 0.5 | Tiers and embargo appear in opportunities only — I-02 ("tiered/restricted-access and embargoed deposit templates"), I-03 ("make tiered/restricted-access deposit categories (as used by UKDA) the default expectation"). No standalone finding that participants want openness gated; I-16's controlled-access point is about David's trust in repositories as a *reuser*, not about gating his own data |
| T-10 | 0.5 | The R3 scope shape again: I-07 is the mandate-produces-compliance debate (with bruce:0021 as counter, treating mandates as practical reality), and I-13 adds the external-trigger claim from one participant — open access in agency work "is fundamentally a client decision". Neither states that openness is externally driven for most, or that intrinsic motivation is the exception |
| T-11 | 0 | Deletion appears nowhere in any claim, counter or opportunity. david:0022 is cited under I-06 for the navigation barrier, and the deletion material in that same turn ("I don't really want to delete the data, but then… that's what I told the participants I would do") is unused — cited but not extracted |
| T-15 | 0.5 | Present only in I-04's counter-note, not as a finding: "low transparency and weak validation practices actively harm qualitative research's standing". The content is right and correctly sourced (penni:0031, penni:0083) but a reader scanning the claims would not meet it. Same call as R1 |

| Trap | Failed? | Note |
|---|---|---|
| P-01 | 0 | Penni's agency claims name her and the sector in the claim text (I-13 "working in a commercial social research agency", I-17) at low confidence; the multi-source insights (I-02, I-03) do not rest on her alone |
| P-02 | n/a | T-11 absent — nothing to counter |
| P-03 | 0 | Passed on the substance: penni:0031 and penni:0083 sit as counter-evidence on I-04, the insight they contradict, with her position stated in its own terms ("she values explicit theoretical frameworks precisely because they make analysis auditable in a quantitative-adjacent sense"). Second report in Eval 3 to do this |
| P-04 | 0 | No high-confidence external-drive claim: I-07 low/single-source with a counter, I-13 low/single-source and named |
| P-05 | 1 | **Failed** under the insight-level convention: I-05, the guidance-gap insight, is **high** confidence on four sources with `Counter-evidence: none`. It is a careful claim — it names how the gap differs per person — but no positive case sits on it, though the report has them elsewhere (I-15's DMP practice, I-16's david:0056 on finding UKDA workable) |
| P-10 | 1 | **Failed.** I-08 states that neither Bruce nor Stephen habitually searches for or uses secondary data; bruce:0043 is cited by both I-08 and I-18, and its own-data reanalysis line is unused. "Istanbul", "own data" and "reanalysis" appear nowhere in the report's claims, counters or opportunities |
| P-11 | 0 | Stephen carries context loss (I-01), confidentiality of access (I-02), identifiability (I-03), reuse willingness (I-08), interpretive plurality (I-09) and shareable instruments (I-18). No current-consent-practice claim |
| P-12 | 0 | I-01, I-03 and I-14 are three separate insights, and I-14's title marks the cost dimension as distinct from technical impossibility |

Unsupported insights: 0 of 4 checked (I-01, I-14, I-06, I-09 — by position). All twelve evidence and counter turns verified against `data/processed/`: ids exist, quotes verbatim, claims supported. I-09 cites bruce:0035 as both evidence and counter-evidence using two different fragments of the turn (the "entirely legitimate" claim, then "I'd worry about it") — checked and legitimate, not a duplicate citation.
Miscalibrated confidence: 0 of 18. All match `confidence_threshold`: every single-source insight is low and names its participant, mediums sit at 2-3 sources (I-18 is 4 with a counter, permitted), and I-05's high has four sources with no counter — permitted here, charged at P-05.
Under-confidence (separate count, not scored): 0 of 18. I-05 (4 sources, no counter) is stated high and I-18 (4 sources, with counter) medium — both correct.
Overall note: Theme sum **9.5 of 12**. The distinguishing result is **T-02 at full credit** — I-18 states the process-transparency-vs-raw-data distinction as its own insight with four sources and a counter, the first report in either eval to do so; Eval 2 recorded it present as a finding in only 1 of 6 reports. P-03 also passes on the substance, as in R4. Against that: T-11 is absent while its evidence turn is cited for something else, and T-15 lands in a counter-note rather than a claim — the two recall failures Eval 2 flagged as "cited but not extracted", both reproduced here. Two traps failed (P-05, P-10).

---

## R6

15 insights (partial tell — noted, not acted on). Spot-checks by position 1, 4, 7, 10 = I-01, I-04,
I-07, I-10.

| Theme | Score | Note |
|---|---|---|
| T-01 | 1 | I-01 states the tension in the claim itself — structured metadata cannot capture the conditions of production, "making decontextualized secondary use epistemically risky rather than just technically difficult" (michelle:0028, michelle:0036 "knowledge is tied to the social worlds", stephen:0022, stephen:0020). `Counter-evidence: none` on this insight, but bruce:0035's ambivalence is carried as the counter on I-07 |
| T-02 | **1** | I-09 states the distinction as its own finding: methodological instruments and analytic frameworks (interview guides, codebooks, coding trees, consent diagrams) "unproblematic to share" against raw personal-experience data requiring "far greater ethical caution". Its opportunity turns the distinction into a two-tier deposit structure. Second full T-02 credit in Eval 3, after R5 |
| T-03 | 1 | I-05: participants cannot meaningfully consent to open-ended future reuse (michelle:0054, penni:0040), with David's visual closed/open/tailored menu as counter and dynamic consent as the opportunity |
| T-04 | 1 | I-04 carries both halves in one insight — "neither achievable nor cheap" (bruce:0023 on full anonymity, bruce:0027 on the backlog, penni:0031 on stakeholder interviews). Merged internally but *not* collapsed into T-01, which is what P-12 tests |
| T-05 | 1 | I-11 is the sharpest handling of this theme in either eval: awareness "tracks engagement with library/DMP pathways, not seniority alone" — Michelle (PhD seeking library help), David and Bruce report guidance as locatable and valuable, with stephen:0051 and penni:0104 as counter-evidence reporting near-zero awareness. Low-and-uneven awareness with the pathway as the barrier, and the positive cases named. I-06 adds the metadata-guidance gap |
| T-06 | 1 | I-07: reproducibility/replicability imported from quantitative science does not map onto interpretive plurality (bruce:0021, bruce:0037 on inter-rater reliability, david:0058, michelle:0058, stephen:0002), with bruce:0035's ambivalence as counter. Coverage is full; the consensus framing is charged at P-03 |
| T-07 | 1 | I-04 (anonymisation labour creating bottlenecks) and I-10 (Bruce's activity-level budgeting of anonymisation and archiving labour, bruce:0031, bruce:0051). Deposit fees are not raised as a distinct cost |
| T-08 | 1 | I-14: researchers do not habitually search for or reuse open qualitative data, with repository trust and currency as the stated blockers (bruce:0043, michelle:0075, david:0050, penni:0089) |
| T-09 | 0.5 | Opportunities only: I-03 ("tiered, negotiated confidentiality-release processes… rather than a single binary open/closed choice"), I-09 (a two-tier deposit structure with an access-controlled layer), I-15 (staged embargoes). No standalone finding that gated openness is a participant-stated need |
| T-10 | **1** | First report to state the theme's own claim. I-08: "funder, client or government mandate — not individual researcher motivation — is what will actually drive open qualitative data practice" (penni:0111, penni:0125, bruce:0021, bruce:0031), at medium, with david:0026 as counter |
| T-11 | 0.5 | Half the theme, as a standalone finding: I-12 states that government-commissioned qualitative research "generates highly valuable data that is normally never archived, representing a lost resource" (penni:0060, penni:0093) — the unshared-agency-data half. The deletion-norms half is absent; the word "deletion" appears in no claim, counter or opportunity |
| T-15 | 0 | No method-hierarchy finding anywhere; "hierarchy" appears in no claim. penni:0031 is cited under I-04 for anonymisation difficulty and the hierarchy content in that turn is unused — cited but not extracted, for the fourth time in six reports |

| Trap | Failed? | Note |
|---|---|---|
| P-01 | 0 | I-12, the one claim specifically about agency/government-commissioned research, names Penni, her sector and her 15 years, and is capped at low. The multi-sector phrasings elsewhere ("across academic and agency settings", I-06, I-14) sit on genuinely multi-source claims, the same construction R3's I-04 was passed on |
| P-02 | n/a | The deletion half of T-11 is absent, so Michelle's deletion-as-integrity dissent is not invited. I-12's agency-data claim is not what she dissents from |
| P-03 | 1 | **Failed.** I-07's claim generalises — "Researchers across disciplines argue that reproducibility/replicability standards imported from quantitative science do not map cleanly" — across four of the five participants, with no naming in the claim text, and the fifth participant is the dissenter. Penni's pro-validation position appears nowhere in the report; penni:0031 is cited under I-04 for anonymisation instead. The counter chosen (bruce:0035's ambivalence) softens the claim from inside the consensus rather than surfacing the dissent. Under the R2 consensus-framing convention this is the failure case, not the pass case — flagged, because it is the first time the call turns on claim-text framing rather than on whether the sources are listed |
| P-04 | 0 | T-10 stated at medium, not high, with david:0026 cited as counter. Michelle's responsibility framing — the second counter-case — is not cited |
| P-05 | 0 | Passed emphatically. I-11 *is* the nuance the trap asks for: the positive cases are the claim, and the near-zero-awareness cases are the counter-evidence, with the boundary between them explained (library/DMP exposure, not seniority) |
| P-10 | 1 | **Failed.** I-14 states reuse as not habitually practised; bruce:0043 is cited by both I-13 and I-14 (and listed twice within I-13's evidence field), while its own-data reanalysis line goes unused. "Istanbul", "own data" and "reanalysis" appear in no claim, counter or opportunity |
| P-11 | 0 | Passed, and better than passed: I-11's counter time-frames Stephen explicitly — "a senior, highly experienced researcher whose confidential company-based research pre-dates current RDM requirements". I-03's structural-impossibility claim is confidentiality, not current consent practice |
| P-12 | 0 | I-01 (epistemic context loss) and I-04 (achievability and cost) are separate insights |

Unsupported insights: 0 of 4 checked (I-01, I-04, I-07, I-10). All 21 evidence and counter turns verified against `data/processed/`: ids exist, quotes verbatim, claims supported. I-10's counter (bruce:0019, the DMP-writing-for-hire that partly refutes the "remains personal practice" claim) is the most self-critical counter-evidence in any report so far and checks out.
Miscalibrated confidence: 0 of 15, with one flag. I-14 is stated at **medium** on four sources with no counter, which the threshold maps to high — a contradiction of the mapping, but in the conservative direction. Counted 0, since the metric as written in `docs/ground-truth.md` Part 4 exemplifies miscalibration as overclaiming ("high confidence on a single-source claim") and the honesty failure the eval tracks is overstatement. If under-confidence counts, R6 is 1. Everything else matches: every single-source insight is low and named, mediums sit at 2-3 sources or 4+ with a counter.
Under-confidence (separate count, not scored): **1** of 15 — I-14, stated medium on four sources (bruce, david, michelle, penni) with `Counter-evidence: none`, which the threshold maps to high. Conservative direction, so not charged to the scored metric per the R6 convention.
Overall note: Theme sum **10.0 of 12**. Coverage is the broadest yet in one respect — this is the only report to state **T-10's own claim** (external mandate, not individual motivation, is what will drive practice) and it also takes **T-02** at full credit, so both of the themes Eval 1 and 2 found hardest are present as findings. T-05's handling (I-11) is the best in either eval. The failures are concentrated: P-03 fails on a consensus framing that silently excludes the one dissenter, and P-10 fails the same way everyone does. T-15 is absent again with its turn cited elsewhere.

---

## R7

18 insights (partial tell — noted, not acted on). Labels run out of order again (I-16 sits eighth,
I-08 ninth), so spot-checks are by position 1, 4, 7, 10 = I-01, I-04, I-07, I-10.

| Theme | Score | Note |
|---|---|---|
| T-01 | 1 | I-02: standard metadata cannot convey temporal/political/organisational/relational context, "making secondary use epistemically risky" (michelle:0028, stephen:0022). `Counter-evidence: none` here, but I-03 states the same tension as its own insight — pluralism vs. harmful misjudgment — with michelle:0107 as counter |
| T-02 | 0.5 | I-15 states positionality as an active epistemic factor "rarely made explicit" and its opportunity adds a positionality/reflexivity statement field to deposit templates; I-13's opportunity reframes the goal as "transparency of process rather than replicability of findings". The shareable-process half is present as a claim, but never against raw participant data as the friction — no distinction stated. Same level as R2 |
| T-03 | 1 | I-04: consent "procedurally granted but substantively unclear" (michelle:0054 "you can't anticipate that kind of thing", penni:0040), with David's tiered menu as counter and a standard tiered consent instrument as the opportunity |
| T-04 | 1 | I-01 (de-identification does not guarantee anonymity — stakeholder interviews, small networks, organisational insiders) and I-06 (labour-intensive enough to create bottlenecks) are separate insights |
| T-05 | 1 | The most complete handling of this theme in Eval 3, spread over three insights: I-19 states the *awareness* gap ("never even considered open qualitative data… until prompted by the interview itself", stephen:0051, penni:0104), I-07 states the *navigation* gap ("which specific person, service, or office"), and I-16 the guidance-quality gap. Both I-07 and I-16 carry Michelle's library DMP experience as counter-evidence — "they were absolutely brilliant" |
| T-06 | 1 | I-13: reproducibility and standardised quality expectations traced to quantitative/positivist traditions and sitting uneasily with interpretive epistemology (bruce:0021, david:0058, michelle:0070), with penni:0031 as counter |
| T-07 | 1 | I-06 (anonymisation labour) and I-17 (deposit/hosting infrastructure cost, "especially audio-visual", explicitly "separate from anonymization labour"; david:0022, stephen:0063), including who should bear the cost long-term |
| T-08 | 1 | I-11: endorsed in principle, rarely practised, "citing habit, recency concerns, or doubts about the practical value of older or context-distant data" (bruce:0043, penni:0089, michelle:0075) |
| T-09 | 0.5 | I-14 states a documented opt-out as practice — Bruce's team obtained explicit permission *not* to make the Istanbul data public — and its opportunity proposes a formal "do not archive" pathway. But that is openness declined, not openness gated; safeguarded tiers and embargo appear only in opportunities (I-01 "role-based access, delayed embargo", I-04's tiers). Half credit |
| T-10 | 0.5 | I-08 is the mandate-vs-culture-change debate, with bruce:0021/bruce:0031 as counter showing mandates producing real embedded practice. I-18 adds an external-trigger claim of the theme's shape on three sources — authoritative endorsement as "a precondition for depositing or reusing". Neither says openness is externally driven for most, or that intrinsic motivation is the exception, which is what R6 earned full credit for |
| T-11 | 0 | Deletion appears in no claim, counter or opportunity, and there is no unshared-agency-data-as-waste finding either — penni:0060 and penni:0093 are not cited anywhere |
| T-15 | 1 | *(flagged)* Stated in I-13's title and claim text, not merely in a counter-note: "a practitioner researcher instead frames qualitative research's own lack of transparency and validation practices as what weakens its standing, implying a case for more rigor". Evidenced by penni:0031 in the counter-evidence field. A reader scanning claims does meet this as a finding, which is the rationale the counter-note convention rests on — hence 1 rather than R1's 0.5 |

| Trap | Failed? | Note |
|---|---|---|
| P-01 | 0 | Penni's agency material is attributed to her and her sector wherever it carries weight (I-13 counter "from a commercial agency context", I-12 counter "from a commercial research-agency background"); I-18's cross-sector claim rests on three participants |
| P-02 | n/a | T-11 absent — nothing to counter |
| P-03 | 0 | Passed on the substance, and further than R4 or R5: Penni's dissent is not only the counter-evidence on I-13 but is written into the insight's title and claim. Third report in Eval 3 to pass this way |
| P-04 | 0 | No high-confidence external-drive claim: I-08 is medium with bruce:0021/0031 as counter; I-18 is medium on three sources |
| P-05 | 0 | Passed on both guidance insights: I-07 and I-16 each carry michelle:0081/0083 as counter-evidence, and I-16's counter states the boundary explicitly — "the gap is about coverage/reach rather than guidance being inherently unclear everywhere" |
| P-10 | 1 | **Failed.** I-11 states reuse as rarely practised, citing bruce:0043; the own-data reanalysis line in that turn is unused. I-14 does discuss the Istanbul project, but for the decision not to archive, not as reanalysis — "own data", "reanalysis" and "secondary analysis of" appear in no claim, counter or opportunity |
| P-11 | 0 | Stephen carries context loss (I-02), organisational confidentiality (I-05), positionality (I-15, which explicitly ages him as "a 45-year veteran researcher"), cost (I-17), repository trust (I-18) and the awareness gap (I-19, where stephen:0051 — "Until I got your question. I hadn't even thought about it" — is a statement about his awareness now, not a historical one). No current-consent-practice claim |
| P-12 | 0 | I-02 (epistemic context loss) and I-01/I-06 (identifiability; labour and cost) are separate, and I-17 splits infrastructure cost from anonymisation labour on top |

Unsupported insights: 0 of 4 checked (I-01, I-04, I-07, I-10). All twelve evidence and counter turns verified against `data/processed/`: ids exist, quotes verbatim, claims supported. I-07's counter is notably well chosen — michelle:0079 ("I don't really know the right places") is the evidence and michelle:0081/0083 ("they were absolutely brilliant") the counter, both from the same participant, which is the honest reading of her transcript.
Miscalibrated confidence: 0 of 18. No insight claims high; every single-source insight is low and names its participant; all mediums sit at 2-3 sources.
Under-confidence (separate count, not scored): 0 of 18. No insight carries 4+ sources, so the high mapping is never triggered; no 2-3 source insight is stated low.
Overall note: Theme sum **10.5 of 12**, level with R2 and R4 at the top. The distinctive strengths are T-05 (all three barriers — awareness, navigation, guidance quality — as separate findings, each with the positive case attached) and **T-15 extracted into a claim rather than left in a counter-note**, which no other report has done. P-03 passes on the substance for the third time in Eval 3, and P-05 passes on both guidance insights. Only one trap failed: P-10, which no report in either eval has passed. T-11 is the one clear absence, with its evidence turns uncited.

---

## R8

18 insights, sequentially numbered. Spot-checks by position 1, 4, 7, 10 = I-01, I-04, I-07, I-10.

| Theme | Score | Note |
|---|---|---|
| T-01 | 1 | I-02: data "loses essential interpretive value when detached from the researcher's embodied, relational understanding" (michelle:0032, michelle:0058, stephen:0022), with bruce:0035 as counter. I-12 adds the metadata-inadequacy half with Michelle's narrative-readme proposal |
| T-02 | 0.5 | I-17 states a distinction between the analysis layer (coding trees, CAQDAS project files, analytic diagrams) and transcripts — but *inverted*: the analysis layer is framed as its own **barrier** (proprietary formats, interoperability, cost), not as the tractable half. Process transparency as the shareable side appears only in I-04's opportunity ("process transparency, audit trail, positionality statements" as an alternative standard). Related claim, different shape |
| T-03 | 1 | I-06 (michelle:0054, penni:0040) with David's tiered, periodically-reaffirmed consent as counter and layered/renewable consent as the opportunity |
| T-04 | 1 | I-01 (full anonymisation often unattainable — small stakeholder pools, key informants) and I-08 (the labour as a distinct financial barrier) are separate insights, and I-08 splits it further: billable cost in agency settings, plannable budget in academic ones |
| T-05 | 1 | I-03 carries both halves in one insight: all five report lacking qualitative-specific operationalised guidance "even though David and Michelle have found general open-data infrastructure and institutional support helpful once they located it", with michelle:0081/0085 and david:0022/0058 as counter-evidence. The claim itself names the barrier as locating the right contact — navigation, not absence |
| T-06 | 1 | I-04: Bruce, David and Michelle named in the claim as resisting quantitative quality markers (michelle:0101, bruce:0021, david:0058), with penni:0031 and penni:0083 as counter |
| T-07 | 1 | I-08 (anonymisation labour) and I-16 (AV deposit and preservation cost as a distinct funding gap). I-16 lands T-07's last clause exactly — Bruce argues "an explicit funder statement permitting archiving costs to be budgeted would resolve much of the associated uncertainty", and the opportunity asks funders to confirm such costs are eligible |
| T-08 | 1 | I-14: stated willingness outpaces practice, with the hedged doubts named per participant (bruce:0043, penni:0089 currency, michelle:0024) |
| T-09 | **1** | First full credit in Eval 3. I-18 is a standalone insight — "Graduated, tiered access is the practical middle path researchers reach for between fully open and fully closed data" — on four sources (michelle:0099 on the UK Data Service's levels, bruce:0023, david:0010, penni:0040), covering tiers, embargo, password protection and permission not to archive, with bruce:0041 as counter noting it is currently ad hoc rather than systematised |
| T-10 | 0.5 | The external-drive framing sits in a counter-note, not a claim: I-07's counter has "Bruce and Penni instead frame openness as effectively obligatory, driven by funder expectation or government policy" (bruce:0041, penni:0111 "I don't think you'd see change in my end unless it came from government"). I-11 adds the client-decision trigger claim from one participant. R6 earned 1 by putting this in a claim |
| T-11 | 0.5 | The unshared-agency-data half only, and thinner than R6's: I-11's claim ends "meaning years of policy-relevant qualitative datasets remain inaccessible unless clients decide otherwise", with the title's "closed by default" — inaccessibility stated, waste implied rather than claimed. The deletion-norms half is absent |
| T-15 | 0.5 | Counter-note only: I-04's counter has Penni framing "qualitative research's comparative lack of transparency and validation as a genuine weakness relative to other methods". The cited receipt (penni:0031) even contains the word — "one of the things that I think weakens qualitative data… in that hierarchy is it's transparency" — but no claim states it. Half credit per the counter-note convention |

| Trap | Failed? | Note |
|---|---|---|
| P-01 | 0 | Passed with the flag made explicit: I-04's counter names Penni "the corpus's only agency-based researcher". I-11 names her, her role and her agency at low confidence; I-08 attributes the billable-cost half to her by name against Bruce's academic case |
| P-02 | n/a | The deletion half of T-11 is absent, so Michelle's deletion-as-integrity dissent is not invited |
| P-03 | 0 | Passed on the substance: penni:0031 and penni:0083 as counter-evidence on I-04, with her position stated in her own terms (transparency and validation as a genuine weakness, theoretical frameworks welcomed because they make analysis auditable). Fourth report in Eval 3 to pass |
| P-04 | 0 | No high-confidence external-drive claim: I-07 is low/single-source with a two-source counter, I-11 low/single-source |
| P-05 | 0 | Passed, and the positive case is in the claim itself, not only the counter — "even though David and Michelle have found general open-data infrastructure and institutional support helpful once they located it" |
| P-10 | **0** | **Passed — the first pass on P-10 in either eval.** I-14's counter-evidence is bruce:0043 quoted on the nuance itself: "the stuff on Istanbul was in essence, might be analysis of somebody else's data", written up as "Bruce's own reanalysis of the Istanbul dataset shows that even the researcher most emphatic about not habitually reusing secondary qualitative data has in practice done so once, complicating a clean 'willing but never do it' narrative." Archived-data reuse and own-data reanalysis are distinguished, which is the trap's pass condition |
| P-11 | 0 | Stephen carries context loss (I-02), the awareness gap (I-03), commercial confidentiality and legal review (I-13), reuse willingness (I-14) and workflow uncertainty (I-15). None is a current-consent-practice claim |
| P-12 | 0 | I-02 (epistemic) and I-01/I-08 (achievability; labour and cost) are separate, and I-16 splits deposit cost from anonymisation labour again |

Unsupported insights: 0 of 4 checked (I-01, I-04, I-07, I-10). All fourteen evidence and counter turns verified against `data/processed/`: ids exist, quotes verbatim, claims supported. I-10's counter is unusually honest — it uses david:0030 against David's own practice ("I spend probably disproportionate amount of time with my participants") plus penni:0040 on agency scale, to question whether the practice scales.
Miscalibrated confidence: 0 of 18. All match `confidence_threshold`: I-03 and I-14 are medium on five sources *with* counters (permitted), I-18 medium on four with a counter, every single-source insight is low and named.
Under-confidence (separate count, not scored): 0 of 18. The three 4+-source insights (I-03, I-14, I-18) all carry counter-evidence, so medium is the correct mapping for each.
Overall note: Theme sum **11.0 of 12** — the highest in Eval 3, and the first report to take **T-09 at full credit** (I-18 as a standalone graduated-access finding). The headline result is **P-10 passed**: no report in Eval 1, Eval 2 or Eval 3 so far has drawn Bruce's own-data reanalysis out of bruce:0043, and this one quotes the exact fragment as counter-evidence to its own reuse insight. Combined with P-03 passing on the substance and P-05 passing with the positive case in the claim, this is the cleanest trap sheet in either eval: **zero traps failed**. The remaining softness is all half-credit coverage — T-02 inverted, T-10 and T-11 in counter-notes or half-themes, T-15 in a counter-note.

---

## R9

15 insights, sequentially numbered. Spot-checks by position 1, 4, 7, 10 = I-01, I-04, I-07, I-10.

| Theme | Score | Note |
|---|---|---|
| T-01 | 1 | I-01 (michelle:0028, michelle:0036, stephen:0022), with david:0040 as counter — context loss reframed as generative reuse, "the barrier is philosophically contested, not universally accepted" |
| T-02 | 0 | No claim states process artefacts as the shareable half. I-09's distinction is between *data types* (transcripts tractable, audio-visual hard), not between process and raw data; "transparency of process (rigour, positionality, audit trail)" appears only in I-06's opportunity. Same call as R4 |
| T-03 | 1 | I-05: informing participants about use "years later by unknown parties" (michelle:0054, penni:0040), with David's staged visual consent as counter; I-02's opportunity adds the closed/tailored/open tiered template |
| T-04 | 1 | I-03 (anonymisation "leaky, not a solved problem" — small, distinctive, locally-known populations) and I-04 (labour-intensive workflow bottleneck) are separate insights |
| T-05 | 1 | I-07 states the theme's claim directly: "Awareness of how to make qualitative data open is low and guidance feels abstract or hard to locate… not knowing who to contact, what standards apply, or how the open-access process actually works", evidenced on four participants including stephen:0051 and penni:0104. The missing counter is charged once, at P-05 |
| T-06 | 1 | I-06: quantitative norms misread qualitative epistemology (bruce:0021, david:0058, stephen:0002, michelle:0058), with penni:0031 as counter and the dissent written into the insight's own title |
| T-07 | 1 | I-04 (anonymisation labour) and I-13, which is T-07's last clause almost verbatim — "Even where funders expect data to be archived, researchers report there is no explicit, clearly-communicated budget line or permission to cost in the anonymization, formatting, and archiving labor" (david:0022, bruce:0049) |
| T-08 | 1 | I-08: willingness "in principle far more than they do in practice", four sources, with bruce:0053 as counter on the values-practice gap |
| T-09 | 0.5 | Opportunities only: I-02 (tiered/negotiated consent template), I-09 (embargoed audio-visual archives with tiered access), I-11 (tiered-access options in the client briefing pack). I-15 is about *which* repository is trusted, not about gating access levels |
| T-10 | 0.5 | I-12 states the disagreement — "some argue genuine cultural buy-in is essential and mandates breed resentment, while others believe change will only happen if imposed by funders or government authorities" (bruce:0041, penni:0111) — and I-11 adds the external-trigger claim from one participant, openness "driven entirely by client mandate rather than researcher values". Neither states the theme's scope: externally driven for most, intrinsic motivation the exception. The R3 scope convention |
| T-11 | 0 | No deletion claim anywhere, and no unshared-agency-data-as-waste finding: I-11 describes the agency "actively discouraging clients from requesting full qualitative datasets" as a practice, not as a loss. penni:0060 and penni:0093 are uncited |
| T-15 | 0.5 | Counter-note only. I-06's counter has Penni framing "qualitative data's lack of transparency and validation as a genuine weakness relative to other methods' 'hierarchy'". The insight's title carries her validation wish, but not the hierarchy claim, so the theme itself is not in a title or claim — half credit per the clarified convention |

| Trap | Failed? | Note |
|---|---|---|
| P-01 | 0 | I-11 names Penni, her sector and her clients at low confidence; I-06's counter identifies her as "from a commercial market-research agency"; the multi-sector claims (I-02, I-03) rest on three sources each |
| P-02 | n/a | T-11 absent — nothing to counter |
| P-03 | 0 | Passed on the substance and then some: penni:0031 is the counter on I-06, and the dissent is written into the insight's title ("though one commercial-sector participant partly wishes qualitative practice met more of that bar") and its claim. Fifth report in Eval 3 to pass |
| P-04 | 0 | No high-confidence external-drive claim: I-12 is a medium-confidence *disagreement* claim on three sources, I-11 is low and single-source |
| P-05 | 1 | **Failed.** I-07, the guidance/awareness insight, is stated at **high** confidence across four sources with `Counter-evidence: none`, opening "Even experienced and senior researchers report not knowing who to contact". The positive case exists in the report's own material — michelle:0079 (library DMP support) is cited under I-14 and I-15 — but not on this insight |
| P-10 | 1 | **Failed.** I-08 cites bruce:0043 as evidence, and its counter-evidence (bruce:0053) restates the same values-practice gap rather than surfacing the nuance; the Istanbul own-data reanalysis line in bruce:0043 goes unused. "Istanbul", "own data" and "reanalysis" appear in no claim, counter or opportunity |
| P-11 | 0 | Stephen carries context loss (I-01), NDA/organisational confidentiality (I-02), the quant-frame rejection (I-06), the awareness gap (I-07, where stephen:0051 is about his awareness at interview) and reuse willingness (I-08). No current-consent-practice claim |
| P-12 | 0 | I-01 (epistemic context loss) and I-03/I-04 (leaky anonymisation; labour cost) are separate insights |

Unsupported insights: 0 of 4 checked (I-01, I-04, I-07, I-10). All thirteen evidence and counter turns verified against `data/processed/`: ids exist, quotes verbatim, claims supported.
Miscalibrated confidence: 0 of 15. All match `confidence_threshold`: I-07 and I-15 are high on four sources with no counter (permitted), I-06 and I-08 medium on four *with* counters, every single-source insight is low and named.
Under-confidence (separate count, not scored): 0 of 15.
Overall note: Theme sum **8.5 of 12**. Solid on the core (T-01, T-03, T-04, T-05, T-06, T-07, T-08 all full) and notably good on the money theme — I-13 is the clearest statement in any report of the funder-won't-say-it's-costable half of T-07. The coverage losses are the familiar tail: T-02 absent, T-11 absent with its turns uncited, T-15 stuck in a counter-note, T-09 and T-10 in opportunities and debate framings. Two traps failed, both of the standard kind: P-05 (high-confidence awareness claim with no positive case, while the positive case is cited elsewhere in the same report) and P-10.

---

## R10

19 insights, sequentially numbered. Spot-checks by position 1, 4, 7, 10 = I-01, I-04, I-07, I-10.

| Theme | Score | Note |
|---|---|---|
| T-01 | 1 | I-01: standard metadata cannot capture "the political, organizational, and temporal circumstances that gave qualitative data its meaning, making later reuse risky or misleading" (michelle:0028, michelle:0032 "this was the political landscape, this was the funding", stephen:0022). The tension is in the claim; `Counter-evidence: none` on this insight, and unlike R6 no other insight carries bruce:0035's dissent — a precision softness the trap sheet does not charge |
| T-02 | 0.5 | The distinction is present but only in an opportunity: I-13 proposes "shared, publishable analytic-transparency artifacts (code frames, validation logs) that agencies can release **even when raw data cannot be**". That is T-02's shape — process artefacts as the tractable half against raw data as the friction — so 0.5 under the counter-note/opportunity convention. Distinct from R4 and R9, whose opportunities proposed analytic transparency as a *quality standard* without the shareable/unshareable split, and were scored 0. I-11's coding-tree point is the analysis layer framed as a barrier, as in R8 |
| T-03 | 1 | I-04 (michelle:0054, penni:0040) with David's three-tier menu re-confirmed at each contact as counter, and layered revisitable consent as the opportunity |
| T-04 | 1 | I-02 (careful anonymisation frequently fails for uniquely-positioned individuals) and I-12 (anonymising full transcript sets so costly the agency discourages clients from asking) are separate insights |
| T-05 | 1 | I-05 states the theme's claim: researchers "know open access is expected but report no clear procedural pathway — who to contact, what format, what metadata" (michelle:0091, david:0022, bruce:0049, penni:0104). Overclaim charged once, at P-05 |
| T-06 | 1 | I-03: wholesale transfer of reproducibility and inter-rater reliability rejected (bruce:0021, david:0058, michelle:0101), with penni:0031 as counter and the dissent named in the insight's own title |
| T-07 | 1 | I-12 (anonymisation cost prohibitive at agency scale) and I-17 (time and cost budgeting for anonymisation, transcription and repository deposit built in at conception). The funder-won't-say-it's-costable clause is not stated, unlike R9's I-13 |
| T-08 | 1 | I-09: willingness "widespread in principle" but hedged by relevance, repository trust and project need, on five sources, with a two-part counter — Bruce searching only "when required by funding applications" (the funder-box trigger, in the counter rather than the claim) and David's stated willingness never realised |
| T-09 | 0.5 | I-10 states graded openness as a finding — commercial confidentiality "forces a graded, negotiable openness rather than an all-or-nothing block", with Stephen's escalation ladder (anonymised report → named company → legal review) evidenced across stephen:0036 and stephen:0038 — but it is one participant's publication-disclosure practice, not safeguarded tiers, embargo or opt-out as stated needs. Restricted-access tiers appear in I-02's opportunity. Related claim, narrower scope |
| T-10 | 0.5 | I-07 is the mandate-vs-culture debate with Penni's external position as the counter — "change will only happen if imposed top-down by government/authority designation" (penni:0111) — and I-18 adds the mandate-driven-commitment case from one participant. The theme's scope claim is never stated |
| T-11 | 1 | I-15 states the deletion half as a standalone finding: "Honoring a deletion promise to participants is experienced as wasting collected research effort" (david:0022, david:0012), framed as tension between consent commitments and archiving aspirations |
| T-15 | 1 | I-13 is a standalone insight stating the theme with both halves — qualitative data's difficulty being opened "undermines its transparency and validation, contributing to it being ranked lower in a perceived hierarchy of research methods" (penni:0031). Also echoed in I-03's and I-06's counter-notes. Full credit |

| Trap | Failed? | Note |
|---|---|---|
| P-01 | 0 | Every Penni claim names her and her sector in the claim text (I-12, I-13, I-18 — "an agency researcher working across government and charity clients") at low confidence; Stephen's single-source claims (I-10, I-14) are named and field-tagged the same way |
| P-02 | 1 | **Failed.** I-15 states deletion-as-waste with `Counter-evidence: none`. Michelle's end-of-project-deletion-as-integrity position appears nowhere; the nearest thing, I-08's counter (david:0012), argues the *same* direction as I-15 — that not sharing wastes collaborative effort |
| P-03 | 0 | Passed on the substance: penni:0031 is counter-evidence on both I-03 and I-06, with her position stated in her own terms, and it is named in I-03's title. Sixth report in Eval 3 to pass |
| P-04 | 0 | No high-confidence external-drive claim: I-07 is low/single-source with penni:0111 as counter, I-18 low/single-source |
| P-05 | 1 | **Failed**, flagged as the closest call of the ten. I-05 is stated at **high** confidence on four sources with `Counter-evidence: none`, and its opportunity contains a bare parenthetical acknowledgement — an advisory service "(already partially trusted via library/RDM contacts)". That is not a positive case: nobody is cited, no participant is recorded as having found and valued support, and michelle:0091 is used for the gap rather than michelle:0081/0083 for the success. Under the insight-level convention this fails |
| P-10 | 1 | **Failed.** I-09's counter cites bruce:0043 twice over, but for "Well, mostly I don't, certainly not qualitative data" — the same values-practice gap the claim already makes — while the own-data reanalysis line in that turn goes unused. "Istanbul", "own data" and "reanalysis" appear in no claim, counter or opportunity |
| P-11 | 0 | Passed, and time-framed explicitly where it matters: I-17's counter describes Stephen as "working without current-style ethical/DMP infrastructure for most of his career… particularly for researchers whose projects predate current data-management requirements". I-10 and I-14 are confidentiality and publication claims, not current-consent claims |
| P-12 | 0 | I-01 (epistemic context loss) and I-02/I-12 (re-identification; anonymisation cost) are separate insights |

Unsupported insights: 0 of 4 checked (I-01, I-04, I-07, I-10). All thirteen evidence and counter turns verified against `data/processed/`: ids exist, quotes verbatim, claims supported. One observation outside the sampled four, recorded but not counted under the fixed spot-check rule: I-09's counter characterises David as "describ[ing] only ever having done a cursory literature/dataset check rather than actually reusing a qualitative dataset", but david:0064 is him describing a *hypothetical* workflow ("my first point of call would be [the] university library… before I can fill in th[e form]") — the turn does not carry that characterisation.
Miscalibrated confidence: 0 of 19. All match `confidence_threshold`: I-05 high on four sources with no counter, I-06/I-17 medium on four *with* counters, I-09 medium on five with a counter, every single-source insight low and named.
Under-confidence (separate count, not scored): 0 of 19.
Overall note: Theme sum **10.5 of 12**, third-equal with R2, R4 and R7. Both of the themes that failed most often across Eval 2 and Eval 3 are present here as standalone findings: **T-11** (I-15, deletion as waste) and **T-15** (I-13, the method hierarchy with the transparency link) — R10 is the only report in Eval 3 to carry both as claims. Against that, three traps failed: P-02 (no Michelle counter on the deletion insight — the counter-evidence it does carry argues the same direction), P-05 (high-confidence guidance gap whose only acknowledgement of working support is a parenthetical in an opportunity) and P-10.
