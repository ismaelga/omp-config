---
name: diverge-converge
description: >-
  Use when one problem has several defensible answers and the first plausible one would
  otherwise win by default — a review that matters, a bug whose right fix depth is unclear,
  a design with no obvious shape. Not for independent tasks that merely run at the same
  time (that is dispatching-parallel-agents).
---

# Diverge Then Converge

## Overview

Send several agents at the **same** problem with **different aims**, then synthesize on the
main thread. Different aims route through different reasoning. The payload is where they
disagree.

Distinct from `dispatching-parallel-agents`: that maps one agent per *independent* problem.
Here every agent gets the *identical* problem and a different lens. Redundancy is the point.

## Gate — all three must hold

1. The decision is load-bearing (it ships, or it costs real rework if wrong).
2. More than one answer is defensible.
3. Left alone you would accept the first plausible answer.

Any one missing → one agent, no fanout. Three lenses cost ~3× input tokens on the same
problem, and ollama-cloud does no prompt caching, so every lens re-bills its whole transcript.

## Two kinds of divergence

| Goal | Diverge by | How |
|---|---|---|
| **Generate** options (fixes, designs) | aim | one agent file, spawned N× with different briefs |
| **Catch misses** (review, audit) | model family | distinct agent files pinned to distinct families |

Same-family critics share blind spots — that is why `cavecrew-challenger` is pinned off
`cavecrew-reviewer`'s family. For generation, aim alone separates the outputs; paying for
family diversity there buys little.

`task` has no per-item model field, so cross-family divergence means distinct agent files.
Aim divergence needs only distinct briefs.

## Blind-parallel vs anchored

- **Blind parallel** (this skill) — lenses never see each other. No anchoring, real
  independence, some redundant findings.
- **Anchored** — the second agent reads the first's report (`cavecrew-challenger`; `momus`
  after a plan). Sharper on misses, inherits framing.

Multi-axis judgment → blind parallel. Verifying one existing report → anchored. On work that
really matters: diverge blind, converge, then challenge the converged output.

## Lens sets

**Review** — one batch, three families:

| Lens | Agent |
|---|---|
| correctness | `cavecrew-reviewer` |
| security | `cavecrew-sentinel` |
| simplicity | `cavecrew-simplifier` |
| design fidelity (UI diffs only) | `designer` — compare the result against what was asked |

**Bug fix** — `cavecrew-fixscout` 3×, `aim: simple` / `thorough` / `creative`. Establish the
repro and cause first with `cavecrew-debugger`; fixscout proposes depth, it does not hunt.

**Design variants** — `designer` 3×: minimal (essentials only) / bold (opinionated) /
unexpected (rethinks the approach). Each writes standalone HTML to
`.omo/variants/<slug>/<aim>.html`. Designs must be seen, not summarized.

## Converge — on the main thread

Converge is synthesis and taste. It stays with you; a subagent that never saw the conversation
cannot weigh it.

The converged output IS these parts, in this order:

1. **CONFLICTS** — every point where lenses disagree: both positions, which one holds, the
   evidence. This section is the reason you diverged.
2. **IMPORTANT** — `<item> — [lens] — <why it matters>`. Tag `[all]` when every lens raised
   it; that is your highest-confidence item.
3. **NICE-TO-HAVE**
4. **NITS**
5. **RECOMMENDATION** — one paragraph, exactly one course of action. Often a combination of
   two lenses; say which parts, from which.

Empty sections are omitted. Every item is attributed to its lens.

## Common mistakes

**Concatenation dressed as synthesis.** Three reports pasted under three headings is not a
converge. No dedupe and no named conflict means you skipped the step that creates the value.

**Recommending everything.** Three lenses produce three plans. Picking all three is picking
none.

**Diverging on a settled problem.** If lens two and lens three restate lens one, the gate was
wrong, not the lenses.

**Lenses that peek.** Handing lens B lens A's output makes it anchored, not divergent. Feed
every lens the identical brief in one batch.

**Delegating the converge.** See above.
