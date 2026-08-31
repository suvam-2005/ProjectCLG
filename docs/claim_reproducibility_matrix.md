# Claim Reproducibility Matrix

For each major conclusion the paper draws (per the automated extraction passes in
Phase 0 and Phase 4 — see `source_evidence.py` for citations), a classification of
whether *we* can currently test it, and why. A claim being "described" in the paper does
not make it reproducible — this matrix only marks REPRODUCIBLE_NOW when we actually have
everything required.

| # | Claim (as reported) | Classification | Why |
|---|---|---|---|
| 1 | "Standard age prompting produces inconsistent/non-monotonic developmental ordering" (models don't reliably get more child-like with age) | REQUIRES OFFICIAL ACCESS | Testing this requires running the actual benchmark items across all 4 anchor ages — the items don't exist in our environment |
| 2 | "Skill-guided agents show clearer developmental differentiation than standard prompting" | REQUIRES OFFICIAL ACCESS | Requires both the official benchmark AND the skill-distillation pipeline/skill cards, neither of which is published |
| 3 | "Language/crystallized-knowledge dimensions (Gc) are easier to calibrate than working memory and processing speed" | REQUIRES ADDITIONAL DATA | Even with benchmark access, this needs the per-factor (Gc/WM/Gf-Gv/PSI) scoring breakdown — and our one attempt to extract that breakdown from the paper's table produced internally-implausible numbers (see `source_evidence.py`), so we don't yet trust even the paper's own reported version of this claim enough to compare against |
| 4 | Qwen3.5-27B (our reproduction target) scores lower overall than the proprietary models tested | REQUIRES OFFICIAL ACCESS | The paper's own Qwen3.5-27B numbers are only MEDIUM confidence (single extraction tool, cross-verified twice but never against ground truth) and we have zero observed data of our own yet — nothing to compare |
| 5 | Age 16 vs. age 7 score gap is near zero for baseline prompting, larger for skill-guided | NOT REPRODUCIBLE FROM PUBLIC MATERIALS | The specific gap values extracted are LOW confidence (single-pass, unverified) and not included in `reference_results.json` at all as trustworthy; nothing to reproduce them against without access |
| 6 | "The current evaluation framework does not compute confidence intervals, formal significance tests, or variance estimates" (the paper's own stated limitation) | REPRODUCIBLE NOW (as a documentation fact, not an experimental result) | This isn't an experimental claim to replicate — it's a methodological limitation we can simply note and then deliberately do better (Phase 3's statistics framework) |
| 7 | ChildAgentEval "exposes where current agentic AI systems can and cannot simulate age-specific cognitive behavior" (general framing/motivation) | REPRODUCIBLE NOW (as framing) | This is the research question itself, not a specific numeric result — our evaluation framework (Phase 3) is built to test exactly this once data exists |
| 8 | Ten interactive subtests map to specific CHC cognitive factors in a specific way | REQUIRES ADDITIONAL DATA | The subtest names are confirmed; the exact factor-to-subtest mapping and per-subtest scoring came only from the unreliable extraction pass and needs author confirmation |

## What "REPRODUCIBLE_NOW" actually means here

Only claims 6 and 7 qualify, and neither is a quantitative result — they're framing and
a documented limitation. Every quantitative claim in the paper requires either official
benchmark access (claims 1, 2, 4) or additional data beyond what's public even with
access granted (claims 3, 5, 8), because our own extraction attempt at the granular
results table failed an internal-consistency check and was rejected rather than trusted.
