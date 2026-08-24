# Phase 0 — Environment Inspection & Repository Setup

Date: 2026-08-24
Scope: Verify what is publicly available for reproducing the Qwen3.5-27B baseline
from "Evaluating Cognitive Age Alignment in Interactive AI Agents" (arXiv:2605.17894,
ChildAgentEval, PediaMedAI). No API calls were made. No benchmark content was invented.

## 1. Paper — verified real

- Title: *Evaluating Cognitive Age Alignment in Interactive AI Agents*
- arXiv: 2605.17894 (cs.AI), submitted May 2026, CC-BY 4.0
- Authors: Yifan Shen, Jiawen Zhang, Jian Xu, Junho Kim, Ismini Lourentzou, Xu Cao, Meihuan Huang
- Introduces ChildAgentEval, described as "the first psychometrically grounded interactive
  benchmark for evaluating cognitive age alignment in MLLM-based agents," inspired by the
  Wechsler Intelligence Scale for Children (WISC).

## 2–5. Repository — verified real, but contains NO benchmark code

Repo: `github.com/PediaMedAI/ChildAgentEval`, created 2026-05-18, ~2000 KB, no license file,
no releases, no code beyond docs.

Full file tree (verified via GitHub API, recursive):

```
CITATION.bib
CITATION.cff
README.md
assets/figures/childagenteval-framework.png
assets/figures/developmental-metrics.png
assets/figures/developmental-trajectories.png
assets/figures/skill-distillation-pipeline.png
assets/figures/subtests-overview.png
assets/pediamed-ai-logo.png
docs/benchmark_overview.md
docs/evaluation_access.md
```

**There is no installation instructions file, no benchmark implementation, no browser
environment, no task definitions, no scoring code, no prompt definitions, no model/API
interface code, no data files, and no calibration data in this repository.** It is a paper
landing page / access-request portal, not a runnable codebase.

### Critical finding: the evaluation protocol is explicitly gated, not open

From `docs/evaluation_access.md` (quoted verbatim):

> "Because the Wechsler scales contain copyrighted clinical materials, we cannot publicly
> release the full evaluation protocol, protected item content, answer keys, scoring
> rubrics, normative conversion details, or any materials that could enable reconstruction
> of the original assessment."

> "External researchers can evaluate their own models by providing controlled access to the
> model, while the ChildAgentEval team administers the benchmark under consistent
> interaction and scoring procedures."

The only sanctioned path to get a model evaluated on the **actual** ChildAgentEval benchmark
is emailing `yifan26@illinois.edu` with model access details and letting the authors run it
on their own infrastructure. They return aggregate summaries only (cognitive-factor
profiles, trajectory plots, error-pattern summaries) — never item-level content, answer
keys, or full trajectories.

## 6–10. What the paper itself describes (methodology text, not released as code)

Extracted from the arXiv HTML source (not from the repo, which does not contain this):

- **10 subtests**: Block Design, Similarities, Digit Span, Picture Concepts, Coding,
  Vocabulary, Letter-Number Sequencing, Matrix Reasoning, Comprehension, **Symbol Search**
  (the paper names Symbol Search as the tenth; the user's brief left this slot open —
  confirmed from the paper text, not assumed).
- **Environment**: Playwright-driven simulated browser. "DOM-assisted mode" gives the agent
  a screenshot plus a sanitized accessibility tree of visible interactive elements.
- **Models evaluated in the paper**: GPT-5.4, Gemini-3.1-Pro, Gemini-3.1-Flash-Lite,
  Qwen-3.6-Plus (proprietary); Qwen-3.5-27B and Gemma-4-31B (open-weight).
  → Qwen-3.5-27B is confirmed as one of the paper's actual open-weight baselines, matching
  the requested model.
- **Scoring**: objective subtests use strict binary scoring (1 point per correct
  action/exact keyword match); Coding is scored as correct operations completed within a
  time limit; open-ended verbal subtests (e.g. Similarities, Vocabulary, Comprehension) use
  a 0/1/2-point rubric.
- **Human raters required**: "Each open-ended response is independently scored by two human
  raters" who are blind to model identity, condition, target age, and hypothesis. This is a
  mandatory, non-automatable component of the original scoring for at least 3 of the 10
  subtests.
- **Item counts**: not stated anywhere in the paper (per-subtest or total). Cannot be
  determined without the restricted materials.
- **Call/trial volume**: not stated. Only "a complete administration requires approximately
  one hour of wall-clock time" per run is given — no request or token counts.
