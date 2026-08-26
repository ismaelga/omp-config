---
name: code-review
description: "Use when dispatching a code review, or when acting on review feedback received."
---

# Code Review

Two halves: choosing and dispatching the right review, then evaluating what comes back.

**Core principle:** review depth is earned by risk, and feedback is evaluated, not obeyed.

## Part 1 — Requesting

Reviewers get precisely crafted context, never your session history. That keeps them on the work
product instead of your thought process, and preserves your context for continued work.

### How much review does this diff earn

Every critic pass is a barrier the main thread blocks on. Match the pass to the cost of a defect.

| Diff | Review |
|---|---|
| Low risk: mechanical, local, covered by green checks | None. Read the diff yourself. Checks are the evidence. |
| A plan, before execution | `cavecrew-plancritic` + Momus in parallel. Highest-yield pass measured; never skip it. |
| Normal feature or bugfix | One `cavecrew-reviewer` at the phase boundary, over the accumulated diff |
| Money, auth, migrations, key custody, anything irreversible | Three lenses via `diverge-converge`: reviewer + sentinel + simplifier, one batch |
| Whole branch, pre-merge, high stakes | [code-reviewer.md](code-reviewer.md) heavyweight template |
| A review whose conclusion you doubt | Add `cavecrew-challenger`, fed the first report |

**No reviewer per task.** Accumulate to a phase boundary — roughly every 3-4 tasks — and review
once. Measured over 36 per-task review receipts in real sessions: 58% came back with nothing at
all, and the mean was ≤1.2 findings (an upper bound, since severity markers in the template
inflate it). Compare 19.2 findings/receipt for plan review. Per-task review is the lowest-yield
critic pass in the system and the one that runs most often, which is how a session ends up with
one critic pass per build pass.

**What replaces it:** the controller checks each task's diff against that task's brief itself. It
already generates the review package, and it already has to resolve the cross-task requirements a
task-scoped reviewer explicitly cannot verify — so the extra round trip was buying a subset of
work the controller owes anyway. Dispatch a task-level agent review only for the single task that
lands genuinely risky code.

**Skipping review is a legitimate outcome.** "It's simple" is a bad reason to skip when the diff
touches the risk list, and a fine reason when it does not.

### Dispatching

