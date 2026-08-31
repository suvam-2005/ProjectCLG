# Phase 4 — Reference Paper → Reproduction Specification

Date: 2026-08-24. Zero OpenRouter calls. No Qwen run, no ChildAgentEval run, no
guardrail algorithm, no WISC-derived material created. Source discipline: only the
arXiv paper (2605.17894, HTML + PDF), the official GitHub repository
(PediaMedAI/ChildAgentEval), and the live OpenRouter API were used as evidence — see
`src/childagenteval_research/evaluation/source_evidence.py` for the full, machine-readable
claim/source/location/confidence/status table backing every fact below.

## 1. Reference paper summary

*Evaluating Cognitive Age Alignment in Interactive AI Agents* (Shen, Zhang, Xu, Kim,
Lourentzou, Cao, Huang; arXiv:2605.17894, cs.AI, May 2026, CC-BY 4.0) introduces
ChildAgentEval, described as the first psychometrically grounded interactive benchmark
for evaluating cognitive-age alignment in MLLM-based agents, inspired by the Wechsler
Intelligence Scale for Children. **CONFIRMED**, high confidence (3 independent fetches).

## 2. Experimental methodology

Agents interact with a Playwright-driven browser environment in "DOM-assisted mode"
(screenshot + sanitized accessibility tree), across 10 subtests, under two conditions
(standard age prompting vs. skill-guided prompting derived from a calibration corpus),
at 4 anchor ages (baseline) or 4 age bands (skill-guided). Objective items score
binary/time-based; open-ended items are scored 0/1/2 by two blind human raters.
**CONFIRMED** (qualitative description), MEDIUM confidence on procedural specifics
(single-pass extraction for several details — see evidence table).

## 3. Models

Proprietary: GPT-5.4, Gemini-3.1-Pro, Gemini-3.1-Flash-Lite, Qwen-3.6-Plus. Open-weight:
**Qwen-3.5-27B** (our reproduction target) and Gemma-4-31B. **CONFIRMED**, high
confidence. No parameter counts beyond what's implied by model names, no checkpoint
dates/hashes, are reported for any model — **UNAVAILABLE**.

## 4. Conditions

Two paper conditions: **baseline** (standard age prompting) and **skill-guided**
(skill-card-constrained). Both are distinct from our own future guardrail conditions
(R1/R2/R3) — see §8 of the brief and `evaluation/result_kind.py`, which structurally
prevents a `REFERENCE_RESULT` from being confused with a `GUARDRAIL_RESULT`.

## 5. Age conditions

Baseline anchor ages **7, 10, 13, 16**; skill-guided age bands **6-8, 9-11, 12-14,
15-17**. These are never merged — `evaluation/age_conditions.py` raises
`AgeConditionMismatchError` if code tries to. **CONFIRMED**, high confidence.

## 6. Benchmark structure

10 subtests: Block Design, Similarities, Digit Span, Picture Concepts, Coding,
Vocabulary, Letter-Number Sequencing, Matrix Reasoning, Comprehension, Symbol Search.
**CONFIRMED** (names), high confidence. Item counts, per-subtest structure, and exact
task content: **UNAVAILABLE** — not published, not in the repository.

## 7. Environment

Playwright + real browser, DOM-assisted mode (screenshot + accessibility
representation). **CONFIRMED**, high confidence, and independently validated as buildable
in Phase 2.5 (our generic adapter uses the current Playwright equivalent, `aria_snapshot()`,
since the paper's era's `page.accessibility` API has since been removed upstream).
Available actions, exact state-exposure rules, termination/reversal/discontinuation
rules, and per-step telemetry format used by the *official* environment: **UNAVAILABLE**
/ **REQUIRES AUTHOR ACCESS**.

## 8. Scoring

Binary for objective items; correct-operations-within-time-limit for Coding; 0/1/2
rubric with two blind human raters for open-ended items. **CONFIRMED** (description),
medium confidence (single-pass). Exact rubric criteria, answer keys, and normalization
formulas: **REQUIRES AUTHOR ACCESS** (explicitly withheld per copyright — see §18).

## 9. Reference results

`reference/reference_results.json` — every quantitative value extracted, each tagged
with confidence/status. **Only the four Qwen3.5-27B baseline Total scores (0.32/0.34/
0.29/0.30 at ages 7/10/13/16) are `status: confirmed`**, having been reproduced
identically across two independently-worded automated extraction passes. Every other
number (other models' scores, skill-guided scores, Spearman correlations, linguistic
complexity figures) is `unverified_single_pass`, and a full per-subtest/per-factor
breakdown table was extracted once and **rejected outright** for containing an internal
contradiction (implausible +4 to +5 SD factor z-scores for a model with a near-lowest
overall score) — see `reference/README.md`.

## 10. Reproduction matrix

Full component-by-component table: `docs/reproduction_specification.md`.

## 11. Claim reproducibility matrix

Full per-claim classification: `docs/claim_reproducibility_matrix.md`. Summary: of 8
major claims classified, 0 quantitative claims are reproducible now; only two framing/
methodological claims are (neither is a number to replicate).

## 12. Expected-vs-observed framework

