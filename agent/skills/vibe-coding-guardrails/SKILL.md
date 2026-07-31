---
name: vibe-coding-guardrails
description: Use when running ultrawork, ralph loops, or any session where the agent is allowed to write significant code autonomously - enforces the discipline that separates productive "vibe coding" from regrettable "slop coding". The boundary is whether you actually read the diff.
---

# Vibe Coding Guardrails

> "There's a difference between vibe coding (productive) and slop coding (regret). The boundary is whether you read the diff." — Andrej Karpathy (paraphrased from his March 2026 thread coining the term)

## What is vibe coding

Vibe coding is the productive flow state where you describe what you want at a high level and the agent does it. You're directing, not typing. Done well, it's the most productive way to build software ever invented.

## What is slop coding

Slop coding is the same activity without discipline. The agent writes plausible-looking code, tests pass, you merge it. Three weeks later you discover:
- The error handling swallows exceptions
- The retry logic creates infinite loops under specific timing
- The "abstraction" is a one-call wrapper that obscures the actual logic
- Comments say what the code does (visibly), not why (invisibly)
- The code is correct for the case you tested and broken for the one you didn't

The technical work output looks identical at write-time. The difference shows up at maintenance-time, when no one wants to touch the slop and the codebase rots.

## The boundary: did you read the diff

Vibe coding ≠ blind trust. The skill is being a fast, opinionated reviewer of your AI's output. You can ride the agent at 10× human typing speed AND read every diff.

**Read the diff means:**
- Eyes scanned every changed line
- You can explain what each function does and why it exists
- You'd be willing to defend the code in code review
- You'd write it the same way (or close) if asked

**Read the diff does NOT mean:**
- "I trust the agent and skimmed it"
- "Tests pass, so it must be fine"
- "It looks reasonable"

## The 4 checkpoint rule

You hit a checkpoint whenever any of these happen:

1. **End of a logical unit of work** (function/file/module complete)
2. **Before any commit**
3. **Before delegating to another agent**
4. **Every 15 minutes of agent runtime, minimum**

At each checkpoint:
1. `git diff` (or equivalent) — actually look at the changes
2. Run the eval / tests, not just `tsc`
3. Run the slop checklist (below)
4. If any item fails: revert, redirect, or fix before continuing

## The slop pattern checklist

These are the AI-generated patterns to reject on sight:

### Code smell patterns

- [ ] **Defensive coding for impossible conditions.** `if (!user)` when `user` is typed non-null and comes from internal code. Trust your types and your boundary contracts.
- [ ] **Wrapper functions with one call.** `function getUser(id) { return db.users.findById(id); }` — delete it, inline the call.
- [ ] **"Just in case" try/catch.** Catching errors only to log and rethrow is noise. Catch where you can recover.
- [ ] **Backwards-compat shims for code that doesn't exist yet.** Don't add `// TODO: support old format` for a format you control.
- [ ] **Pre-emptive abstraction.** One concrete user → don't make it generic. Three similar lines beat a parameterized one.
- [ ] **Configuration for hardcoded values.** `const TIMEOUT_MS = 5000` is fine. A whole config system for one timeout is slop.
- [ ] **Helper files with one helper.** `utils/formatDate.ts` exporting one 4-line function. Just put it next to where it's used.

### Comment / naming smell patterns

- [ ] **Comments that restate the code.** `// increment counter` above `counter++` is noise.
- [ ] **AI-flavored phrasing.** Words to nuke: "leverage", "utilize", "robust", "comprehensive", "in order to", "it's important to note", "delve". If you wouldn't say it out loud at a code review, delete it.
- [ ] **Excessive JSDoc on internal code.** Internal types and small functions don't need 8 lines of `@param` blocks.
- [ ] **TODO comments left as a substitute for actually doing the work.** Either do it, file an issue, or delete the comment.

### Behavior smell patterns

- [ ] **Error swallowing.** `catch (e) { return null; }` — propagate, don't hide.
- [ ] **Silent fallbacks.** Default values that mask real failures.
- [ ] **Untested code paths.** If a branch isn't covered by the eval/tests, it doesn't exist in your mental model.
- [ ] **Magic numbers without context.** `setTimeout(retry, 4327)` — why 4327? Either explain or use a named constant.
- [ ] **Type assertions to escape errors.** `as any`, `// @ts-ignore`, `unwrap()` everywhere — fix the underlying type, don't paper over it.

If you find ANY of these, the agent is slop coding. Stop, point at the pattern, and restart with explicit anti-slop instructions.

## Guardrails for specific modes

### Running `ultrawork` / `ulw`

- Set a hard time/iteration cap before starting (e.g., max 30 min wall clock, max 20 tool turns)
- Checkpoint every 5 minutes minimum, not every 15
- Eval must exist before kickoff (see `eval-driven-development`)
- After completion: re-read the whole diff before merging

### Running `ralph_loop`

- Cap `max_iterations` (you have it at 30, good)
- Define explicit exit criteria — not just "until done"
- After every 5 iterations: human review checkpoint
- If the loop is making the same kind of edit repeatedly, it's stuck — stop and redirect

### Running `team` mode / `hyperplan`

- Lead agent's plan must be read by you before members start executing
- After execution: read the diff from every member, not just the lead's summary
- Critics in `hyperplan` are advisors, not oracles — sometimes they're wrong; you decide

## What productive vibe coding looks like

✅ You said: "Add JWT auth to the API, use the existing user schema, hash with bcrypt."
✅ The agent read the existing patterns, found `src/auth/` was empty, asked one clarifying question about token expiry.
✅ You answered: "24h access, 30d refresh, store refresh in httpOnly cookie."
✅ The agent wrote 4 files, 280 lines, all matched existing conventions.
✅ You ran the diff in 90 seconds, ran the eval (auth flows pass), committed.
✅ Total elapsed: 6 minutes. Result: you would have written something very similar in 45 minutes.

## What slop coding looks like

❌ You said: "Add auth."
❌ The agent wrote 1100 lines across 14 files, including a custom JWT library, an "auth manager", a strategy pattern for "future auth providers", elaborate retry logic on the bcrypt call, and 200 lines of error classes.
❌ Tests pass. You merge it.
❌ Three weeks later you need to add OAuth and realize the "strategy pattern" only handles JWT and the refactor takes a day.

The output difference at week 0: barely visible. At week 3: enormous.

## Integration with other skills

- **`eval-driven-development`** → Pre-commit checkpoint runs the eval, not just `npm test`
- **`receiving-code-review`** → You are reviewing the agent's output; same rigor applies
- **`verification-before-completion`** → The slop checklist is the verification
- **`ai-slop-remover`** (oh-my-openagent built-in) → Runs many of these checks automatically; use after vibe coding sessions

## The single-sentence test

Before any commit produced via vibe coding, ask yourself:

> *"If a senior engineer with strong opinions asked me 'why does this code look like this?', could I defend every choice without saying 'the AI wrote it that way'?"*

If yes: ship it.
If no: the agent slopped. Read the diff again, fix what's not yours, commit.
