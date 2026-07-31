---
name: cavecrew
description: >
  Decision guide for delegating to caveman-style subagents. Routes to
  `cavecrew-investigator` (locate code), `cavecrew-builder` (1-2 file edit),
  `cavecrew-refactorer` (behavior-preserving cross-file rewrite),
  `cavecrew-debugger` (root-cause a reproduced failure), `cavecrew-testwright`
  (write tests), `cavecrew-testrunner` (run tests/build/lint),
  `cavecrew-evalsmith` (eval harness for non-deterministic behavior),
  `cavecrew-benchwright` (measure perf and cost), `cavecrew-reviewer` (diff
  review), `cavecrew-sentinel` (security audit), `cavecrew-githistorian`
  (blame/log -S/bisect), `cavecrew-mergescout` (branch merge-readiness), or
  `cavecrew-plancritic` (implementation-plan review), instead of doing the work
  inline. Receipts are caveman-compressed, so the tool-result injected back
  into main context is small.
  Trigger: "delegate to subagent", "use cavecrew", "spawn investigator/builder/refactorer/debugger/testwright/testrunner/evalsmith/benchwright/reviewer/sentinel/githistorian/mergescout/plancritic",
  "save context", "compressed agent output".
---

Cavecrew = thirteen subagent presets emitting caveman receipts. Same jobs as vanilla agents; the difference is receipt size, so main context lasts longer per delegation. All thirteen run on the flat ollama-cloud tier, so fanning out wide costs latency, not money.

## Routing

| Task | Use |
|---|---|
| "Where is X defined / what calls Y / list uses of Z" | `cavecrew-investigator` |
| Same, plus architecture commentary | `scout` (vanilla) |
| Surgical edit, ≤2 files, behavior may change | `cavecrew-builder` |
| Rename / signature / codemod / dead code, behavior identical | `cavecrew-refactorer` |
| New feature / new behavior / 3+ files | Main thread or `task` |
| Reproduced failure, cause unknown | `cavecrew-debugger` |
| Cause known, fix ≤2 files | `cavecrew-builder` (skip debugger) |
| Tests for existing behavior or a bug | `cavecrew-testwright` |
| Run tests / build / lint | `cavecrew-testrunner` |
| Prompt, agent loop or model comparison — needs pass-rate over N | `cavecrew-evalsmith` |
| "Is it faster" / "what does it cost per request" | `cavecrew-benchwright` |
| Review diff, branch, file for bugs | `cavecrew-reviewer` |
| Deep review with rationale + alternatives | `reviewer` (vanilla) |
| Injection / authz / secrets, trust boundary in scope | `cavecrew-sentinel` |
| "Who wrote X / when added / which commit broke Z" | `cavecrew-githistorian` |
| "Is this branch ready / what will conflict / PR body" | `cavecrew-mergescout` |
| Commit, rebase, squash, push | `git-master` on main thread |
| External library or API facts | `librarian` (vanilla) |
| Review plan in `.omo/plans/` | `cavecrew-plancritic` (pair with Momus) |
| Answer you already know | Main thread, no subagent |

Overlap tiebreakers:

- **builder vs refactorer** — behavior changes? Yes → builder. No → refactorer (verifies callsites via `lsp references`, refuses semantic drift).
- **investigator vs debugger** — investigator answers *where*, debugger answers *why* and needs a reproduction.
- **reviewer vs sentinel** — reviewer finds bugs, sentinel traces attacker input to a sink and needs a trust boundary.
- **testwright vs evalsmith** — deterministic assertion → testwright. Scored over N samples → evalsmith.
- **testrunner vs benchwright** — pass/fail → testrunner. Numbers with spread → benchwright.

## Why this exists

Subagent receipts are injected into main context verbatim, so a terse receipt leaves more room in the parent session. That is the actual benefit: **context headroom, not money.** Caveman compresses output only, and output is the smallest term in any token bill — measured input runs 20-55K/turn against a few hundred output. The compression ratio has never been measured here; treat "smaller receipts" as design intent, not a benchmarked number. If you want the real figure, that is `cavecrew-evalsmith` plus `cavecrew-benchwright` on identical inputs.

## Input discipline (where the tokens actually are)

ollama-cloud does no prompt caching, so every subagent turn re-bills its whole transcript. Turn count and tool-output volume dominate everything else:

- Hand the agent the narrowest scope that answers the question — a path, a symbol, a commit range. A vague brief costs a discovery loop.
- Read-only locators run with summarized reads; they should never pull whole file bodies to emit line numbers.
- One well-aimed spawn beats a chatty one. Prefer re-spawning with a better brief over letting an agent grope across ten turns.

## Output contracts

