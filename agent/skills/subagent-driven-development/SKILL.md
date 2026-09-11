---
name: subagent-driven-development
description: Use when executing implementation plans with independent tasks in the current session
---

# Subagent-Driven Development

Execute plan by dispatching a fresh implementer subagent per task, a controller-side spec check against the task brief after each, an agent review of the accumulated diff at each phase boundary, and a broad whole-branch review at the end.

**Why subagents:** You delegate tasks to specialized agents with isolated context. By precisely crafting their instructions and context, you ensure they stay focused and succeed at their task. They should never inherit your session's context or history — you construct exactly what they need. This also preserves your own context for coordination work.

**Core principle:** Fresh subagent per task + controller spec check per task + agent review per phase boundary + broad final review = high quality, fast iteration

**Narration:** between tool calls, narrate at most one short line — the
ledger and the tool results carry the record.

**Continuous execution:** Do not pause to check in with your human partner between tasks. Execute all tasks from the plan without stopping. The only reasons to stop are: BLOCKED status you cannot resolve, ambiguity that genuinely prevents progress, or all tasks complete. "Should I continue?" prompts and progress summaries waste their time — they asked you to execute the plan, so execute it.

## When to Use

```dot
digraph when_to_use {
    "Have implementation plan?" [shape=diamond];
    "Tasks mostly independent?" [shape=diamond];
    "subagent-driven-development" [shape=box];
    "Manual execution or brainstorm first" [shape=box];

    "Have implementation plan?" -> "Tasks mostly independent?" [label="yes"];
    "Have implementation plan?" -> "Manual execution or brainstorm first" [label="no"];
    "Tasks mostly independent?" -> "subagent-driven-development" [label="yes"];
    "Tasks mostly independent?" -> "Manual execution or brainstorm first" [label="no - tightly coupled"];
}
```

**Why not a new session:**
- Same session (no context switch)
- Fresh subagent per task (no context pollution)
- Controller checks each task against its brief; agent review batches at phase boundaries and once at the end
- Faster iteration (no human-in-loop between tasks)

## The Process

```dot
digraph process {
    rankdir=TB;

    subgraph cluster_per_task {
        label="Per Task";
        "Dispatch implementer subagent (./implementer-prompt.md)" [shape=box];
        "Implementer subagent asks questions?" [shape=diamond];
        "Answer questions, provide context" [shape=box];
        "Implementer subagent implements, tests, commits, self-reviews" [shape=box];
        "Controller reads the diff against the task brief" [shape=box];
        "Spec gap or defect the controller can name?" [shape=diamond];
        "Dispatch fix subagent with the complete findings list" [shape=box];
        "todo done for the task; append the progress ledger line" [shape=box];
    }

    "Read plan; todo init from its tasks" [shape=box];

    "Phase boundary (~3-4 tasks) or risky task?" [shape=diamond];
    "Dispatch reviewer over the accumulated diff" [shape=box];
    "More tasks remain?" [shape=diamond];
    "Use skill://finishing-a-development-branch" [shape=box style=filled fillcolor=lightgreen];

    "Dispatch implementer subagent (./implementer-prompt.md)" -> "Implementer subagent asks questions?";
    "Read plan; todo init from its tasks" -> "Dispatch implementer subagent (./implementer-prompt.md)";
    "Answer questions, provide context" -> "Dispatch implementer subagent (./implementer-prompt.md)";
    "Implementer subagent asks questions?" -> "Implementer subagent implements, tests, commits, self-reviews" [label="no"];
    "Implementer subagent implements, tests, commits, self-reviews" -> "Controller reads the diff against the task brief";
    "Controller reads the diff against the task brief" -> "Spec gap or defect the controller can name?";
    "Spec gap or defect the controller can name?" -> "Dispatch fix subagent with the complete findings list" [label="yes"];
    "Dispatch fix subagent with the complete findings list" -> "Controller reads the diff against the task brief" [label="re-check"];
    "Spec gap or defect the controller can name?" -> "todo done for the task; append the progress ledger line" [label="no"];
    "Phase boundary (~3-4 tasks) or risky task?" -> "Dispatch reviewer over the accumulated diff" [label="yes"];
    "todo done for the task; append the progress ledger line" -> "Phase boundary (~3-4 tasks) or risky task?";
    "Phase boundary (~3-4 tasks) or risky task?" -> "More tasks remain?" [label="no"];
    "More tasks remain?" -> "Dispatch implementer subagent (./implementer-prompt.md)" [label="yes"];
    "More tasks remain?" -> "Dispatch final code reviewer subagent (../code-review/code-reviewer.md)" [label="no"];
    "Dispatch final code reviewer subagent (../code-review/code-reviewer.md)" -> "Use skill://finishing-a-development-branch";
}
```

