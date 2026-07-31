---
name: cost-aware-coding
description: Use when building features that involve LLM calls, agent loops, vector databases, or any per-request infrastructure - track cost as a first-class metric alongside correctness and latency, before it becomes a surprise on the invoice. In 2026, naive LLM-driven features can 100x their cost overnight; tracking it during development is the only safe path.
---

# Cost-Aware Coding

> "If you don't know what your call costs, you don't have a product, you have a science experiment running on someone else's credit card." — common 2026 wisdom (sources: Augment, Anthropic engineering, multiple postmortems)

## Why this skill exists in 2026

The cost profile of agent-driven software is wildly non-linear and easy to ignore at design time.

Examples of what's killed startups in 2026:
- A "smart retry" loop on a $25/MTok model that triggered 50 times per failed request
- An agent that re-read the same 200K-token codebase on every step for 8 hours
- A vector embedding pipeline that re-embedded unchanged docs nightly
- A "thinking" model variant left at `xhigh` in production for a feature that worked fine at `medium`
- A naive RAG that pulled 50 documents per query when 5 would do

In every case, the bug was visible at design time. Nobody looked.

## The discipline

Make cost visible **during development**, not after the bill arrives.

Cost is a metric like latency. You wouldn't ship a feature without knowing its latency. Same standard for cost.

## The 5-step pattern

### 1. Cost a single call before scaling

Before writing the loop, the orchestrator, or the batch job — compute the cost of ONE call. Use the actual model, actual prompt, actual expected output length. Multiply by expected daily volume.

If the answer surprises you, redesign before building.

### 2. Set explicit budgets

For every feature involving LLM/agent calls, decide upfront:
- Cost per user action: target $X
- Cost per day at expected scale: target $Y
- Hard kill switch if either exceeds: 5x target

These go in the plan. They're not aspirational. They're constraints.

### 3. Track cost in the eval

Your eval already tracks accuracy and latency (see `eval-driven-development`). Add cost as a column. Now when you swap models or prompts, you see the full tradeoff matrix.

A model that's 2% more accurate but 10x more expensive is rarely the right choice.

### 4. Cache aggressively

Three layers, in order of leverage:
- **Prompt caching**: Anthropic/OpenAI/etc. all offer it. Hit the cache aggressively. Cached input is ~10% of uncached cost.
- **Result caching**: if the same query is likely to repeat, cache the result. Even crude TTL caching saves dramatically.
- **Embedding caching**: never re-embed unchanged content. Hash inputs, store outputs.

The Karpathy point: cached frontier model input is often cheaper than uncached cheap-model input. The right routing isn't always "cheaper model."

### 5. Right-size the variant

Variants (`low`/`medium`/`high`/`max`/`xhigh`) compound cost. A `max` variant on every Hephaestus call is rarely justified.

For each agent/category, ask: "what's the lowest variant that still passes the eval?" That's the right setting. Anything higher is paying for capability you're not using.

## Common cost patterns to audit

### The runaway loop
- Symptom: an agent gets stuck and keeps calling the same tool with slight variations
- Watch: number of tool calls per task; alert if >50 without progress
- Mitigation: `circuitBreaker` on tool call count (you have this configured)

### The bloated context
- Symptom: the agent has 100k tokens of stale tool output before every reasoning step
- Watch: input token count per call; should plateau, not grow linearly
- Mitigation: `context-curation` skill + dynamic_context_pruning

### The wrong-variant default
- Symptom: every category set to `max` or `xhigh` "to be safe"
- Watch: spec-by-spec cost on the eval
- Mitigation: tune variants down until the eval starts regressing, then back up one notch

### The chatty subagent
- Symptom: subagents spawn freely, each starting with a fresh context
- Watch: total subagent invocations per task
- Mitigation: `max_parallel_members` limit (you have 4), `maxDepth` (you have 3)

### The over-frequent embedding
- Symptom: re-embedding content that hasn't changed
- Watch: embedding API calls per indexable item per day
- Mitigation: content-hash based caching, only embed deltas

## The single number everyone should know

For any feature involving LLM calls, you should know:

**Cost per user-meaningful action**

Not cost per API call. Not cost per token. Cost per *thing the user wanted*. If a user asks a question and your system makes 12 LLM calls to answer, that's one user action and 12 calls — track the total cost per question.

If you can't quote this number, you don't have cost awareness. Quote it.

## Anti-patterns

- **"We'll optimize later."** Cost compounds. Optimization at month 6 is 100x harder than at week 1.
- **"It's only X dollars in test."** Multiply by daily prod volume. Multiply by 30 days. Multiply by retries. Multiply by the year you're going to be wrong about something.
- **"The cheapest model is fine."** Sometimes. Often not. Use the eval to decide, not vibes.
- **"Caching is premature optimization."** No. It's the default. Justify NOT caching.
- **"Costs will go down."** They will. But your usage will go up faster. Design for current prices.

## Karpathy connection

Karpathy has been a steady voice on "compute is the bottleneck." In the LLM era this translates directly: tokens × dollars × calls × users = your bill. Each multiplier compounds. Catch each one early.

## Integration

- **`eval-driven-development`** → Cost is a column in the eval table
- **`baseline-first`** → Baseline cost is a key data point; if baseline already meets budget, you're done
- **`pre-mortem`** → "Cost spike" is a failure mode to enumerate
- **`context-curation`** → Direct cost lever; less context = less input tokens
- **`background_task.circuitBreaker`** (your config) → Hard ceiling against runaway loops

## Single-number test

> *"How much does my feature cost per user-meaningful action, right now?"*

If you can't answer in dollars and cents → measure before continuing.
