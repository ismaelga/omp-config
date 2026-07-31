---
name: pre-mortem
description: Use before kicking off any non-trivial feature, migration, refactor, or deployment - imagine the work has already failed catastrophically and work backwards to figure out why, surfacing risks while they're cheap to mitigate. Inverts the usual planning lens from "how will this succeed" to "how will this fail".
---

# Pre-Mortem

> "Imagine that we are a year into the future. We implemented the plan as it now exists. The outcome was a disaster. Please take five to ten minutes to write a brief history of that disaster." — Gary Klein (popularized by Kahneman in *Thinking, Fast and Slow*)

## Why this skill

Standard planning asks "how will this succeed?" — which biases toward optimistic execution paths and blind spots.

Pre-mortem inverts the question: "we shipped this. It was a disaster. What happened?"

This single reframe surfaces 5-10x more risks than the same engineers asked "what could go wrong?" — because it gives them permission to imagine failure concretely rather than dismissing it as pessimism.

## When to run a pre-mortem

- Before any feature touching auth, payments, data deletion, or external systems
- Before any non-reversible migration (DB schema, file format, deployment topology)
- Before any "big rewrite" or "we'll just refactor X"
- Before launching to real users (especially internal tools that "feel safe")
- Before agreeing to an estimate that feels too aggressive
- Before merging a PR that touches >10 files OR critical paths

## The 7-step protocol

### 1. Frame the failure (1 minute)

State the plan in one sentence. Then state the failure scenario:

> *"It is 3 months from now. We shipped [the feature]. It went badly. We are doing a postmortem. Walk me through what happened."*

### 2. Brainstorm failure modes — generative phase (5 min)

List failure modes without filtering. Be specific. Bad: "performance issues." Good: "the migration locks the users table for 8 minutes, login outage during NA business hours."

Aim for 10+ specific failure scenarios. Quantity over quality at this stage.

Categories to probe:
- **Correctness**: wrong output, edge cases, off-by-one
- **Reliability**: crashes, timeouts, race conditions
- **Performance**: latency, throughput, resource exhaustion
- **Security**: auth bypass, injection, data leakage
- **Data**: corruption, loss, schema drift
- **Operational**: deployment failures, rollback impossibility, alerting gaps
- **Human**: misunderstanding the requirement, scope creep, key person leaves
- **Integration**: upstream/downstream contract breaks, version skew
- **Cost**: blown budget, runaway autoscaling, expensive bug-induced loops

### 3. Probability × impact — filter phase (3 min)

For each failure mode, score:
- Probability: low / medium / high
- Impact if it happens: low / medium / catastrophic

Focus only on medium-or-higher probability **AND** medium-or-higher impact. Discard the rest.

### 4. Identify leading indicators

For each remaining failure mode, what would you see *before* the failure that would warn you? These become your monitoring/checkpoint signals.

E.g., "users table migration locks for 8 minutes" → leading indicator: "migration on staging runs >2 minutes on similarly-sized data."

### 5. Decide mitigations

For each top failure mode, pick ONE of:
- **Prevent**: design change that makes the failure impossible
- **Detect**: monitoring/alert that catches it early
- **Mitigate**: fallback that limits blast radius
- **Accept**: explicit risk acceptance (with name attached)

"Accept" is a real option. Don't pretend to mitigate everything.

### 6. Update the plan

The mitigations become work items in the plan. The plan is now stronger by construction.

### 7. Save the pre-mortem

Write it down. Even one bullet per failure mode. When something goes wrong (and something will), you'll want to know if you saw it coming.

## What good output looks like

A pre-mortem document with:
- The plan being analyzed
- 10+ specific failure modes
- 3-5 prioritized risks with mitigations
- 2-3 leading indicators to monitor
- 1-2 explicit risk acceptances if any
- Timestamp and who participated

Total length: 1-2 pages. Total time: 15-30 minutes for a meaningful project.

## Anti-patterns

- **Skipping it for "small" changes.** Small changes break production all the time.
- **Vague failure modes.** "Things could go wrong" is not a failure mode.
- **Solving everything.** Mitigating every risk is impossible; explicit acceptance is part of the discipline.
- **One-person pre-mortem.** Diversity of perspective is the whole point. If solo, at least run it through a critic agent.
- **Pre-mortem at the end.** The point is to surface risks *while they're cheap to mitigate* — design phase, not after implementation.

## Karpathy connection

Karpathy's repeated emphasis: "the failure modes of LLM systems are non-obvious and accumulate silently." Pre-mortem is the discipline that drags those silent accumulators into daylight before they bite.

## Integration

- **`brainstorming`** → Brainstorming opens the design space. Pre-mortem stress-tests the chosen point.
- **`writing-plans`** → Pre-mortem output goes into the plan as mitigations.
- **`hyperplan`** (oh-my-openagent) → The 5 hostile critics are doing pre-mortem in parallel.
- **`eval-driven-development`** → Failure modes inform what the eval needs to catch.

## Single-question test

> *"What's the most embarrassing way this could fail, and have I mitigated it?"*

If you can't answer in concrete detail → run the pre-mortem.
