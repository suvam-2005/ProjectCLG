# Reproduction Specification — Reference Paper vs. Our Setup

Source discipline: every "Reference paper" cell below is backed by a row in
`src/childagenteval_research/evaluation/source_evidence.py` (claim/source/location/
confidence/status) — see that file for full citations. Nothing here was inferred from
blogs, summaries, or any source other than the arXiv paper (HTML/PDF), its official
GitHub repository, and the live OpenRouter API.

Status legend: **CONFIRMED** (evidence supports it), **NOT CONFIRMED** (evidence is
weak/single-pass), **DIFFERENT** (ours deliberately or necessarily diverges),
**UNAVAILABLE** (not published anywhere we can see), **REQUIRES AUTHOR ACCESS** (only
the ChildAgentEval team can supply it).

| Component | Reference paper | Our setup | Status | Evidence |
|---|---|---|---|---|
| Model (ours) | Qwen3.5-27B (open-weight) | `qwen/qwen3.5-27b` via OpenRouter | CONFIRMED | Model list confirmed in paper text; OpenRouter listing verified live (Phase 0/1) |
| Model version/checkpoint | Not reported (no date/hash given for any model) | OpenRouter canonical slug `qwen/qwen3.5-27b-20260224` | DIFFERENT | Paper gives no checkpoint identifier at all; ours is whatever OpenRouter currently routes to |
| Prompt (standard age prompting) | Exists, exact wording not published | Placeholder text, explicitly labeled non-official (`configs/prompts/standard_age_prompt.placeholder.txt`) | REQUIRES AUTHOR ACCESS | `docs/phase0_findings.md`; repo contains no prompt files |
| Age conditions (baseline) | Anchor ages 7, 10, 13, 16 | Same four ages supported (`age_conditions.py`) | CONFIRMED | Consistent across 3 independent paper fetches |
| Age conditions (skill-guided) | Bands 6-8, 9-11, 12-14, 15-17 | Same four bands supported, kept structurally distinct from anchor ages | CONFIRMED | Same as above |
| Benchmark (ChildAgentEval itself) | 10 subtests, WISC-inspired, browser-based | No implementation — `environment/factory.py` raises `OfficialBenchmarkUnavailableError` for the `official_childagenteval` adapter | REQUIRES AUTHOR ACCESS | `docs/phase0_findings.md`; repo file tree has no benchmark code |
| Subtests | Block Design, Similarities, Digit Span, Picture Concepts, Coding, Vocabulary, Letter-Number Sequencing, Matrix Reasoning, Comprehension, Symbol Search | Names known, no item content | CONFIRMED (names only) | Consistent across 2 independent fetches |
| Browser | Real browser required | Real Chromium via Playwright, validated Phase 2.5 | CONFIRMED | `docs/phase2_5_browser_smoke_test.md` |
| Playwright | Used by the paper's environment | Used identically (our own generic adapter) | CONFIRMED | `environment/playwright_adapter.py` |
| DOM mode | "DOM-assisted": screenshot + sanitized accessibility tree | Screenshot (optional) + `page.locator("body").aria_snapshot()` | DIFFERENT (implementation detail) | Playwright's legacy `page.accessibility` API was removed upstream (Phase 2.5) — we use the current equivalent, which returns a different data shape (string, not object tree) than whatever the paper's original Playwright version produced |
| Screenshot mode | Present in DOM-assisted mode | Implemented, optional per adapter config | CONFIRMED (capability), DIFFERENT (never tested against real benchmark pages) | `test_playwright_real_browser.py` |
| Action schema | Not published (paper describes click/type/select behavior generically) | Generic click/type/select/scroll/keypress/wait/finish schema (`actions.py`) | DIFFERENT | Ours is an original design matching the paper's narrative description, not a copy of an unpublished schema |
| Scoring | Binary for objective items, correct-ops-in-time for Coding, 0/1/2 rubric + 2 human raters for open-ended items | Not implemented — `TaskPerformanceResult` fields are populated only by a real benchmark adapter, none exists | REQUIRES AUTHOR ACCESS | `docs/phase0_findings.md`; `capability.py` |
| Stopping rules (finish/reversal/discontinuation) | Paper mentions reversal/discontinuation as a WISC-inspired concept; exact rule unpublished | Our environment protocol supports a generic `finish` action and `Observation.done`; no reversal/discontinuation logic exists | REQUIRES AUTHOR ACCESS | No published rule found in either fetch |
| Skill guidance | A "skill distillation" pipeline from a calibration corpus (CHILDES, OCSC, Frog Story, LCCPW, ClassBank) | Not implemented; no skill cards exist | REQUIRES AUTHOR ACCESS | Single-pass evidence, `source_evidence.py` |
| Temperature | Not stated for any model in the results tables (our Qwen run's own settings are external to the paper) | 0 (fixed, enforced by `L0Config`) | DIFFERENT (ours is a design choice, paper's is unknown) | `configs/l0.yaml`; paper text did not state a temperature |
| Max tokens | Not reported | 512 (configurable, `max_output_tokens_per_call`) | DIFFERENT | Our own infrastructure choice |
| Number of runs | Not reported (no repetition count given) | Configurable (`RepetitionConfig`), not yet executed | UNAVAILABLE (paper), NOT YET RUN (ours) | `evaluation/repeated_runs.py` |
| Statistical method | **None** — paper explicitly states no CIs, significance tests, or variance estimates are computed | Bootstrap/normal CIs, Welch's t-test, rank correlation, multiple-comparison correction all implemented (Phase 3-4) | DIFFERENT (we add rigor the paper does not have) | `source_evidence.py` (Appendix A.5 quote, medium confidence) |
| Telemetry | Not published in detail beyond "extensive artifacts for every evaluation run" | Full JSONL `TrajectoryRecord` schema, cost ledger, experiment identity | DIFFERENT (ours is more granular than what's described) | `telemetry/schema.py` |
| Human raters | 2 independent raters, blind, 0/1/2 rubric, for open-ended items | Not available to us — no rater pool, no rubric | REQUIRES AUTHOR ACCESS | Single-pass evidence |
| Item counts / total trials | Not reported anywhere in the paper | Unknown — cannot be planned until either official access responds or we scope real content | UNAVAILABLE | `docs/phase0_findings.md`, `docs/phase1_smoke_test.md` |

See `docs/phase4_reproduction_specification.md` for the full narrative writeup and
`docs/claim_reproducibility_matrix.md` for which of the paper's conclusions can actually
be tested with what's available today.
