---
name: reviewing-model-pins
description: Use when reviewing, re-pinning, or auditing which model each omp role uses — triggered by "review model choices", "check newer models", "check benchmarks", a new model release, a price change, a role feeling slow or wrong, or a fallback chain that may have gone stale.
---

# Reviewing Model Pins

## Overview

A model pin is a claim about the world that decays: models ship, prices move, promos
end, routes 410, vendors reroute old ids to new weights. This review re-derives each
pin against today's evidence.

**Core principle: a pin changes only on evidence produced in this pass.** Recalled
knowledge, a vendor blog, and a catalog index field are inputs to a *candidate*, never
to a *change*.

## Evidence classes

Every recommendation carries a class. The class decides what the recommendation is
allowed to be.

| Class | What it is | Sufficient to re-pin? |
|---|---|---|
| **M** — measured here | bakeoff execution, `omp bench`, raw `curl` wire timing, `model_perf` with n≥50 *and* a fresh `updated_at` | Yes |
| **L** — leaderboard read today | Artificial Analysis, OpenRouter rankings; effort tier recorded | Yes, for quality ordering only |
| **V** — vendor fact | release date, model id spelling, list price, plan availability, modality, deprecation notice | Yes, for facts. Never for quality ordering |
| **C** — bundled catalog | `omp models` rows: context, output cap, effort ladder, image input | Yes, for capability facts. Never for quality ordering — `int`/`tps` fields are unaudited vendor numbers |

A candidate with only V or C quality evidence is a **watch item**, not a re-pin. Write
it down as a watch item and move on.

## Procedure

Run all six. Steps 1 and 3 are the ones that get skipped and the ones that find the
real news.

1. **Provider health (REQUIRED, first).** A pin on a provider that cannot answer is
   worse than a weaker pin that can, and quota state is invisible in every catalog.
   Run `omp usage` and read the credit balance of each metered key. Any provider that
   is out of credit, out of quota, or entitlement-blocked is a finding that outranks
   every quality delta in the rest of the pass: its roles are already falling through
   their chains, and its links have to move behind routes that answer.

2. **Inventory.** `omp models refresh`, then read `modelRoles`, `modelProviderOrder`,
   `retry.fallbackChains` in `~/.omp/agent/config.yml` and the overrides in
   `models.yml`. Diff catalog against pins: what exists now that did not exist at the
   last pass, and what the pins name that the catalog no longer carries.

3. **Claim re-check (REQUIRED).** Every pin comment in `config.yml` carries a dated
   number and often an explicit exit condition ("revert when the discount ends").
   Re-check each one. A stale claim is a finding even when the pin does not move, and
   an exit condition whose trigger has fired is a re-pin with the evidence already
   written down. Local claims re-check against `model_perf`; price claims against a
   live provider call.

4. **Candidates.** For each role, name the newest plausible model reachable on an
   authenticated provider. Research vendor facts via `web_search` with `site:`-scoped
   queries (id spelling per provider, release date, price, plan reachability, modality,
   deprecation/reroute notices) and `read <vendor notice url>`; read one leaderboard
   directly, recording the effort tier each score was measured at. For local measured
   evidence, `read agent.db:model_perf?q=SELECT … model_key, samples, ttft_samples,
   updated_at …` with a freshness filter on `updated_at`.

5. **Measure only the contested ones.** Most roles are decided by sources plus a wire
   probe, and running a bakeoff for them is wasted wall time: context, price,
   modality, id spelling and deprecation are V/C facts, and quality *ordering* is what
   the leaderboard is for. One thing an index cannot decide: whether a model reliably
   *emits working code*. DeepSeek V4-Flash looked fine on every index and returned
   nothing on 4 of 4 bakeoff calls. So the bakeoff is REQUIRED exactly when the
   criterion is coding correctness (`task`), and OPTIONAL everywhere else. A pin whose
   criterion is latency needs `omp bench` or curl, not a bakeoff. See `commands.md`.
   Verify the validator against a reference implementation before scoring any model.

   **Derive wall-clock, never read it off.** A leaderboard's tok/s is a rate on the
   vendor's own API; what a role waits for is tokens-emitted ÷ rate, on *your* route.
   AA publishes both halves (`Output tokens per second`, `Output tokens from
   Intelligence Index`). Read 2026-09-11: DeepSeek V4.1-Flash 197.4 tok/s but 250M
   tokens, GLM-5.3-Flash 89.9 tok/s and 180M, GLM-5.3 59.8 and 210M — so on paper
   V4.1-Flash finishes a task in 63% of GLM-5.3-Flash's time. On ollama-cloud the
   same three answered the same prompts in 117–140 s / 24–37K tokens against
   62–68 s / 4.7–6.2K, i.e. the reverse. Both numbers are true; only the second one is
   about this machine.