`evaluation/expected_observed.py` — `ExpectedResult` (built from a `ReferenceResult`),
`ObservedResult` (our own repeated-run values, never pre-collapsed to a mean before
comparison), and `compare_expected_observed()`, which **raises
`IncompatibleComparisonError`** rather than computing a number when metric/model/
condition/age/subtest don't match on both sides. When the expected value itself is only
`low` confidence, or when observed data is too sparse (n < 2) for an interval/test, the
result's `interpretation_status` says so explicitly rather than presenting a false
sense of precision.

## 13. Future experiment matrix

| Experiment | Model | Benchmark | Condition | Purpose |
|---|---|---|---|---|
| R0 | Qwen3.5-27B | Official (blocked) | Paper baseline | Reproduction |
| Paper Skill-Guided | Qwen3.5-27B | Official (blocked) | Paper skill-guided | Reproduction |
| R1 | Qwen3.5-27B | Official (blocked) | Output guardrail | New intervention |
| R2 | Qwen3.5-27B | Official (blocked) | Action guardrail | New intervention |
| R3 | Qwen3.5-27B | Official (blocked) | Dynamic guardrail | New intervention |

None of these are implemented or run this phase — `evaluation/conditions.py`'s
`IMPLEMENTED_CONDITIONS` remains limited to the identifier for R0, with no algorithm.

## 14. Figure plan

10 figures specified as data in `evaluation/figure_spec.py` (`FIGURE_PLAN`) — each with
x/y axes, units, grouping, required statistical annotations, required data, and a
`data_currently_exists` flag. **Only Figure 1** (the reference paper's own age
trajectory) can be drawn today, and only from the low/medium-confidence
`reference_results.json` data — every other figure needs real observed data that
doesn't exist yet. `evaluation/reporting.generate_figure_caption()` renders a caption
that says "DATA NOT YET AVAILABLE" for any figure whose flag is False, so no figure can
silently render with numbers it shouldn't have.

## 15. Table plan

9 tables specified in `evaluation/table_spec.py` (`TABLE_PLAN`). Tables 1-3 (models,
reproduction matrix, reference results) are populated with what we actually have today;
tables 4-9 (our results, R0-R3 comparison, significance, failure analysis, cost, and
ablations) all require data that doesn't exist yet and are marked `populated=False`.

## 16. Statistical plan

Every future measured result must carry N, mean, median, stdev, a confidence interval
(bootstrap and/or normal-approximation), an effect size (Cohen's d), and — now added
this phase — a significance test (`evaluation.statistics_utils.welch_t_test`, a
normal-approximation p-value, explicitly documented as an approximation rather than an
exact Student's-t result) plus multiple-comparison correction (Bonferroni,
Benjamini-Hochberg) when comparing more than one pair. No function in this codebase
computes a p-value without also returning the sample size(s) that produced it, and none
auto-flags "significance" — that judgment is left to whoever reads `n` alongside `p`.

## 17. Data provenance

`evaluation/provenance.py` defines the seven-stage chain (raw_trajectory → task_result →
processed_result → metric → statistical_analysis → figure_or_table → paper_statement).
`ProvenanceChain.is_grounded_in_raw_data()` is what "no manually typed experimental
results" means operationally for `OUR_RESULT`/`REPRODUCTION_RESULT`/`GUARDRAIL_RESULT`;
`is_grounded_in_paper_statement()` is the equivalent check for a `REFERENCE_RESULT`.

## 18. Copyright / ethics constraints

- Benchmark items are withheld by the authors (WISC copyright) — confirmed directly
  from the repository's own access-policy document, not inferred.
- No WISC-derived material has been created anywhere in this repository (verified by
  repository-wide search in Phase 2.5 and re-confirmed by inspection this phase — the
  only WISC/subtest-name mentions are documentation of what the paper says, or explicit
  disclaimers that our own fixtures are *not* derived from it).
- We will not recreate copyrighted items under any circumstance, including for
  "placeholder" or test purposes.
- Any independent benchmark content we ever build is required to carry the
  `INDEPENDENT_EXPERIMENT` tag (`reproduction_kind.py`, Phase 2) and must never be
  labeled `official_childagenteval`.
- Publication rights for anything obtained via controlled author access remain
  unconfirmed — see `docs/author_access_requirements.md` items 7-9.

## 19. Author-access requirements

Full checklist: `docs/author_access_requirements.md`. Nine categories: benchmark access,
task/environment access, scoring, prompts, configuration, baseline details, permitted
use, publication rights, redistribution restrictions. None received as of this phase.

## 20. Remaining uncertainties

- The paper's exact "standard age prompting" and skill-card text remain unpublished; our
  harness prompt is an explicitly-labeled placeholder, never to be used for a real
  reproduction claim.
- Real per-item/per-step token and call volume is still unknown, so realistic experiment
  cost cannot be forecast (unchanged since Phase 1).
- Our own extraction of the paper's granular per-subtest/per-factor results failed an
  internal-consistency check and was rejected — meaning even *if* official access is
  granted, we should re-verify any number we think we already "know" from the paper
  before using it as an `ExpectedResult`.
- The paper itself reports no confidence intervals, significance tests, or variance
  estimates (medium confidence — single-pass extraction of this specific claim) — if
  true, any comparison we run will be statistically more rigorous than what we're
  comparing against, which is worth stating plainly rather than implying the paper's
  numbers carry the same uncertainty quantification ours will.
- Whether the official benchmark provides any dev/validation/test split remains unknown;
  `evaluation/splits.py`'s `NullSplitProvider` documents this as an open question, not an
  assumption.