```bash
BASE_SHA=$(git rev-parse HEAD~1)   # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

Hand the reviewer the SHA range, a one-line description of intent, and the plan or requirement it
should be judged against.

`cavecrew-challenger` runs *after* `cavecrew-reviewer`, never in parallel: its job is to dispute
specific findings and name what the first pass walked past, which needs the report in hand. The
pair runs different model families on purpose — reviewer on `ollama-cloud/glm-5.2`, challenger on
`openai-codex/gpt-5.6-terra`. One family reviewing its own output agrees with its own priors and
returns a rephrased first opinion; self-preference bias in LLM evaluators is measured and
systematic, not random (NeurIPS 2024, "LLM Evaluators Recognize and Favor Their Own Generations").
Cross-family disagreement is the signal you are paying for.

**The benefit is asymmetric, and this matters here.** On 116 LiveCodeBench tasks, cross-family
review raised pass rate 71.6% → 89.7% when the reviewer was the *stronger* model, but *dropped* it
91.4% → 82.8% when the reviewer was weaker (Agentic SE @ KDD '26, arxiv 2607.21656). Both reviewers
above are weaker than an `opus-5` primary. So their findings are input to your adjudication, never
something you apply on sight — the adjudication step below is what keeps a weaker reviewer from
degrading the diff. For money, auth, migration, or key-custody code, put the reviewer on a model at
least as strong as the one that wrote it.

The heavyweight template's `model:` field is REQUIRED — fill it. An omitted model silently
inherits the `task` role, the weakest coding model configured. Its four `[PLACEHOLDER]` tokens are
documented in that file (square brackets, not braces). Do not restate them here; a second copy is
how the two files drifted apart before.

### Arbitrating a pair

- Both flag the same issue → fix it, no debate.
- Challenger disputes a finding → you adjudicate against the code. The first reviewer does not win by default.
- Challenger reports a miss → treat it as a reviewer-tier finding at its stated severity.
- Challenger returns `AGREE.` → the first review stands. That is a real result, not a failed run.
- Neither flags something you suspect → your call. Neither agent has your session context.

### Verify the receipt, not the claim

A subagent reporting success is not evidence that it changed anything. Check the diff before you
repeat its claim. `completed` means the process exited, not that the artifact is correct.

## Part 2 — Receiving

Review requires technical evaluation, not emotional performance. Verify before implementing. Ask
before assuming. Technical correctness over social comfort.

```
1. READ:       complete feedback, without reacting
2. UNDERSTAND: restate the requirement in your own words, or ask
3. VERIFY:     check it against codebase reality
4. EVALUATE:   is it sound for THIS codebase?
5. RESPOND:    technical acknowledgment or reasoned pushback
6. IMPLEMENT:  one item at a time, test each
```

### Forbidden responses

NEVER "You're absolutely right!", "Great point!", "Excellent feedback!", or any gratitude
expression. NEVER "Let me implement that now" before verification.

Instead: restate the technical requirement, ask a specific question, push back with reasoning, or
just start working. Actions over words — the code shows you heard the feedback. If you catch
yourself typing "Thanks", delete it and state the fix.

### Unclear feedback blocks everything

Any unclear item → STOP, implement nothing, ask about the unclear items. Items are often related,
and partial understanding produces a wrong implementation.

Understand 1,2,3,6 but not 4,5 → "Understand 1,2,3,6. Need clarification on 4 and 5 before
implementing." NOT "implement 1,2,3,6 now, ask later".

### Source matters

**Your human partner:** trusted. Implement after understanding. Still ask if scope is unclear. No
performative agreement — skip to action.

**External reviewers:** be skeptical, but check carefully. Before implementing, check whether it is
correct for this codebase, whether it breaks existing functionality, whether there is a reason for
the current implementation, whether it holds on all supported platforms, and whether the reviewer
had full context. Cannot verify? Say so: "I can't verify this without X. Should I investigate, ask,
or proceed?" Conflicts with your partner's prior decision → stop and discuss first.

### YAGNI check on "implement it properly"

Reviewer asks for the professional version → grep for actual usage first. Unused → "Nothing calls
this. Remove it (YAGNI)?" Used → implement properly.

### Order of work

Clarify unclear items FIRST. Then: blocking issues (breaks, security) → simple fixes (typos,
imports) → complex fixes (refactoring, logic). Test each individually. Verify no regressions.

### Push back when

The suggestion breaks existing functionality, the reviewer lacks context, it violates YAGNI, it is
wrong for this stack, legacy or compatibility reasons exist, or it conflicts with a standing
architectural decision. Push back with technical reasoning and reference working tests or code, not
defensiveness. Architectural → involve your partner. Uncomfortable pushing back? Name the tension,
then report the issue anyway.

### When you pushed back and were wrong

"You were right — I checked X and it does Y. Implementing now." State the correction factually and
move on. No long apology, no defending the pushback, no over-explaining.

### Correct feedback

"Fixed. <what changed>" or "Good catch — <specific issue>. Fixed in <location>." or just fix it and
show the code.

## Common mistakes

| Mistake | Fix |
|---|---|
| One reviewer per task | Accumulate to a phase boundary |
| Three lenses on a mechanical diff | One reviewer, or none |
| Performative agreement | State the requirement, or just act |
| Blind implementation | Verify against the codebase first |
| Batch fixes without testing | One at a time, test each |
| Assuming the reviewer is right | Check whether it breaks things |
| Avoiding pushback | Technical correctness over comfort |
| Partial implementation of unclear feedback | Clarify all items first |
| Trusting a subagent receipt | Check the diff |

## Bottom line

Review is earned by risk. Feedback is a suggestion to evaluate, not an order to follow.

Verify. Question. Then implement.

Template: [code-reviewer.md](code-reviewer.md)
