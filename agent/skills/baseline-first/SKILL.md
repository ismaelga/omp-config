---
name: baseline-first
description: "Use before building any non-trivial feature, optimization, or smart system: establish the dumbest solution as the baseline first."
---

# Baseline-First

> "Always run the dumbest possible thing first. You'll be surprised how often it works, and when it doesn't, the gap tells you exactly what to build next." — Andrej Karpathy (paraphrasing his repeated advice on building ML systems and agentic features)

## The principle

The most common bug in AI-assisted development is solving problems that don't exist.

The pattern:
1. Hear feature request
2. Imagine the elegant, scalable, well-architected solution
3. Build it
4. Discover the original problem was solved by `if/else` and 20 lines

**The fix:** always start with the dumb solution. Measure. Add complexity only when measurement justifies it.

## When this applies

- Adding caching ("the API is slow") → first measure: is it actually slow?
- Adding retry logic ("the API is flaky") → first measure: how often does it actually fail?
- Adding a queue ("requests pile up") → first measure: do they?
- Adding RAG ("the model doesn't know our docs") → first try: just paste the docs in
- Adding fine-tuning ("the prompts are too long") → first try: shorter prompts
- Adding a state machine ("the flow is complex") → first try: nested if/else
- Adding an abstraction layer ("we might need to swap X") → first try: don't
- Building a custom orchestrator ("agents need to coordinate") → first try: one agent
- Building a custom embedding store ("we need fast retrieval") → first try: linear scan + cache

## The discipline

For any non-trivial feature, before writing the planned solution:

### Step 1: Write the baseline

The baseline is the dumbest thing that could possibly work for the demo case.

- Single function, hardcoded values, no error handling, no edge cases
- Synchronous if possible, blocking is fine
- No abstractions, no configurability, no extensibility
- "If a junior dev had to ship in 30 minutes" energy

### Step 2: Measure on your eval

Run the baseline against your real measurement — a test suite, a scored sample set, or a perf/cost
benchmark. Run the scoring loop in the `eval` kernel (persistent Python/JS, so the baseline's
numbers stay live across cells while you iterate on the smart version); when the thing being
measured must run as a server, launch it with `hub start {name, application, args, ready:{log, port}}`
and point `eval` at that port. A baseline measured by a backgrounded `bash` job you then have to
babysit is the failure this avoids. Record:
- Accuracy / correctness
- Latency
- Cost
- Failure modes (which inputs broke it)

### Step 3: Decide

Look at the baseline number vs. the requirement.

| Baseline result | Decision |
|---|---|
| Meets requirement | **Ship the baseline.** Add nothing. The "real" solution was imaginary complexity. |
| Misses by a little | Try ONE incremental improvement. Re-measure. |
| Misses by a lot | The gap tells you what to build. Build the minimum to close it. |
| Fails catastrophically | The problem may be harder than you thought. Re-scope. |

### Step 4: Justify every layer added on top

For each layer of complexity beyond baseline, you need a measurement that justifies it. "It might be useful later" doesn't count.

## Concrete examples from Karpathy's playbook

**Building a chat bot:**
- Baseline: one LLM call with a hardcoded system prompt
- Often sufficient. If not, gap reveals: needs memory? needs tools? needs retrieval?

**Building an agent that fixes bugs:**
- Baseline: send the error + the file to the LLM, apply the diff it returns
- Often sufficient for simple bugs. If not, gap reveals: needs to read related files? needs to run tests? needs to iterate?

**Building a code search system:**
- Baseline: ripgrep
- Often sufficient. If not, gap reveals: needs semantic search? cross-language? AST-aware?

**Building a recommendation system:**
- Baseline: "most popular in last 7 days"
- Often within 5% of the fancy solution. If not, gap reveals: needs personalization? freshness? diversity?

## Anti-patterns to reject

- **"That's too simple."** Simple isn't bad. Wrong is bad. Measure first.
- **"We'll need X eventually."** Build X when you actually need it. YAGNI is real.
- **"The senior engineer would build it the smart way."** The senior engineer builds the dumb way first BECAUSE they're senior.
- **"It's not impressive enough to demo."** The demo is whether it works, not whether it's elegant.
- **"We need to think about scale."** Build for 1x. Refactor at 10x. Rebuild at 100x.

## The hard part

The hard part is psychological. The baseline feels embarrassing. You imagine your colleagues judging it.

In practice, your colleagues judge you for:
- Wasting two weeks building something that hardcoding would have solved
- Adding a dependency, abstraction, or service that doesn't earn its complexity
- Optimizing the wrong thing
- Shipping late

Nobody judges you for shipping the baseline that works.

## Integration with other skills

- **`brainstorming`** → Should explicitly include "what's the dumbest version?"
- **`writing-plans`** → Plan should start with baseline step before "smart" steps
- **`code-review`** → Slop is often a skipped baseline plus over-engineering; the review catches it

## Single-sentence test

> *"Did I measure the dumbest possible solution before building this one?"*

If no → stop. Build the dumb one. Measure. Then decide if you still need the smart one.
If yes → continue, with the baseline number in hand as your reference point.
