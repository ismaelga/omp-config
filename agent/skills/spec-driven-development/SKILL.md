---
name: spec-driven-development
description: Use for non-trivial features where the brainstorming has produced shape but the implementation isn't obvious - chains brainstorming → spec → tests → implementation as a single coherent pipeline rather than three disconnected activities. The spec is the artifact that bridges intent and code.
---

# Spec-Driven Development

> "A clear specification is more valuable than a thousand lines of code. If you can't write the spec, the code you're about to write is a guess." — engineering folklore, repeated by everyone from Karpathy to DHH

## What "spec" means here

Not a formal IEEE document. A spec is:
- A few hundred words of plain English
- Describes what the feature does, not how
- Includes inputs, outputs, edge cases, success criteria
- Could be handed to a different engineer who'd produce essentially the same code
- Could be handed to QA who'd produce essentially the same tests

If your description doesn't meet those criteria, it's not a spec yet.

## Why this skill

The common failure mode of AI-assisted development:

1. Brainstorm → produces vague ideas
2. Jump to code → AI writes plausible-looking implementation
3. Tests pass → ship
4. Production reveals the AI guessed at the parts you didn't specify

The fix: insert a spec between brainstorming and code. The spec forces the ambiguity out into the open where you can resolve it before commit.

## The 5-phase pipeline

### Phase 1: Brainstorm (open mode)

Use `superpowers/brainstorming`. Output: a high-level idea of what to build and why.

### Phase 2: Spec (constrained mode)

Take the brainstorming output and convert it to a concrete spec. A good spec has:

**Header**:
- Feature name
- 1-sentence purpose statement
- Why now / what changes if we don't

**Behavior**:
- Inputs: what does it receive, in what shape?
- Outputs: what does it produce, in what shape?
- Side effects: what does it change about the world?

**Edge cases** (the most important section):
- What happens when input is empty?
- What happens when an external dependency is unavailable?
- What happens when called twice in parallel?
- What happens when called with malformed data?
- What's the worst case latency / size / cost?

**Success criteria** (the eval, in plain English):
- How will we know this works correctly?
- How will we know it's broken?
- Concrete: "an HTTP 500 from the user service should not block account creation, but it should be logged with severity=warn"

**Non-goals**:
- What is this NOT trying to solve?
- What should it explicitly fail to do?

**Open questions**:
- List everything ambiguous
- Each one needs a decision before code starts

### Phase 3: Test scaffold (mechanical conversion)

The spec's behavior + edge cases section converts almost mechanically into test cases. Write the test names (and probably the test bodies) from the spec, before any implementation.

This is also where `eval-driven-development` plugs in if the feature is agentic.

### Phase 4: Implementation (the easy part)

With spec + tests in hand, implementation is the most mechanical part of the work. The AI excels here. You vibe-code with `vibe-coding-guardrails` on, because the spec gives you a clear lens to evaluate the diff against.

### Phase 5: Spec-vs-code reconciliation

Before declaring done:
- Does the code match the spec?
- Did you discover anything during implementation that requires a spec update?
- Are all "open questions" from the spec resolved in the code?

Update the spec to match reality. The spec lives with the code as documentation.

## What makes a bad spec

- **Too long.** A spec for a single function should be < 200 words. For a small feature, < 1 page. If you're writing 10 pages, you're writing requirements, not a spec.
- **Too vague.** "Should handle errors gracefully" is not a spec. "On JWT validation failure, return 401 with body `{error: 'invalid_token'}`" is.
- **Implementation in disguise.** If the spec says "use a Redis cache with 60s TTL," that's an implementation detail. Spec says "lookups should be fast (<10ms p99 for warm queries)." HOW is the engineer's choice.
- **Doesn't enumerate failure cases.** Most bugs are in the edge cases nobody specified.
- **No success criteria.** If you can't define "done," you can't ship.

## What makes a good spec

- **Small.** A page or less for most features.
- **Concrete.** Specific HTTP codes, specific data shapes, specific failure responses.
- **Edge-aware.** At least half the spec is about what happens when things go wrong.
- **Spec-vs-implementation invariant.** A reader can tell from the code whether the spec is being honored.
- **Living.** Updated when reality diverges. Not a write-once artifact.

## Anti-patterns

- **"Specs slow you down."** No. Skipping specs slows you down at the 60% mark when you discover you've been guessing at requirements.
- **"The AI will figure it out."** It will produce something. Without a spec, "something" is the right description.
- **"The PR description is the spec."** Sometimes. Usually not — PR descriptions tend to describe what the code does, not what the feature should do.
- **"Specs are for waterfall."** Modern lightweight specs are 200 words and exist to align humans and AI, not to satisfy a process gate.

## Integration with your skills

- **`brainstorming`** → Phase 1 input
- **`pre-mortem`** → Run against the draft spec; surfaces missing edge cases
- **`eval-driven-development`** → Success criteria section + edge cases become the eval
- **`test-driven-development`** → Phase 3 derives tests from spec
- **`vibe-coding-guardrails`** → Spec is the lens for diff review in Phase 4
- **`baseline-first`** → Spec should include "dumbest possible implementation" as Phase 4 starting point

## When NOT to use this

- **Single-line bug fixes.** Just fix it.
- **Truly experimental work.** If you're spiking to learn, the spike is the spec. Throw it away after.
- **Boilerplate that follows existing patterns.** Don't spec a new CRUD endpoint that's the 47th of its kind. Copy the pattern.

The signal: if you'd struggle to explain the feature to a colleague in 5 minutes, you need a spec. If you can describe it in 30 seconds and they'd build the same thing, skip it.

## Single-question test

> *"Could a different engineer, given only this spec, produce essentially the same implementation I'm about to write?"*

If yes → spec is good, proceed to tests/code.
If no → the spec is incomplete. Sharpen it before writing code.
