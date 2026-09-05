# Setup — ChildAgentEval Research

Commands to install the engine, run the independent benchmark, generate results, and
verify everything with tests. Run all commands from the project root
(`childagenteval-research/`) unless noted otherwise.

## 1. Install

```bash
# create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows (PowerShell/Git Bash: .venv\Scripts\Activate.ps1)
# source .venv/bin/activate      # macOS/Linux

# install runtime + dev dependencies
pip install -r requirements-dev.txt

# install the package itself (editable) so `childagenteval_research` is importable
pip install -e .

# install the headless Chromium build Playwright drives (only Chromium is needed)
playwright install chromium
```

## 2. Configure secrets

```bash
copy .env.example .env      # Windows
# cp .env.example .env      # macOS/Linux
```

Edit `.env` and set:

```
OPENROUTER_API_KEY=sk-...
```

`.env` is gitignored — never commit it. All run parameters (model, temperature, budget
caps, step limits) live in `configs/independent_benchmark.yaml` / `configs/experiments/*.yaml`,
not in code or `.env`.

## 3. Start the engine (single-request smoke test)

Validates the inference/cost/telemetry pipeline end-to-end with exactly one real
OpenRouter call before running the full benchmark:

```bash
python scripts/smoke_test_phase1.py
```

## 4. Run the benchmarks

Each condition (`L0` = no guardrail control, `L1` = output guardrail, `L2` = action
guardrail, `L3` = dynamic trajectory guardrail) is run separately and serially —
concurrent runs are not safe against the shared project cost ledger (see
`docs/phase5c_pilot_reliability_and_freeze.md`).

```bash
# pilot: 1 task per category at age 10, to sanity-check a condition cheaply
python scripts/run_independent_benchmark.py --condition L0 --pilot

# full run per condition (32 tasks each)
python scripts/run_independent_benchmark.py --condition L0
python scripts/run_independent_benchmark.py --condition L1
python scripts/run_independent_benchmark.py --condition L2
python scripts/run_independent_benchmark.py --condition L3

# optional: run an explicit subset of tasks instead of --pilot/full
python scripts/run_independent_benchmark.py --condition L0 --task-ids abstraction_age10_v1 language_age10_v1
```

Every request is checked against both an $8.00 combined benchmark cap and the $10.00
whole-project hard cap (`configs/independent_benchmark.yaml` → `budget:`) before it is
sent; the run halts if either cap is exceeded.

## 5. Build derived results (manifests, statistics, figures, reports)

Run after all four conditions (L0-L3) have produced raw data:

```bash
# task pages — only needed if task JSON under benchmark/tasks/ changed
python scripts/generate_benchmark_pages.py

# statistical analysis: processed data + statistics tables from raw data
python scripts/analyze_full_benchmark.py

# experiment + reproducibility manifests
python scripts/build_manifests.py

# research-report figures (10 figures) from processed/statistics data
python scripts/generate_final_figures.py

# lay-audience outcome brief: data summary + its 10 presentation figures
python scripts/build_outcome_data_summary.py
python scripts/generate_outcome_brief_figures.py
```

## Where results are stored

| Content | Path |
|---|---|
| Raw per-task results (one line per task run) | `data/independent_benchmark/raw/{L0,L1,L2,L3}.jsonl` |
| Pilot raw results | `data/independent_benchmark/pilot/run_*/raw/` |
| Per-step trajectories (full agent/guardrail/environment log) | `data/independent_benchmark/raw/trajectories/{condition}/{task_id}.jsonl` |
| Processed/aggregated data (alignment, capability, tradeoff, per-age/category) | `data/independent_benchmark/processed/*.json` |
| Statistical summaries (descriptive stats, L0 comparisons, data-quality report) | `data/independent_benchmark/statistics/*.json` |
| Cost ledgers (per-condition + whole-project spend tracking) | `.state/cost_ledger.json`, `.state/benchmark_cost_ledger_{condition}.json` (gitignored) |
| Research-report figures | `reports/figures/figure1_...png` … `figure10_...png` |
| Outcome-brief figures | `reports/outcome_figures/fig01_...png` … `fig10_...png` |
| Reports (prose, tables, reproducibility manifest) | `reports/benchmark_report.md`, `reports/tables.md`, `reports/reference_vs_ours.md`, `reports/final_results_summary.md`, `reports/outcome_brief.{md,html}`, `reports/reproducibility_manifest.json`, `reports/outcome_data_summary.json` |
| Reference (published paper) results, for comparison only | `reference/reference_results.json` |

## 6. Test it

```bash
# full test suite
pytest

# just this session's touched areas
pytest tests/test_agent.py tests/test_environment.py tests/test_actions.py \
       tests/test_eval_statistics_utils.py

# with coverage-style verbosity while debugging
pytest -v tests/
```

All tests run against mocked models/environments (`environment/mock_environment.py`,
fake model clients) — they never call OpenRouter or spend real budget, so they're safe
to run anytime without `.env` configured.
