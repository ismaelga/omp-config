---
name: eval-driven-development
description: Use when building agentic features, LLM-driven workflows, or any system whose correctness can't be captured by unit tests alone - before writing implementation, define how you'll measure that it actually works. Supersedes TDD for behavior that emerges from prompts, tool chains, model selection, or multi-step pipelines.
---

# Eval-Driven Development

> "If you don't have an eval, you don't have a feature." — Andrej Karpathy

## When this beats TDD

TDD tests individual functions in isolation. Eval-Driven Development tests **aggregate behavior** — the thing the user actually cares about. They are complementary, not competing.

Use EDD when:
- The feature involves an LLM call, agent loop, or tool chain
- "Correct" depends on quality, not just shape (good summary vs. bad summary, helpful response vs. wrong tool choice)
- Unit tests pass but the system still fails in production
- You're tuning prompts, model variants, retrieval strategy, or multi-step orchestration

Use TDD when:
- The function has a deterministic contract (parser, validator, math, data transform)
- You can write `assert f(x) == y` and mean it

Most real features need **both**.

## The core discipline

**Write the eval before the implementation.** Not after. Not "we'll add evals later." Before.

The eval is your spec. If you can't write the eval, you don't understand the feature well enough to build it.

## The 5-step EDD loop

1. **Define the success metric in plain English.** One sentence. "The agent should fix the failing test without breaking other tests." "The summary should preserve the 3 key decisions from the meeting." "The retrieval should return the relevant docs in the top 5."

2. **Build the dataset.** Minimum 10 examples. Ideally 30-50. Mix easy / medium / hard / edge cases. Real examples beat synthetic examples. If you don't have data, your "feature" is a guess.

3. **Build the scorer.** How does an example go from input → judged output? Options in increasing rigor:
   - Manual: you eyeball N examples and rate them
   - Heuristic: regex / structural checks on the output
   - LLM-as-judge: another model scores the output (use the cheapest one that's calibrated)
   - Programmatic ground truth: deterministic check against expected output (only when possible)
   
   Validate the scorer itself: do scorer scores match your gut on a held-out set?

4. **Run baseline. Implement. Re-run.** The baseline is "the simplest thing that could possibly work" — often a one-shot prompt with the cheapest model. The implementation should beat baseline by a meaningful margin. If it doesn't, the implementation is more complex than necessary.

5. **Iterate on the eval as much as the implementation.** When you find a failure mode in production, add it to the eval set. The eval is a living artifact, not a one-time gate.

## What makes a bad eval

- **Too few examples.** N=3 is anecdote, not evaluation. Aim for N≥10 minimum, prefer N≥30.
- **Synthetic-only data.** Examples you invented test what you expected, not what users do.
- **Single metric.** Single-number evals hide regressions. Track accuracy + latency + cost minimum.
- **No held-out set.** If you tune against the full eval, you're overfitting. Keep 20% you don't peek at until ship time.
- **Pass/fail only.** Score distributions are more informative than binary verdicts.
- **LLM-as-judge without validation.** If you didn't manually grade ≥20 examples to calibrate the judge, you don't know what the judge is measuring.

## What makes a good eval

- **Spec-faithful.** The eval measures what the user actually cares about, not what's easy to measure.
- **Diverse.** Easy, medium, hard, edge cases, adversarial inputs.
- **Stable.** Running twice gives similar scores (within noise floor).
- **Discriminating.** Different implementations get meaningfully different scores. If everything scores 95%, your eval is too easy.
- **Cheap to run.** If running the eval takes 2 hours, you'll skip it. Aim for ≤5 minutes for the iteration loop, longer evals reserved for release gates.

## Anti-patterns to reject

- "We'll add evals later." → No you won't. Build it first.
- "The benchmark says we're at 85%." → On what data? Public benchmarks are often saturated or contaminated. Build a workload-specific eval.
- "Both implementations pass the tests." → Tests pass != equally good. EDD shows the gradient.
- "It worked when I tried it." → N=1. Run the eval.
- "The new model is better." → On what eval? Run yours. Lots of frontier models regress on specific tasks while improving on aggregate benchmarks.

## Integration with other skills

- **`brainstorming`** → Defines the success metric in step 1
- **`writing-plans`** → Plan should include the eval design as a first-class deliverable
- **`test-driven-development`** → Use for the deterministic parts (parsers, validators); EDD for the agentic parts
- **`verification-before-completion`** → "Verification" is running the eval, not just `npm test`

## Output checklist before claiming done

- [ ] Eval has ≥10 examples covering easy/medium/hard
- [ ] Scorer is validated (manual spot-check agrees with scorer scores)
- [ ] Baseline number is recorded
- [ ] Final number beats baseline by a meaningful margin
- [ ] Held-out set was not used during iteration
- [ ] Cost and latency are tracked alongside accuracy
- [ ] At least 3 failure cases from the eval are documented in the PR/handoff

If any box is unchecked, you don't have a feature. You have a guess.
