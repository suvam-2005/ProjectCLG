# Draft — evaluation request email

Not sent. Review, fill in the bracketed fields, and send from your own email client —
this isn't something to send on your behalf without your review.

---

**To:** yifan26@illinois.edu
**Subject:** ChildAgentEval Evaluation Request - Qwen3.5-27B

Hi Yifan,

I'm requesting a ChildAgentEval evaluation, per the process in your repo's
`docs/evaluation_access.md`.

1. **Model name, version, organization:** Qwen3.5-27B (open-weight), Alibaba Qwen team,
   accessed via OpenRouter (`qwen/qwen3.5-27b`) — [your name / affiliation here].
2. **Access method:** OpenRouter API endpoint.
3. **Supported modalities:** vision-language (text+image input, text output) — matches
   your DOM-assisted mode (screenshot + accessibility tree).
4. **Inference constraints:** temperature 0, deterministic decoding where the benchmark
   permits, no other sampling parameters set.
5. **Target evaluation setting:** [choose: baseline only / skill-guided only / both] across
   all four anchor ages (7, 10, 13, 16) [and/or skill-guided age bands 6-8, 9-11, 12-14,
   15-17 if in scope].
6. **Confidentiality / publication / attribution:** [state your intended use — e.g.
   coursework/research project, whether you intend to publish or just study internally].
7. **Primary contact:** [your name and email].

We're separately building our own guardrail-research harness (cost-bounded OpenRouter
client, telemetry, L0-L3 guardrail interface) for follow-on work studying whether output-,
action-, and trajectory-level cognitive guardrails improve alignment beyond the L0
baseline — happy to share results if useful to you.

Thanks,
[your name]
