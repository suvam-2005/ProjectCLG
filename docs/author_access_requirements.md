# Author Access Requirements

Exactly what we need from the PediaMedAI / ChildAgentEval team before we can claim an
**exact** reproduction of any paper result. This supersedes nothing in
`docs/email_draft_to_authors.md` (Phase 0) — it's the fuller checklist behind that
initial request, for use as the project matures.

## 1. Benchmark access
The actual ten subtests' task content (Block Design boards, Digit Span sequences,
Vocabulary items, etc.) or a controlled way to run our model against them without us
ever seeing the protected item content directly.

## 2. Task/environment access
The real Playwright-driven pages/DOM structure per subtest, or equivalent controlled
execution so our agent interacts with the actual environment rather than a page we
built from a narrative description.

## 3. Scoring
The exact scoring rubrics (binary criteria, the Coding time-limit/operation-count rule,
the 0/1/2 open-ended rubric) and, ideally, access to (or replication of) the
two-human-rater protocol — or confirmation that the authors will score our runs
themselves under their controlled process.

## 4. Prompts
The exact "standard age prompting" wording used for baseline, and the skill-card
format/content used for the skill-guided condition. Our current placeholder prompt
(`configs/prompts/standard_age_prompt.placeholder.txt`) must never be used in anything
claiming to reproduce the paper.

## 5. Configuration
Decoding settings actually used in the paper's own experiments (temperature, max
tokens, sampling), if any were fixed, since none are stated in the publicly available
text.

## 6. Baseline details
Item counts per subtest, total trials per model/condition/age, and the exact
per-model/per-age Table 1/2 values at a trustworthy source (our own extraction of the
granular breakdown failed an internal-consistency check — see
`src/childagenteval_research/evaluation/source_evidence.py` — so even the numbers we
"have" need author confirmation before being trusted for comparison).

## 7. Permitted use
Explicit confirmation of what we are allowed to do with results obtained under
controlled access: internal analysis only, coursework/research use, or publication.

## 8. Publication rights
Whether we may publish our own Qwen3.5-27B numbers (obtained via their controlled
evaluation) alongside our guardrail research, and under what attribution/citation
requirements.

## 9. Redistribution restrictions
Confirmation that we may not redistribute any protected item content, scoring rubric,
or administration script we're given access to — and what, if anything, we may share
(e.g. aggregate summaries, trajectory metadata stripped of item content).

---

None of the above has been received as of this phase. The evaluation request drafted in
`docs/email_draft_to_authors.md` was sent (per the user's Phase 2 status update); no
response has been incorporated into this project yet.
