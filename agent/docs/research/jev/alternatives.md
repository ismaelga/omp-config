# Jev Alternatives: Guardrails, Classifiers, Sandboxes — What Actually Works, With Numbers

## Bottom line

- **No prompt-injection classifier is adversarially robust.** Adaptive attacks bypass every published detection defense with >50% ASR (UIUC, [arXiv:2503.00061](https://arxiv.org/abs/2503.00061)); simple character injection (emoji smuggling, upside-down text) achieves up to 100% evasion against six named commercial and open detectors ([arXiv:2504.11168](https://arxiv.org/abs/2504.11168)). A hosted typed-judgment API is in the same category and inherits the same failure mode; there is no benchmark anywhere showing a Jev-class or any hosted judge surviving an adaptive attacker.
- **Small local classifiers are embarrassingly competitive.** Fine-tuned DeBERTa/BERT detectors beat commercial API guardrails on out-of-distribution data (IBM Adversarial Prompt Evaluation, Table 3: DeBERTa F1 0.672 OOD vs Llama-Guard-2 0.474, OpenAI Moderation 0.134, NeMo-inspired rail 0.056) at ~500MB RAM and milliseconds of latency ([arXiv:2502.15427](https://arxiv.org/abs/2502.15427)).
- **System-level controls dominate the Pareto frontier.** On AgentDojo, tool filtering (a policy question, not a classifier) reached 7.5% ASR; CaMeL got 0% ASR with provable security at 77% utility vs 84% undefended ([arXiv:2503.18813](https://arxiv.org/abs/2503.18813)). The harness-native controls (sandbox, permissions, no credentials) are what every serious harness actually ships.
- **The whole guardrail category is evidence-poor.** Every prompt-injection detector ships marketing numbers with no reproducible evidence (raucle-bench, epic28-ltd/raucle-bench README, 2026). Where neutral benchmarks exist (Lakera PINT, 4,314 inputs), even the best commercial scorer (Lakera Guard 95.2%) is closely shadowed by a free 86M-param model (PromptGuard 2 86M: 78.8%), and a free DeBERTa (79.1%) — the commercial premium buys ~10-16 points, not safety.
- **Verdict for our threat model:** sandbox the agent (Seatbelt/bubblewrap container, no credentials), keep regex/denylist + confirmation prompts as the tool-call gate, optionally run a small local DeBERTa as a cheap screen on fetched web/PR content — and use Jev only where a natural-language judgment over rich state is genuinely the right primitive (route/stuck/screen triage), not as the destructive-action guard. The destructive-action guard should not be a classifier at all.

---

## 1. Purpose-built guardrail systems

### Meta LlamaFirewall / PromptGuard 2 / Llama Guard

Source: [arXiv:2505.03574](https://arxiv.org/html/2505.03574v1) (LlamaFirewall paper, 2025-05-06) and [PINT results](https://github.com/lakeraai/pint-benchmark).

- **PromptGuard 2 86M** (DeBERTa-based, runs locally): AUC 0.99 English / 0.995 multilingual, **97.5% recall at 1% FPR** on Meta's *private* jailbreak benchmark — claimed, and tuned by the vendor, so treat as upper bound. Latency 92.4ms per classification on A100 at 512 tokens (paper §4.1, Table "PromptGuard 2").
- **AgentDojo (LlamaFirewall, own evaluation, paper Table in §4.3.2):** baseline ASR 17.63% → PromptGuard 2 alone 7.53% → AlignmentCheck (Llama 4 Maverick CoT auditor) 2.89% → combined **1.75% ASR**, utility 47.7% → 42.7%. AlignmentCheck costs a second LLM call over the full trace — the latency budget for a single-user harness is roughly one extra big-model inference per action.
- **PINT benchmark (independent, Lakera-run):** PromptGuard 2 86M scored **78.76%**, PromptGuard 1 (original) **61.82%** — the vendor's private-benchmark advantage does not fully transfer ([pint-benchmark README](https://github.com/lakeraai/pint-benchmark), scores dated 2025-05-02/05).
- **Failure mode (independent):** character-injection evasion — Prompt Guard had ASRs of 70.44% (injection) / 73.08% (jailbreak) under character-injection attacks, and AML evasion dropped it to 12.66%/2.76% (its relative strength) ([arXiv:2504.11168](https://arxiv.org/html/2504.11168v1) §5). Also "Meta's AI safety system defeated by the space bar" (The Register, 2024-07-29, cited therein).
- **Llama Guard family** (LLM-as-classifier, ~8B): WildGuardTest Total F1 56.0% (v1), 70.9% (v2) ([arXiv:2406.18495](https://arxiv.org/pdf/2406.18495) Table); LlamaGuard3-8B avg F1 76.2% across ToxiC/OpenAIMod/Aegis/SimpST/WildGuard ([arXiv:2510.19169](https://arxiv.org/pdf/2510.19169) Table 2). On the IBM benchmark's OOD split: F1 0.474, precision 0.453 ([arXiv:2502.15427](https://arxiv.org/html/2502.15427) Table 3) — i.e., roughly coin-flip-level usefulness on unseen attacks despite 96% accuracy, because benign dominates the test set.
- **Cost/locality:** Llama Guard requires hosting an 8B model (GPU); PromptGuard 86M/22M run on CPU. None of Meta's stack covers *tool-call policy* natively — CodeShield (static analysis of LLM-generated code, 96% precision / 79% recall on CyberSecEval3 completions, ~60ms tier-1 / ~300ms tier-2, paper §4.4) is the closest, and it is a regex/Semgrep engine, not a judgment API.

### NVIDIA NeMo Guardrails

- LLM-rail architecture: +1 extra inference per prompt; SmoothLLM for comparison adds up to 10 ([arXiv:2502.15427](https://arxiv.org/html/2502.15427) §6 RQ2).
- Measured (IBM benchmark): NeMo-inspired input rail on OOD data: **ACC 0.38, F1 0.056** — worst classifier-family result in the table ([arXiv:2502.15427](https://arxiv.org/html/2502.15427) Table 3). Its strength is dialog-flow control, not injection detection.
- Independent single-config education-domain test: 0% bypass but **16.22% false positives and >1.4s mean latency** (p95 >4s) ([arXiv:2605.06669](https://arxiv.org/pdf/2605.06669)).
- Jailbreak-detect variant (random forest over embeddings, [arXiv:2412.01547](https://arxiv.org/abs/2412.01547)): 72.54% ASR under character injection — near-worst of six detectors tested ([arXiv:2504.11168](https://arxiv.org/html/2504.11168v1) §5.1).
- No published number exists for NeMo Guardrails on tool-call guarding in a coding harness.

### Invariant Labs

- AgentDojo authors ([agentdojo.spylab.ai](https://agentdojo.spylab.ai), [arXiv:2406.13352](https://arxiv.org/abs/2406.13352)). Their own numbers: GPT-4o + BERT injection detector as defense reduced ASR to ~8% (intro) — but "the prompt injection detector has too many false positives, however, and significantly degrades utility" (§4.3, Fig. 9). Tool filtering (non-ML) reached **7.5% ASR** and was their standout defense. AgentDojo covers 97 tasks / 629 security cases, 4 suites (Workspace, Slack, Travel, Banking).
- Invariant also ships a guard framework (semgrep-based, per LlamaFirewall §2.2) but no independent benchmark of it was found (searched: arXiv, GitHub, Google — nothing beyond their own blog).

### Lakera Guard

- Best independent PINT score: **95.22%** (2025-05-02, [pint-benchmark README](https://github.com/lakeraai/pint-benchmark)) — but the benchmark is run by Lakera itself; the neutrality claim ("no training on PINT inputs") is asserted, not audited. PINT's category mix (36.5% chat, 36.5% documents, 20.9% hard negatives) is closer to a RAG pipeline than a coding-agent tool stream.
- Hosted API only; latency not published (negative finding: no latency number anywhere in PINT materials).

### Protect AI / Rebuff / Guardrails AI / promptfoo / Vijil

- **ProtectAI DeBERTa v2** — see §4; the strongest local open model. v1 archived alongside the LLM Guard project (model card warning banner, [huggingface.co/protectai/deberta-v3-base-prompt-injection-v2](https://huggingface.co/protectai/deberta-v3-base-prompt-injection-v2)).
- **Rebuff**: shipped with marketing numbers and no reproducible evidence; adapter for raucle-bench still a welcome-PR (raucle-bench README "What's in v0.1" table; also called out in [particula.tech comparison](https://particula.tech/blog/ai-guardrails-compared-nemo-guardrails-ai-llama-guard), secondary source). **Negative finding:** no credible published benchmark of Rebuff exists as of writing (searched arXiv, GitHub, raucle-bench).
- **Guardrails AI**: Python validator framework (50-200ms per validation — secondary source [particula.tech](https://particula.tech/blog/ai-guardrails-compared-nemo-guardrails-ai-llama-guard)); on the NFL benchmark: PHTest F1 0.917 but adversarial SAGE F1 0.600 — among the worst adversarial performers ([arXiv:2504.00441v2](https://arxiv.org/html/2504.00441v2) Table 2).
- **promptfoo**: red-teaming harness, not a runtime guardrail — useful for *testing* our Jev stack; no published detection benchmark of its own runtime behavior (its docs cover [testing guardrails](https://www.promptfoo.dev/docs/guides/testing-guardrails/), not being one).
- **Vijil (ModernBERT-based)**: fastest local option in NFL Table 2 (0.056s avg latency, adversarial F1 0.938 SAGE / 0.996 XTRAM) but falters on long-context attacks (0.451 on Long) ([arXiv:2504.00441v2](https://arxiv.org/html/2504.00441v2)). Under attack: worst of six detectors — 87.95% ASR (prompt injection) / 91.67% (jailbreak) under character injection ([arXiv:2504.11168v1](https://arxiv.org/html/2504.11168v1) §5.1).

**[actionable]** The NFL result (Table 2, [arXiv:2504.00441v2](https://arxiv.org/html/2504.00441v2)) is the single most decision-relevant table: a *free, small* classifier (enkryptai iad-v3, 0.038s latency) matched or beat every provider API on 4 of 5 adversarial datasets, and every LLM-based guardrail's advantage came at 5-200x latency. If we add a screen, a small local model is the only class that fits a per-tool-call budget.

## 2. Harness-native controls (what actually ships)

### Claude Code

- Tiered permission system + modes (default/acceptEdits/plan/auto/dontAsk/bypassPermissions); deny > ask > allow rule precedence; read-only command set (`ls`, `cat`, `grep`, `find`...) auto-approved ([permissions docs](https://code.claude.com/docs/en/permissions), fetched 2026-09-22).
- OS-level Bash sandbox: Seatbelt on macOS, bubblewrap+socat+optional seccomp on Linux; filesystem read/write allow-deny lists and **network domain allowlist** enforced for every command and child process ([sandboxing docs](https://code.claude.com/docs/en/sandboxing)). Docs are explicit that `Bash(curl *)`-style rules are **not** a security boundary ("doesn't match the same program invoked in a different form… use sandboxing") — the same argument applies to any regex gate, including ours.
- Docs' own recommendation hierarchy: for reliable URL filtering, "deny Bash network tools + sandbox network allowlist", not classifier judgment.

### OpenAI Codex

- Sandboxing + approvals docs redirect to [developers.openai.com/codex/security](https://developers.openai.com/codex/security) (verified 2026-09-22 via [repo docs/sandbox.md](https://github.com/openai/codex/blob/main/docs/sandbox.md)). **Negative finding:** the public docs I could reach describe the *Codex Security* product (vulnerability scanning), not the runtime sandbox policy details; sandbox internals are not published at the doc URL I could fetch. Observed behavior (harness runs commands in a sandboxed workspace with approval tiers) is consistent across the ecosystem but not citable to a primary doc from here — marked undated/incomplete.

### OpenHands

- Docker sandbox by default, "strongly recommends running via Docker for security", non-root via `SANDBOX_USER_ID=1000`, resource caps ([sandboxes overview](https://docs.openhands.dev/openhands/usage/sandboxes/overview), [byteiota OpenHands 1.0 writeup](https://byteiota.com/openhands-1-0-autonomous-coding-agent/), secondary).
- Security system is an **LLM self-assessed risk enum**: the tool schema gains a required `security_risk` field (LOW/MEDIUM/HIGH/UNKNOWN) that the *same LLM filling the tool call* also fills; `LLMSecurityAnalyzer` just reads it back — "No Additional LLM Calls: risk assessment happens inline" ([security architecture](https://docs.openhands.dev/sdk/arch/security)). `ConfirmRisky` policy (threshold=HIGH, confirm_unknown=True) is the default gate. **Failure mode is structural:** the attacker-controlled injection can steer the same generation that emits `security_risk`, so the risk label is untrusted under exactly our threat model (b) — this is a self-report, not a judgment. Source: [openhands-sdk security/llm_analyzer.py](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/openhands/sdk/security/llm_analyzer.py).

**[actionable]** OpenHands' `security_risk` design is the cheapest possible inline guard (zero extra calls) and is what Jev's `noul` gate competes with directly. It is also provably gameable by the very context it gates. Any Jev-based guard should be *paired* with an OS sandbox, never a substitute.

### Devin

- Closed-source. **Negative finding:** no published technical detail on its guard mechanism; only Anthropic/OpenAI-comparable sandbox claims in marketing material. Searched: web, docs, arXiv — nothing primary.

### Kernel primitives

- Seatbelt (macOS `sandbox_init` profiles), Landlock (Linux LSM, unprivileged since 5.13), seccomp-bpf, bubblewrap. These are the enforcement layer Claude Code and Codex wrap; deterministic, ~zero latency, and immune to semantic injection by construction. No LLM judgment layer can make a stronger guarantee than these for the "destructive action" threat (a): if the process cannot write outside the workspace and cannot reach the network, no prompt injection can change that.

## 3. The dumb baselines

- **Trivial baselines beat nothing, and the guardrail field fails to beat them cleanly.** raucle-bench (weekly-run, v0.1 dataset of 165 prompts, 6 attack classes + benign; [results/latest.json](https://github.com/epic28-ltd/raucle-bench/blob/main/results/latest.json), run 2026-09-21): `always-block` gets recall 1.0 / FPR 1.0; LLM Guard prompt-injection scanner gets recall 0.768 / FPR 0.125 / F1 0.8496 with a 145ms p50 latency; `raucle-detect` regex variants get precision 0.95-1.0 but recall 0.008-0.36. Read: **regex alone is near-useless as a recall tool but harmless as a false-positive tool; the ML layer adds recall at real latency cost and a real false-positive rate.**
- **`sudo`-style confirmation prompts** are the OpenHands/Claude Code default and have no bypass paper because they are not a classifier — they are a human decision. Their failure mode is prompt fatigue (user starts clicking "yes"), which is a UX problem, not an evasion problem.
- **Container with no credentials** removes the exfiltration channel entirely: an injected payload that cannot read `~/.aws/credentials` and cannot reach the network cannot exfiltrate. This is the only defense with a *proof-shaped* argument (CaMeL-style provable security, [arXiv:2503.18813](https://arxiv.org/abs/2503.18813): 77% of AgentDojo tasks with provable security vs 84% undefended).

**[actionable]** For threat (a) (agent doing something destructive), the dumb baseline stack — sandbox + denylist on destructive commands + confirm-on-write — covers it with zero network latency. A Jev guard on top of that adds at most a soft prior on *which* destructive commands to prompt for. It cannot beat "sandbox it and stop trying to classify" for that threat.

## 4. Small local classifiers

| Model | Size | Benchmark numbers | Latency | Local? |
|---|---|---|---|---|
| protectai/deberta-v3-base-prompt-injection-v2 | 86M backbone (DeBERTa-v3-base, ~184M total) | PINT 79.14% (2025-12-16, [results/protect_ai.md](https://github.com/lakeraai/pint-benchmark/blob/main/results/protect_ai.md)); OOD F1 0.672 ([arXiv:2502.15427](https://arxiv.org/html/2502.15427) Table 3); 95.25% acc on own post-training eval (model card, claimed) | ms-class on CPU/ONNX | Yes (836K downloads, Apache-2.0) |
| Meta PromptGuard 2 86M | 86M (mDeBERTa) | PINT 78.76%; AUC 0.98-0.995 (vendor benchmark) | 92.4ms @512tok A100 (paper) | Yes |
| Meta PromptGuard 2 22M | 22M (DeBERTa-xsmall) | AUC 0.995 EN | 19.3ms @512tok A100 (paper §4.1) | Yes, very cheap |
| vijil-mbert-prompt-injection (ModernBERT) | small | NFL adversarial F1: 0.938 SAGE / 0.996 XTRAM / 0.451 long-context | 0.056s avg | Yes |
| enkryptai iad-v3 | small | NFL adversarial F1: 0.896-0.991 | 0.038s avg | Yes |
| BERT/DeBERTa/GPT2 fine-tunes (IBM) | 371-548MB RAM | OOD F1 0.578 / 0.672 / 0.720 vs Llama-Guard-2 0.474, Azure 0.703 | "fraction of the compute cost" of LLM guards | Yes |

- IBM's central finding (RQ1 answer): "**simple baselines can display competitive out-of-distribution performance compared to many state-of-the-art defences**" ([arXiv:2502.15427](https://arxiv.org/html/2502.15427) §6) — either the open data covers the attack space and simple classifiers suffice, or no data exists to prove LLM guards generalize better. Either way, the hosted-API premium is unproven.
- ProtectAI v2's own card flags the two failure modes that matter for us: "does not detect jailbreak attacks or handle non-English prompts", and "**we do not recommend using this scanner for system prompts, as it produces false-positives**" — i.e., screening *agent* context is its weak spot by design.

## 5. The evidence on whether prompt-injection detection works at all

This decides whether the category is worth any latency:

1. **Adaptive attacks break everything detection-shaped.** Eight defenses (fine-tuned detector, LLM-based detector, perplexity filter, instruction prevention, delimiters, sandwich, paraphrasing, adversarial fine-tuning) all bypassed at >50% ASR via GCG/M-GCG/Two-stage-GCG/AutoDAN ([arXiv:2503.00061v2](https://arxiv.org/html/2503.00061v2), InjecAgent benchmark, 2025-03). Detection rates of the fine-tuned detector and LLM detector dropped from 34-72% (original attacks) to **~0-10%** once adversarial strings were optimized against them (paper Table 2).
2. **Non-adaptive character obfuscation alone is enough.** Emoji smuggling: 100% ASR against *every* detector tested, including Azure Prompt Shield and Meta Prompt Guard ([arXiv:2504.11168v1](https://arxiv.org/html/2504.11168v1) §5.1). White-box transfer of word-importance rankings from a public model (ProtectAI v2) improved ASR against black-box Azure Prompt Shield in 7 of 8 attack techniques (Table 3).
3. **AgentDojo's structure result** ([arXiv:2406.13352v3](https://arxiv.org/html/2406.13352v3) §4.3): all *prompt-shaping* defenses (delimiters, sandwiching, detector) lose 15-20% utility under attack; only the **tool filter** (a capability question) and structural isolation (CaMeL) hold the line without paying in utility. The BERT detector defense specifically was called out for too many false positives degrading utility.
4. **The counter-evidence, honestly stated:** SecAlign (preference-optimization fine-tune, [arXiv:2410.05451](https://arxiv.org/abs/2410.05451), CCS'25) reports <10% ASR even against unseen attack classes, and Meta's LlamaFirewall reports 1.75% combined ASR on AgentDojo. But both are (i) benchmark-selected by the defender, (ii) untested against the adaptive-attack suite of [arXiv:2503.00061](https://arxiv.org/abs/2503.00061), and (iii) SecAlign requires retraining the *agent* model, which we do not control. LlamaFirewall's AlignmentCheck also requires an extra large-model inference per trace step — fine for a chat product, painful for a per-tool-call guard in a fast harness.
5. **The field has no referee.** raucle-bench ([epic28-ltd/raucle-bench](https://github.com/epic28-ltd/raucle-bench)) exists precisely because "every prompt-injection detector ships with marketing numbers and no way to reproduce them"; its v0.1 is 165 prompts, so treat its numbers (LLM Guard F1 0.8496, raucle regex F1 0.52-0.26) as a floor-of-evidence, not a verdict.

## 6. Verdict for our threat model

Single-user coding-agent harness on a laptop; threats: (a) agent does something destructive unasked, (b) prompt injection in fetched web/PR/issue content.

**(a) Destructive action guard → sandbox and stop trying to classify.**
The strongest published result on this exact axis is AgentDojo's *tool filtering* (7.5% ASR) and CaMeL (0% ASR, provable) — both are policy/isolation mechanisms, not classifiers. An OS sandbox with filesystem+network restrictions (what Claude Code and OpenHands ship, and what our `guard` already gates on denylists) enforces *the actual thing we care about* — the process cannot touch what it shouldn't — with zero latency and no evasion surface beyond the kernel. Jev's value here is only the triage layer: an `noul` over "is this destructive command plausibly what the user asked for" to decide *whether to prompt*, not whether to run. That is a UX optimization, and its measured competitor is OpenHands' zero-extra-call `security_risk` self-report — a design Jev beats only if a second opinion demonstrably beats self-report, which no published benchmark establishes. Honest answer: keep Jev for this only if we can measure it beating confirmation-prompt fatigue, which is a UX metric, not an accuracy one.

**(b) Prompt injection screen on fetched content → a local DeBERTa-class classifier, not Jev.**
PINT gives the only neutral head-to-head: Lakera Guard 95.2 (hosted, paid) vs protectai DeBERTa v2 79.1 and PromptGuard 2 86M 78.8 — both free and local. For a laptop single-user harness, the ~16-point hosted premium does not survive the latency/privacy/availability trade, and neither survives adaptive attack anyway. The failure modes documented for ProtectAI (false positives on system prompts; blind to non-English and jailbreaks) suggest its correct role in our stack is a *cheap first screen on tool-result text only* (never the system prompt), with hits routed to confirmation — exactly the layered pattern LlamaFirewall formalized (cheap classifier → semantic auditor → stop), but with the layers swapped for cost.

**Where Jev / a hosted typed-judgment API is genuinely the right answer:**
- Questions a classifier cannot ask: `choice`/`score` over "given this tool call, this user request, and this last-8-messages context, is this consistent with the request?" — the AlignmentCheck shape. If we keep `stuck`/`route`/`screen` as trace-level *triage* (not per-call gates), Jev's state+typed-question form is the natural API for it, and the LlamaFirewall result (AlignmentCheck dropping ASR 17.6%→2.89% at −4.6% utility) is the closest published evidence that this class of judgment has real value — on an open benchmark, with the caveat that it was not tested against adaptive attacks and costs a large-model call per evaluation.
- Anything we want to *log and tune over time* with a stable schema (our JSONL logging) — no OSS guardrail ships a comparably ergonomic typed-question API over arbitrary state.

**Where it is the wrong tool, stated bluntly:** as the *primary* tool-call guard. No published evidence supports a hosted judgment API beating a local 86M classifier on detection, it adds a network round-trip into every tool call, its robustness under adaptive attack is unstudied, and the failure mode (silent false-negative with high confidence) is worse than a confirmation prompt's (annoyance). The category-wide adversarial evidence says detection-only defenses fold; structure and isolation don't.

## Gaps / not found

- **PIDS-Bench**: referenced in secondary coverage (beri.net) with a PromptGuard-2 F1 of 0.539 claim, but the primary paper/repo was not locatable on arXiv or GitHub as of 2026-09-22 (searched arXiv by title, GitHub by name). Treat that number as unverified secondary sourcing.
- **Jev / System One benchmark numbers**: no third-party evaluation of `jev-*` models on AgentDojo, PINT, InjecAgent, or any injection benchmark exists (searched: arXiv, GitHub, HuggingFace, Google). If Meta's or Lakera's numbers set the bar, Jev has no published evidence in this exact fight — its fit must be argued, not measured, today.
- **Devin's guard mechanism**: no primary technical documentation.
- **Codex runtime sandbox policy details**: the docs URL redirects to a product-marketing page; the actual sandbox policy surface (approvals matrix, network policy details) was not retrievable in this pass.
- **Latency for hosted guards** (Lakera, Azure Prompt Shield) per call in an agent loop: not published anywhere I could find; all latency figures above are for local models or LLM-as-judge patterns.
- **raucle-bench** is v0.1 with 165 prompts and mostly self-authored adapters (its own `raucle-detect` is the most-represented detector); it is a start, not a referee yet.