# Design It Twice

When the user wants to explore alternative interfaces for a chosen deepening candidate, use this parallel sub-agent pattern. Based on "Design It Twice" (Ousterhout): your first idea is unlikely to be the best.

Uses the vocabulary in [SKILL.md](SKILL.md): **module**, **interface**, **seam**, **adapter**, **leverage**.

## Process

### 1. Frame the problem space

Before spawning sub-agents, write a user-facing explanation of the problem space for the chosen candidate:

- The constraints any new interface would need to satisfy
- The dependencies it would rely on, and which category they fall into (see [DEEPENING.md](DEEPENING.md))
- A rough illustrative code sketch to ground the constraints, not a proposal, just a way to make the constraints concrete

Show this to the user, then immediately proceed to Step 2. The user reads and thinks while the sub-agents work in parallel.

### 2. Spawn sub-agents

One batched `task` call with 3+ items (agent: `task`), one per design
constraint, so the designs come back comparable instead of as free-form
transcripts:

```
task(context: "<the technical brief below>", tasks: [
  {name: "DesignMinimal",  task: "Design constraint: minimize the interface — 1-3 entry points max, maximize leverage per entry point"},
  {name: "DesignFlexible", task: "Design constraint: maximize flexibility — support many use cases and extension"},
  {name: "DesignCaller",   task: "Design constraint: optimize for the most common caller — make the default case trivial"},
  {name: "DesignAdapters", task: "Design constraint: ports & adapters for cross-seam dependencies"}  // if applicable
])
```

Each dispatch carries an `outputSchema` so the results arrive validated and
side by side:

```
outputSchema: {
  "interface": "types, methods, params, plus invariants, ordering, error modes",
  "usage": "example showing how callers use it",
  "hiddenImplementation": "what the implementation hides behind the seam",
  "dependencyStrategy": "dependency strategy and adapters",
  "tradeoffs": "where leverage is high, where it's thin"
}
```

Prompt each sub-agent with the shared technical brief in `context` (file
paths, coupling details, dependency category from [DEEPENING.md](DEEPENING.md),
what sits behind the seam — independent of the user-facing problem-space
explanation in Step 1); the per-item design constraints are the four shown
above. Include both [SKILL.md](SKILL.md) vocabulary and CONTEXT.md
vocabulary in the brief so each sub-agent names things consistently with
the architecture language and the project's domain language. The
`outputSchema` fields above ARE the five-part answer — the designs return
as structured data, not prose transcripts.

### 3. Present and compare

Present designs sequentially so the user can absorb each one, then compare them in prose. Contrast by **depth** (leverage at the interface), **locality** (where change concentrates), and **seam placement**.

After comparing, give your own recommendation: which design you think is strongest and why. If elements from different designs would combine well, propose a hybrid. Be opinionated: the user wants a strong read, not a menu.

For the converge step — which design to keep when several defensible answers
remain — see `skill://diverge-converge`; this file does not duplicate it.