6. **Apply and verify.** Edit pins, chain heads, and chain links together — a re-pin
   that leaves the old chain head in place makes the chain dead config. Then verify
   the new selector resolves to the provider you intended, and that every link in the
   touched chains is live and keeps the modality the role needs.

## Output shape

Two artifacts. Both REQUIRED.

**A recommendation table**, one row per role, every column filled:

| Role | From | To (or KEEP) | Criterion | Evidence | Class |
|---|---|---|---|---|---|

`Criterion` is what this role is bottlenecked on (below). `Evidence` is the number and
its date and sample count. `Class` is M/L/V/C. A row with class V or C in the Evidence
column and a non-KEEP value in `To` is invalid — downgrade it to a watch item.

**A claim re-check table** from step 2:

| Config claim (with its date) | Still true? | Evidence today |
|---|---|---|

**Config comments carry provenance.** Every number written into `config.yml` names its
source and date, so the next pass can re-derive it: `omp bench --profile chat (5 runs,
256-token cap, 2026-09-01)`. A number without provenance is a number nobody can
re-check.

## Role criteria

Ranking every role by one intelligence index is the mistake this table prevents.

| Role | Bottleneck | Ranked by |
|---|---|---|
| `default`, `plan`, `slow` | correctness on long-horizon work | quality first, latency second |
| `task`, `scout` | wall-clock across 8–32 concurrent subagents | execution-scored quality at $0 marginal, then output tok/s |
| `tiny`, `smol`, `commit` | TTFT — a human waits on these | TTFT, then tok/s, then format adherence |
| `vision` | the modality must actually exist | verified input modalities |
| `critic`, `sentinel` | precision; false alarms get the reviewer ignored | defect detection at low false-positive rate |
| `advisor` | uncached **input** tokens, not reasoning | input $/Mtok + cache-read + prefill speed |

## Standing rules

- **Reachability outranks quality.** Check what answers before comparing what is
  smart. A 402, a spent weekly quota, or an entitlement block turns the best pin in
  the file into a chain walk.
- **Flat plans win high-volume roles.** `anthropic`, `openai-codex`, `zai` and
  `opencode-go` are plan-based here (`opencode-go` bills against 5-hour/weekly/monthly
  caps, not per token) and `ollama-cloud` is $0 marginal; `openrouter` is the one
  genuinely metered key. Metered spend must buy something the plans cannot — a
  modality, a context window, a capability.
- **Probe the modality, never trust the field — and never with a toy image.** Before a
  role that sends images lands on a route, post a real image to that exact provider and
  model and read the answer. Use at least 64x64 of a solid, unambiguous colour, and
  probe two different colours so a lucky guess cannot pass: Kimi K3 called a 2x2 red
  PNG "Black" and answered "Red"/"Blue" correctly at 64x64 (2026-09-11). The catalog's
  `input` list is vendor metadata; two correct answers are evidence.
- **Pin the effort tier.** With `providers.autoThinkingMaxEffort: max`, any bare
  selector can be classified into the top tier, which reliably buys latency rather
  than correctness. `ultrathink` still reaches `max` on demand.
- **Chain hygiene.** Same weights on cheaper providers first; every link keeps the
  modality the role needs; the tail must not silently downgrade the role that
  overflowed into it; metered providers last.
- **Verbosity is a latency cost.** Tokens-per-second times tokens-emitted is what the
  user waits for. A terser model at lower tok/s can finish first.
- **Never derive route latency from `omp -p`.** CLI startup dominates. Use `omp bench`
  or curl.
- **google-antigravity is refused on terms grounds**, not missing. Do not re-add it.

- "I could not verify the price / the quota / the route" → one call settles it. `read
  https://openrouter.ai/api/v1/models` for prices, `omp usage` for quota; keep curl
  only for latency probes, where the timing is the measurement.

- "I did not run anything, but the index is higher" → that is a watch item, not a re-pin.
- "I could not verify the price / the quota / the route" → one curl settles it. Run it.
- Quoting `int` or `tps` out of `omp models` as if it were measured.
- Recommending a swap while leaving the old id as a fallback chain key.
- Re-pinning a role without checking whether the old model's vendor has rerouted it.
- A dated claim in the config that this pass neither re-checked nor cited.
- Comparing today's leaderboard number against a number in a comment without checking
  whether the index was rescaled between the two reads.
- Concluding a route is dead, or alive, from `omp bench` alone.

## Reference

- `commands.md` — runnable verification commands: catalog, price, latency, perf,
  link audit, config validation, bakeoff harness shape.
- `traps.md` — known failure modes, each as symptom → cause → detection.
- `~/.omp/.omo/research/model-selection/` — prior decision docs; `00-decision.md` holds
  the role-bottleneck reasoning and the advisor economics.
