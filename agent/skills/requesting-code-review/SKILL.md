---
name: requesting-code-review
description: Use when completing tasks, implementing major features, or before merging to verify work meets requirements
---

# Requesting Code Review

Dispatch a code reviewer subagent to catch issues before they cascade. The reviewer gets precisely crafted context for evaluation — never your session's history. This keeps the reviewer focused on the work product, not your thought process, and preserves your own context for continued work.

**Core principle:** Review early, review often.

## When to Request Review

**Mandatory:**
- After each task in subagent-driven development
- After completing major feature
- Before merge to main

**Optional but valuable:**
- When stuck (fresh perspective)
- Before refactoring (baseline check)
- After fixing complex bug

## How to Request

**1. Get git SHAs:**
```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**2. Dispatch the review pair:**

1. **cavecrew-reviewer** (`subagent_type: "cavecrew-reviewer"`) — first pass over the SHA range.
2. **cavecrew-challenger** (`subagent_type: "cavecrew-challenger"`) — give it the same SHA range **plus the reviewer's report**.

These run in sequence, not in parallel: the challenger's job is to dispute specific findings and
name what the first pass walked past, which it cannot do without the report in hand. The extra
round trip is the price of dispute semantics instead of two overlapping reports you have to diff
yourself.

The pair runs different model families on purpose — `cavecrew-reviewer` on `ollama-cloud/glm-5.2`,
`cavecrew-challenger` on `openai-codex/gpt-5.6-terra`. One agent that generates and reviews inside
a single family agrees with its own priors and returns a rephrased first opinion. Disagreement
across families is the signal you are paying for.

**For the final pre-merge gate** on a whole branch, use the heavyweight template at
[code-reviewer.md](code-reviewer.md) instead of the pair. Its `model:` field is REQUIRED — fill it.
An omitted model silently inherits the `task` role, which is the weakest coding model configured.

Its four `[PLACEHOLDER]` tokens are documented in that file — square brackets, not braces.
Do not restate them here; a second copy is how the two files drifted apart before.

**3. Arbitrate the pair:**
- Both flag the same issue → fix it, no debate.
- Challenger disputes a finding → you adjudicate against the code. The first reviewer does not win by default.
- Challenger reports a miss → treat it as a reviewer-tier finding at its stated severity.
- Challenger returns `AGREE.` → the first review stands. That is a real result, not a failed run.
- Neither flags something you suspect → your call. Neither agent has your session context.

**4. Act on feedback:**
- Fix Critical / 🔴 immediately
- Fix Important / 🟡 before proceeding
- Note Minor / 🔵 for later
- Push back if a reviewer is wrong (with reasoning)

## Example

```
[Just completed Task 2: Add verification function]

You: Let me request code review before proceeding.

BASE_SHA=$(git log --oneline | grep "Task 1" | head -1 | awk '{print $1}')
HEAD_SHA=$(git rev-parse HEAD)

[Dispatch code reviewer subagent]
  DESCRIPTION: Added verifyIndex() and repairIndex() with 4 issue types
  PLAN_OR_REQUIREMENTS: Task 2 from .omo/plans/deployment-plan.md
  BASE_SHA: a7981ec
  HEAD_SHA: 3df7661

[Subagent returns]:
  Strengths: Clean architecture, real tests
  Issues:
    Important: Missing progress indicators
    Minor: Magic number (100) for reporting interval
  Assessment: Ready to proceed

You: [Fix progress indicators]
[Continue to Task 3]
```

## Integration with Workflows

**Subagent-Driven Development:**
- Review after EACH task
- Catch issues before they compound
- Fix before moving to next task

**Executing Plans:**
- Review after each task or at natural checkpoints
- Get feedback, apply, continue

**Ad-Hoc Development:**
- Review before merge
- Review when stuck

## Red Flags

**Never:**
- Skip review because "it's simple"
- Ignore Critical issues
- Proceed with unfixed Important issues
- Argue with valid technical feedback

**If reviewer wrong:**
- Push back with technical reasoning
- Show code/tests that prove it works
- Request clarification

See template at: [code-reviewer.md](code-reviewer.md)