- **Age conditions**: baseline anchor ages are 7, 10, 13, 16. Skill-guided condition uses
  age *bands* 6–8, 9–11, 12–14, 15–17 — these are two distinct schemes, not
  interchangeable (matches the brief; confirmed in paper text, not assumed).
- **Calibration data**: a multi-source corpus spanning ages 6–17, drawing on CHILDES, OCSC,
  Frog Story, LCCPW, and ClassBank for the skill-distillation pipeline. None of this corpus
  or its processing code is in the repo.

## 11. What can be reproduced with Qwen3.5-27B via OpenRouter

- The model exists on OpenRouter as `qwen/qwen3.5-27b` (262K context) — verified live
  against the OpenRouter `/models` endpoint. Matches the brief exactly.
- We can build: an OpenRouter client, a hard cost guard, a config-driven experiment runner,
  a guardrail interface (L0–L3 stubs), and a telemetry schema — all generic infrastructure
  not dependent on restricted content.
- We can prompt Qwen3.5-27B with **standard age prompting** (asking it to act as a child of
  a given age) on **tasks we construct ourselves**, and log its behavior. This can exercise
  the harness end-to-end.

## 12. What cannot be reproduced exactly

- The actual ChildAgentEval task items (Block Design boards, Digit Span sequences,
  Vocabulary word lists, Matrix Reasoning matrices, Coding key-mappings, etc.) are
  unpublished and copyright-derived. **We cannot reconstruct these without inventing
  content the paper explicitly withholds.** Doing so would violate the user's explicit
  instruction not to invent benchmark implementation and would not constitute a
  reproduction of the paper's actual measurements.
- The Playwright browser/DOM harness that renders these specific tasks is not published —
  only described narratively.
- The scoring rubrics (0/1/2-point criteria) and answer keys are not published.
- The two-human-rater open-ended scoring pipeline cannot be reproduced without recruiting
  and training blind human raters — this is a structural, not a technical, limitation.
- The skill-distillation calibration corpus (CHILDES, OCSC, Frog Story, LCCPW, ClassBank)
  is not bundled or linked with processing code in the repo.
- Exact per-subtest item counts and call volumes cannot be determined, so a faithful
  replication of the original experiment's scale (and therefore its cost) cannot be planned
  precisely in advance.

**Bottom line: the "official Qwen3.5-27B baseline" in the paper cannot be independently
reproduced from public materials alone.** The repository is an access-request portal, not
a benchmark. Getting the actual paper numbers requires emailing the authors and having them
run their controlled infrastructure against our model — we would not control task content,
guardrail injection points, or per-step logging in that path, since we would not be running
the loop ourselves.

## 13. Reproduction plan (draft — for approval, nothing executed)

Two non-exclusive tracks, since the official benchmark is gated:

**Track A — Official channel (for a validated baseline number only)**
1. Email `yifan26@illinois.edu` requesting evaluation of `qwen/qwen3.5-27b` via OpenRouter,
   per the required fields in `evaluation_access.md` (model/version, access method,
   modality, inference constraints — temperature 0, deterministic — target setting:
   baseline + skill-guided across all 4 age bands).
   Limitation: this gives us *their* aggregate numbers, not a harness we can attach
   guardrails to, since we don't run the interaction loop.

**Track B — Our own harness (for the guardrail research, PHASE 2–5)**
1. Build the generic infrastructure now (cost guard, OpenRouter client, config schema,
   telemetry schema, GuardrailResult interface) — none of this depends on restricted
   content, so it's safe to build ahead of approval.
2. Do NOT build ChildAgentEval's actual tasks. Instead, either:
   (a) pause task-content work until Track A returns something usable, or
   (b) construct a small, clearly-labeled **original** task set inspired only by the
   publicly documented *categories* (e.g. our own digit-span-style task, our own
   vocabulary list) — explicitly flagged everywhere as "not ChildAgentEval, not validated
   against the paper's items" so it is never confused with a reproduction.
3. Either way, L0 (no guardrail) must be fully working and reviewed before L1–L3 begin, per
   the brief.

This is a decision point, not something to resolve unilaterally — see the question posed
to the user alongside this report.

## 14. No expensive API runs were made

No inference requests were sent. `OPENROUTER_API_KEY` is not currently set in this
environment. Confirmed `qwen/qwen3.5-27b` is a live, listed OpenRouter model via the public
`/models` endpoint only (no completions endpoint called).