Before dispatching Task 1, scan the plan once for conflicts:

- tasks that contradict each other or the plan's Global Constraints
- anything the plan explicitly mandates that the review rubric treats as a
  defect (a test that asserts nothing, verbatim duplication of a logic block)

Present everything you find to your human partner as one batched question —
each finding beside the plan text that mandates it, asking which governs —
before execution begins. That is exactly one `ask` call with all findings:
`questions[]` with one question per conflict, each option carrying the plan
text that mandates it against the review rubric's objection, `recommended`
marking which you think should govern. If the scan is clean, proceed without
comment. The review loop remains the net for conflicts that only emerge from
implementation.

## Agent Selection

omp's `task` dispatch has no per-spawn model parameter — model comes from the
agent type (each agent's own frontmatter), overridden by
`task.agentModelOverrides` in config.yml. So you control cost and capability
by choosing the agent TYPE per dispatch, not by naming a model:

- **`scout`** — read-only, fast, cheap. Investigation and plan recon; never
  for code changes.
- **`reviewer`** — code review. Use for phase-boundary, risky-task, and
  final whole-branch reviews.
- **`security-reviewer`** — review of genuinely risky code: money movement,
  auth, a migration, key custody, anything irreversible.
- **`task`** — general implementation. The default implementer type.

Where the original model-tiering judgment lives on: a mechanical task with a
complete spec and a design task needing broad codebase judgment both run on
`task`, but they deserve different agent types only if your config maps
several implementation agents at different capability points — check
`task.agentModelOverrides` and the `agents/*.md` fleet before assuming one
generic implementer is the only option. When one type maps to one model,
the tiering lever moves to how you write the dispatch: a well-specified
brief with exact code and commands keeps even a mid-tier implementer to few
turns, and turn count — not token price — dominates cost.

Complexity signals that should make you reach past the default type:
- Touches 1-2 files with a complete spec → the default implementer type is fine
- Touches multiple files with integration concerns → check whether your config
  defines a stronger implementation agent; if it does, use it
- Requires design judgment or broad codebase understanding → the most capable
  implementation agent type available; if none is defined, note the limit when
  you report to the human

## Handling Implementer Status

Implementer subagents report one of four statuses via their dispatch's
`outputSchema` (shape in [implementer-prompt.md](implementer-prompt.md));
results arrive validated and stay reachable at `agent://<id>?q=.status`.
Handle each appropriately:

**DONE:** Generate the review package (`scripts/review-package BASE HEAD`, from this skill's directory — it prints the unique file path it wrote; BASE is the commit you recorded before dispatching the implementer — never `HEAD~1`, which silently drops all but the last commit of a multi-commit task), then copy it to `local://` (e.g. `cp <path> local://sdd-review-<base7>..<head7>.diff`) and read that copy against the task brief. See "Per-Task Spec Check" below. Hold the URI — the phase-boundary reviewer gets the accumulated range, not this one.

**DONE_WITH_CONCERNS:** The implementer completed the work but flagged doubts. Read the concerns before proceeding. If the concerns are about correctness or scope, address them before the spec check. If they're observations (e.g., "this file is getting large"), note them and carry them to the phase-boundary review.

**NEEDS_CONTEXT:** The implementer is now idle with its context intact — do
not throw that away. Send it the missing information in place:
`hub send {to: "<implementer-name>", message: "<the missing context>"}` wakes
it with everything it already learned intact. Re-dispatching a fresh agent
would rebuild context from zero for no reason. Re-dispatch via `task` is for
BLOCKED, where the agent type itself must change.

**BLOCKED:** The implementer cannot complete the task. Assess the blocker:
1. If it's a context problem, provide more context via `hub send` first; a
   fresh dispatch with the added context is the fallback when the blocker is
   structural (the agent needed it before starting, not mid-task)
2. If the task requires more reasoning, re-dispatch with a different agent
   type — a more capable implementation agent from your `agents/` fleet
3. If the task is too large, break it into smaller pieces
4. If the plan itself is wrong, escalate to the human

**Never** ignore an escalation or re-dispatch the same agent type with
unchanged inputs. If the implementer said it's stuck, something needs to
change.

## Per-Task Spec Check

After each task you read the review package against that task's brief yourself. No reviewer
subagent per task: measured over 36 real per-task review receipts, 58% came back with nothing and
the mean was ≤1.2 findings, against 19.2 for plan review. It was the lowest-yield critic pass in
the system and the one that ran most often — one per task is exactly how a session ends up with a
critic pass for every build pass.

You are also the only one who *can* do the whole job. A task-scoped reviewer cannot verify
requirements that live in unchanged code or span tasks; it can only flag them as "cannot verify
from diff" and hand them back. You hold the plan and the cross-task context, so those were always
yours to resolve.

What you are checking, in order:

1. **Spec compliance** — every requirement in the brief is met, and nothing extra was built.
   Missing or extra both fail.
2. **Global constraints** — the binding values, formats, and stated relationships from the plan's
   Global Constraints section hold.
3. **Cross-task coupling** — interfaces this task exposes match what later tasks expect. This is
   the failure that compounds, and it is the reason the check is per task rather than deferred.
4. **Obvious defects** — anything the code-slop bans name. Deep quality review is the phase
   boundary's job, not yours; do not go hunting.

Found a real gap → dispatch ONE fix subagent with the complete findings list, then re-read the
updated package. Clean → mark the task complete and move on.

Do not delegate this check back out to an agent to avoid reading a diff. Reading the diff is the
job.

## Phase-Boundary Review

Every ~3-4 tasks, and once at the end, dispatch a reviewer over the *accumulated* diff rather than
one task's. Build the package with `scripts/review-package BASE HEAD` (BASE = the commit the phase
started from), copy it to `local://sdd-review-<base7>..<head7>.diff`, and pass that URI to a
`reviewer` agent. One reviewer, not a pair — dispatch a second `reviewer` (fed the first report)
only when you doubt it.

Dispatch a task-scoped review off-cycle for a single task only when that task lands genuinely
risky code: money movement, auth, a migration, key custody, or anything irreversible.

## Constructing Reviewer Prompts

Phase-boundary reviews cover the accumulated diff. The broad review happens once, at the
final whole-branch review. When you fill a reviewer template:

- Do not add open-ended directives like "check all uses" or "run race tests
  if useful" without a concrete, task-specific reason
- Do not ask a reviewer to re-run tests the implementer already ran on the
  same code — the implementer's report carries the test evidence
- Do not pre-judge findings for the reviewer — never instruct a reviewer to
  ignore or not flag a specific issue. If you believe a finding would be a
  false positive, let the reviewer raise it and adjudicate it in the review
  loop. If the prompt you are writing contains "do not flag," "don't treat X
  as a defect," "at most Minor," or "the plan chose" — stop: you are
  pre-judging, usually to spare yourself a review loop.
- The global-constraints block you hand the reviewer is its attention
  lens. Copy the binding requirements verbatim from the plan's Global
  Constraints section or the spec: exact values, exact formats, and the
  stated relationships between components ("same layout as X", "matches
  Y"). The reviewer's template already carries the process rules (YAGNI,
  test hygiene, review method) — the constraints block is for what THIS
  project's spec demands.
- Hand the reviewer its diff as a `local://` file: run this skill's
  `scripts/review-package BASE HEAD`, copy the file it prints to
  `local://sdd-review-<base7>..<head7>.diff`, and pass the reviewer that
  URI (or, without the script: `git log --oneline`, `git diff --stat`,
  and `git diff -U10` for the range, written to one uniquely named file
  under `local://`). The output never enters your own context, and the
  reviewer sees the commit list, stat summary, and full diff with context
  in one Read call. Use the BASE you recorded before dispatching the
  implementer — never `HEAD~1`, which silently truncates multi-commit tasks.
- A dispatch prompt describes one task, not the session's history. Do not
  paste accumulated prior-task summaries ("state after Tasks 1-3") into
  later dispatches — a real session's dispatch hit 42k chars of which 99%
  was pasted history. A fresh subagent needs its task, the interfaces it
  touches, and the global constraints. Nothing else.
- Dispatch fix subagents for Critical and Important findings. Record Minor
  findings in the progress ledger as you go, and point the final
  whole-branch review at that list so it can triage which must be fixed
  before merge. A roll-up nobody reads is a silent discard.
- A finding labeled plan-mandated — or any finding that conflicts with
  what the plan's text requires — is the human's decision, like any plan
  contradiction: present the finding and the plan text, ask which governs.
- The final whole-branch review gets a package too: run
  `scripts/review-package MERGE_BASE HEAD` (MERGE_BASE = the commit the
  branch started from, e.g. `git merge-base main HEAD`), copy the file to
  `local://`, and put the URI in the final review dispatch, so the final
  reviewer reads one file instead of re-deriving the branch diff with git
  commands.
- Every fix dispatch carries the implementer contract: the fix subagent
  re-runs the tests covering its change and reports the results. Name the
  covering test files in the dispatch — a one-line fix does not need the
  whole suite. Before re-dispatching the reviewer, confirm the fix report
  contains the covering tests, the command run, and the output; dispatch
  the re-review once all three are present.
- If the final whole-branch review returns findings, dispatch ONE fix
  subagent with the complete findings list — not one fixer per finding.
  Per-finding fixers each rebuild context and re-run suites; a real
  session's final-review fix wave cost more than all its tasks combined.

## File Handoffs

Everything you paste into a dispatch prompt — and everything a subagent
prints back — stays resident in your context for the rest of the session
and is re-read on every later turn. Hand artifacts over as files in your
`local://` space: the parent writes the payload once with `write local://<name>.md`,
and the subagent reads that URI by path in its dispatch. Payloads under
`local://` never enter your context, and the subagent gets them in one Read.

- **Task brief:** before dispatching an implementer, run this skill's
  `scripts/task-brief PLAN_FILE N` and copy the file it prints to
  `local://sdd-task-N-brief.md` (or write the brief straight there).
  Compose the dispatch so the brief stays the single source of
  requirements. Your dispatch should contain: (1) one line on where this
  task fits in the project; (2) the brief URI, introduced as "read this
  first — it is your requirements, with the exact values to use verbatim";
  (3) interfaces and decisions from earlier tasks that the brief cannot
  know; (4) your resolution of any ambiguity you noticed in the brief;
  (5) the report URI and report contract. Exact values (numbers, magic
  strings, signatures, test cases) appear only in the brief.
- **Report file:** name the implementer's report file after the brief
  (`local://sdd-task-N-brief.md` → `local://sdd-task-N-report.md`) and put
  the URI in the dispatch prompt. The implementer writes the full report
  there; its validated result carries only status, commits, a one-line
  test summary, and concerns.
- **Reviewer inputs:** a phase-boundary or risky-task reviewer gets three
  `local://` URIs — the brief files for the tasks in range, the report
  file, and the review package — plus the global constraints that bind them.
- Fix dispatches append their fix report (with test results) to the same
  report file and return a short validated summary; your re-check reads the
  updated file.

## Tracking Progress

Use the `todo` tool as the primary in-session tracker: `todo init` from the
plan's task list at skill start, then `todo start` when you dispatch a task,
`todo done` when its review comes back clean, `todo block` when a task is
stuck. The todo list is what you (and a compaction) see at a glance — keep
it authoritative for the current session.

The todo list does not survive the session, and conversation memory does not
survive compaction. In real sessions, controllers that lost their place have
re-dispatched entire completed task sequences — the single most expensive
failure observed. The ledger file is the git-durable complement that covers
both:

- At skill start, check for a ledger:
  `cat "$(git rev-parse --show-toplevel)/.superpowers/sdd/progress.md"`. Tasks listed there
  as complete are DONE — do not re-dispatch them; resume at the first task
  not marked complete.
- When a task's review comes back clean, append one line to the ledger in
  the same message as your other bookkeeping:
  `Task N: complete (commits <base7>..<head7>, review clean)`.
- The ledger is your recovery map: the commits it names exist in git even
  when your context no longer remembers creating them. After compaction,
  trust the ledger and `git log` over your own recollection.
- `git clean -fdx` will destroy the ledger (it's git-ignored scratch); if
  that happens, recover from `git log`.

## Prompt Templates

- [implementer-prompt.md](implementer-prompt.md) - Dispatch implementer subagent
- [task-reviewer-prompt.md](task-reviewer-prompt.md) - Phase-boundary review, and off-cycle review of a single risky task
- Final whole-branch review: use `code-review`'s [code-reviewer.md](../code-review/code-reviewer.md)

## Example Workflow

```
You: I'm using Subagent-Driven Development to execute this plan.

[Read plan file once: docs/plans/feature-plan.md]
[todo init from the plan's tasks]

Task 1: Hook installation script

[task-brief to local://; dispatch implementer with brief + report URIs + context]

Implementer: "Before I begin - should the hook be installed at user or system level?"

You: "User level (~/.config/superpowers/hooks/)"

Implementer: "Got it. Implementing now..."
[Later] Implementer:
  - Implemented install-hook command
  - Added tests, 5/5 passing
  - Self-review: Found I missed --force flag, added it
  - Committed

[Run review-package, copy to local://, read it against the Task 1 brief]
Spec ✅ - all requirements met, nothing extra. Interfaces match what Task 3 expects.

[todo done Task 1; append ledger line]

Task 2: Recovery modes

[task-brief to local://; dispatch implementer with brief + report URIs + context]

Implementer: [No questions, proceeds]
Implementer:
  - Added verify/repair modes
  - 8/8 tests passing
  - Self-review: All good
  - Committed

[Run review-package, copy to local://, read it against the Task 2 brief]
Spec ❌:
  - Missing: Progress reporting (spec says "report every 100 items")
  - Extra: Added --json flag (not requested)

[Dispatch ONE fix subagent with both findings]
Fix subagent: added progress reporting, removed --json, 8/8 tests pass

[Re-read the updated package]
Spec ✅.

[todo done Task 2; append ledger line]

...

[After all tasks]
[Dispatch final code-reviewer]
Final reviewer: All requirements met, ready to merge

Done!
```

## Advantages

**vs. Manual execution:**
- Subagents follow TDD naturally
- Fresh context per task (no confusion)
- Parallel-safe (subagents don't interfere)
- Subagent can ask questions (before AND during work)

**vs. Executing Plans:**
- Same session (no handoff)
- Continuous progress (no waiting)
- Review checkpoints automatic

**Efficiency gains:**
- Controller curates exactly what context is needed; bulk artifacts move
  as files, not pasted text
- Subagent gets complete information upfront
- Questions surfaced before work begins (not after)

**Quality gates:**
- Self-review catches issues before handoff
- Controller spec check per task catches divergence that compounds across tasks
- Phase-boundary review carries the quality verdict over an accumulated diff
- Spec compliance prevents over/under-building
- Cross-task interface drift is caught at the task that introduced it

**Cost:**
- Subagent invocations: one implementer per task, one reviewer per phase boundary
- Controller does more prep work (extracting all tasks upfront) and reads every task diff
- Fix loops add iterations
- But catches issues early (cheaper than debugging later)

## Red Flags

**Never:**
- Start implementation on main/master branch without explicit user consent
- Skip the per-task spec check, or mark a task complete without reading its diff
- Proceed with unfixed issues
- Dispatch multiple implementation subagents in parallel (conflicts)
- Make a subagent read the whole plan file (hand it its task brief at
  `local://sdd-task-N-brief.md` — `scripts/task-brief` + a copy to
  `local://` — instead)
- Skip scene-setting context (subagent needs to understand where task fits)
- Ignore subagent questions (answer before letting them proceed)
- Accept "close enough" on spec compliance (spec gap = not done)
- Skip the re-check after a fix (fix dispatched = re-read the diff before completing)
- Let implementer self-review replace your spec check (both are needed)
- Reinstate a reviewer subagent per task to avoid reading diffs yourself — that is the
  1.2-findings-per-receipt pass this skill deliberately removed
- Tell a reviewer what not to flag, or pre-rate a finding's severity in the
  dispatch prompt ("treat it as Minor at most") — the plan's example code is
  a starting point, not evidence that its weaknesses were chosen
- Dispatch a phase-boundary reviewer without a review package — generate it
  first (`scripts/review-package BASE HEAD`, copy to `local://`) and put
  the URI in the dispatch
- Skip reading a task's diff yourself because the tests passed — green checks do not
  show you that the wrong thing was built
- Move to next task with an open spec gap or an unfixed Critical/Important finding
- Re-dispatch a task the progress ledger already marks complete — check
  the ledger (and `git log`) after any compaction or resume

**If subagent asks questions:**
- Answer clearly and completely
- Provide additional context if needed
- Don't rush them into implementation

**If the spec check or a review finds issues:**
- Dispatch ONE fix subagent with the complete findings list
- Re-read the updated review package
- Repeat until the gap is closed
- Don't skip re-reading the diff after the fix

**If subagent fails task:**
- Dispatch fix subagent with specific instructions
- Don't try to fix manually (context pollution)

## Integration

**Required workflow skills:**
- **skill://using-git-worktrees** - Ensures isolated workspace (creates one or verifies existing)
- **skill://writing-plans** - Creates the plan this skill executes
- **skill://code-review** - Review depth gating, the whole-branch template, and how to act on findings
- **skill://finishing-a-development-branch** - Complete development after all tasks

**Subagents should use:**
- **skill://test-driven-development** - Subagents follow TDD for each task

**Execution alternative:**
- None. Plans execute via subagents, not a new session.