**`cavecrew-investigator`** — `path:line — \`symbol\` — note`, then `totals:`. Or `No match.` Greppable as `path:\d+`.

**`cavecrew-builder`** — `<path:line-range> — <change>` + `verified:`. Or terminal `too-big.` / `needs-confirm.` / `ambiguous.` / `regressed.`

**`cavecrew-refactorer`** — `symbol:` old→new, `callsites: n in m files (source: lsp references)`, `residual:`, `check: lsp diagnostics`. Or `not behavior-preserving.` / `no lsp.`

**`cavecrew-debugger`** — `repro:`, `cause: path:line — mechanism`, `killed:`, `fix:`. `cause` always present or `no-repro.` Killed hypotheses are load-bearing.

**`cavecrew-testwright`** — `file:` (n cases, convention), `run:`, `gaps:`. Or `tests only.` / `no sibling tests.` / `needs seam at path:line.`

**`cavecrew-testrunner`** — `cmd:`, `result: PASS | FAIL (n/total) | ERROR | HUNG`, `fails:`. PASS → 2 lines. Or `run-only.` / `ambiguous.`

**`cavecrew-evalsmith`** — `task:`, `rubric:` (+judge kind), `variants:` each `pass/N (rate%)` + failure mode, `verdict:`, `harness:`. Never a rate without N; `no separation at N=n` is a valid verdict.

**`cavecrew-benchwright`** — `subject:`, `harness:` (N per arm), `arms:` median + p95, `delta:` or `within noise`, `cost:` (+cached input yes/no), `bottleneck:`. No baseline → no verdict.

**`cavecrew-reviewer`** — `path:line: <emoji> <severity>: <problem>. <fix>.` + `totals:`. Or `No issues.` Sorted file → line.

**`cavecrew-sentinel`** — `path:line: <emoji> <severity>: <vuln>. Path: source -> sink. Fix:` + `traced:`. Every finding names a traced path; 🔴/🟠 carry a plain-English blast-radius line.

**`cavecrew-githistorian`** — `answer:` first, then `<sha7> <date> <author> — subject — file:line`. Or `No match in history.` / `read-only.`

**`cavecrew-mergescout`** — `branch:` ahead/behind, `conflicts:`, `gaps:`, `leftovers:`, `pr-body:`, `verdict: READY | FIX-THEN-GO | REBASE-FIRST` last. Read-only; never merges.

**`cavecrew-plancritic`** — `plan:`, `<task-N>: <emoji> <severity>:`, `totals:`, `verdict: BLOCK | FIX-THEN-GO | GO` last.

## Chaining

**Locate → fix → verify**: investigator returns sites → builder edits 1-2 → reviewer audits diff.

**Bug to green**: testrunner confirms → debugger returns `cause:` → testwright writes the regression test → builder fixes → testrunner re-runs.

**Wide refactor**: investigator maps surface → refactorer rewrites (self-checks callsites) → reviewer + testrunner in parallel.

**Regression hunt**: testrunner confirms → githistorian finds suspect commit → debugger confirms mechanism → builder fixes.

**Optimization**: benchwright baselines → builder or refactorer changes one thing → benchwright re-measures. No baseline first = no claim after.

**Prompt or model change**: evalsmith defines rubric and baselines pass rate → change → evalsmith re-runs same inputs.

**Ship it** (parallel, one batch): mergescout (readiness) + sentinel (audit) + testrunner (full suite). No shared files, no ordering.

**Plan review**: Momus + plancritic in parallel, different model families by design. Both flag → fix. One flags a concrete defect → fix.

**Parallel scout**: 2-3 investigators in one message on different angles (defs vs callers vs tests), aggregate on main thread.

## What NOT to do

- Don't hand `cavecrew-builder` a file you haven't located — spawn investigator first.
- Don't chain investigator → builder for a 5-file refactor; builder returns `too-big.` Use refactorer.
- Don't send refactorer anything that changes behavior — it returns `not behavior-preserving.`
- Don't spawn debugger on an unreproduced failure; it returns `no-repro.`
- Don't ask testwright or evalsmith to touch production code, or testrunner/benchwright to fix anything.
- Don't ask benchwright for a verdict with no "before" — it needs a baseline ref.
- Don't ask evalsmith for a winner at N=1; it will say `no separation`.
- Don't ask sentinel for a generic sweep with no trust boundary in scope.
- Don't ask reviewer for architecture opinions — that's vanilla `reviewer`.
- Don't ask githistorian, mergescout or plancritic to mutate anything. All read-only.
- Don't expect prose. Receipts are terse to the point of cryptic; paraphrase before showing a human.

## Auto-clarity (inherited)

Subagents drop caveman for security warnings, irreversible-action confirmations, and anywhere terseness could be misread. Resume after.
