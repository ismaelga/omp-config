---
name: minimum-viable-reimplementation
description: Use when stuck on a library bug, a framework abstraction is misbehaving, or you genuinely don't understand why some external code is doing what it's doing - rewrite the broken piece from scratch in 50-200 lines to isolate the issue and build a real mental model. Faster than reading 10k lines of library code. Inspired by Karpathy's nanoGPT/nanochat pedagogy.
---

# Minimum Viable Reimplementation

> "When you don't understand something, rewriting it from scratch is often faster than reading the existing implementation. The result is also more debuggable." — Andrej Karpathy (nanoGPT / nanochat pedagogy)

## When to reach for this

This is a power tool with narrow but high-value use cases. Use it when:

- A library is doing something unexpected and you've already spent 30+ minutes reading its source
- A framework abstraction is leaking and the fix isn't obvious from the docs
- Performance debugging where the suspected code is buried in vendor code
- You need to predict what the library will do in an edge case the docs don't cover
- You're going to use this thing every day for years and don't actually understand it

Do NOT use it for:
- Bugs in your own code (just fix the bug)
- Libraries you'll use briefly (read the docs, file an issue, move on)
- Production systems (this is a learning/debugging exercise, not a deployment plan)
- "Just because" — it's expensive in time

## The discipline

### Step 1: Set the budget

Decide upfront: 50 lines? 200? 500? If you can't do it in the budget, the abstraction is irreducible — abandon the exercise, file an issue, work around it.

Karpathy's nanoGPT is ~300 lines reimplementing transformer training. Most things you're debugging are much simpler than transformers.

### Step 2: Identify the minimum interface

What's the smallest API surface you need? If the library has 50 methods and you use 3, your reimplementation only needs the 3. Strip ruthlessly.

### Step 3: Write the dumbest possible version

- Synchronous, blocking, no error handling
- One file, no abstractions
- Hardcoded everything you can hardcode
- Match the input/output shape exactly so it's a drop-in for testing

### Step 4: Run your mini-version against the same inputs

Now you have two implementations:
- **Theirs**: the black box you don't understand
- **Yours**: 50-200 lines you wrote and understand completely

Run both. Compare outputs. The divergence is exactly where your mental model differs from reality. That's your bug.

### Step 5: Decide what to do

| Outcome | Action |
|---|---|
| Outputs match | You now understand. Use their version. Document the insight. |
| Outputs differ, theirs is right | You found your wrong assumption. Update your model. Use their version. |
| Outputs differ, yours is right | You found their bug. File an issue or PR. Use yours until fixed. |
| Outputs differ, both wrong | The problem is harder than you thought. New plan. |

## Concrete examples

**"Why is this async iterator never finishing?"**
- 30 min of reading their async helpers: no insight
- 60 min reimplementing a basic async iterator: discover they're awaiting `Promise.all` on an unbounded stream → infinite hang
- Their bug. Your understanding is now correct.

**"Why does my embedding similarity look wrong?"**
- 45 min reading their vector library: too generic to debug
- 30 min implementing cosine similarity from scratch: 12 lines
- Discover their library normalizes when you didn't expect it
- Now you understand their normalization model. Use it correctly going forward.

**"Why is JSON serialization weird here?"**
- Reimplement the relevant fragment of their serializer in 40 lines
- Run on the same input
- Output differs in handling of `undefined` vs `null`
- That's their model. Now you know.

## The pedagogy advantage

Even if it takes 2 hours, you walk away with:
- A clear mental model of how the library actually works (not just what it does)
- Code you can show to a junior engineer to explain the concept
- A debug tool that lives in your toolbox forever
- Confidence to use the real library aggressively

Karpathy's full thesis: rebuilding deepens understanding more than reading. This works for libraries, frameworks, protocols, algorithms, and even product features.

## Anti-patterns

- **Over-engineering the mini-version.** It's a debugging tool, not a library. 50-200 lines.
- **Using it for everything.** Most bugs aren't in dependencies. Most are yours. Check yours first.
- **Shipping the mini-version.** It's a learning artifact. Use the real library in production unless you found a real bug.
- **Spending all day on it.** Set the time budget. Honor it.

## Integration with other skills

- **`systematic-debugging`** → Use this when standard debugging hits a wall against external code
- **`baseline-first`** → Related principle: simplest version first reveals more than elaborate analysis
- **`context-curation`** → After the exercise, summarize the insight and prune the exploration trail

## Quick test

> *"Have I spent more than 30 minutes reading code without making progress on understanding?"*

If yes → consider this skill. The reimplementation might be faster than continued reading.
If no → keep reading. Reimplementation has overhead; don't reach for it prematurely.
