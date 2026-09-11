---
name: cavecrew
disable-model-invocation: true
description: >
  Routing guide for the caveman subagent fleet. INERT: all 14 cavecrew-* agents
  and momus are listed in task.disabledAgents, so none can spawn. Kept for
  reference and for the day the fleet is re-enabled; use omp's bundled agents
  (task, scout, reviewer, security-reviewer) instead.
---

Cavecrew = fourteen subagent presets emitting caveman receipts. Same jobs as vanilla agents; the difference is receipt size, so main context lasts longer per delegation. Most run on the flat ollama-cloud tier, so fanning out wide costs latency, not money. Two ride the chatgpt plan on purpose: `cavecrew-challenger`, for model-family divergence against reviewer, and `cavecrew-sentinel`, because a security audit is long-context recall over a diff plus its callers.

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
| Cause known, right fix depth unclear | `cavecrew-fixscout` ×3 — see `skill://diverge-converge` |
| Tests for existing behavior or a bug | `cavecrew-testwright` |
| Run tests / build / lint | `cavecrew-testrunner` |
| "Is it faster" / "what does it cost per request" | `cavecrew-benchwright` |
| Review diff, branch, file for bugs | `cavecrew-reviewer` |
| Second pass on an existing review, different family | `cavecrew-challenger` |
| "Can this be simpler" / over-abstracted / what deletes | `cavecrew-simplifier` |
| Injection / authz / secrets, trust boundary in scope | `cavecrew-sentinel` |
| "Who wrote X / when added / which commit broke Z" | `cavecrew-githistorian` |
| Commit, rebase, squash, push | `git-master` on main thread |
| External library or API facts | `task` (vanilla) |
| Review plan in `.omo/plans/` | `cavecrew-plancritic` (pair with Momus) |
| One problem, several defensible answers | `skill://diverge-converge` — fan lenses, converge here |
| Answer you already know | Main thread, no subagent |

Overlap tiebreakers:

- **builder vs refactorer** — behavior changes? Yes → builder. No → refactorer (verifies callsites via `lsp references`, refuses semantic drift).
- **investigator vs debugger** — investigator answers *where*, debugger answers *why* and needs a reproduction.
- **reviewer vs sentinel** — reviewer finds bugs, sentinel traces attacker input to a sink and needs a trust boundary.
- **testwright vs testrunner** — testwright writes the assertions, testrunner only executes and reports. Neither fixes production code.
- **testrunner vs benchwright** — pass/fail → testrunner. Numbers with spread → benchwright.
- **simplifier vs refactorer** — simplifier says *what* to cut and proves it dead; refactorer performs the cut. Report, then act.
- **fixscout vs debugger vs builder** — debugger finds the cause, fixscout proposes depth without editing, builder applies. Cause known and depth obvious → straight to builder.
- **challenger vs a second reviewer** — challenger needs the first report and disputes it. Two blind reviewers on different lenses is `diverge-converge` instead.

## Why this exists

Subagent receipts are injected into main context verbatim, so a terse receipt leaves more room in the parent session. That is the actual benefit: **context headroom, not money.** Caveman compresses output only, and output is the smallest term in any token bill — measured input runs 20-55K/turn against a few hundred output. The compression ratio has never been measured here; treat "smaller receipts" as design intent, not a benchmarked number.

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

**`cavecrew-fixscout`** — `aim:`, `fix: path:line`, `steps:` (thorough/creative only), `root-cause: addressed | symptom-only:`, `blast:`, `risk:`, `rejected:`. Or `no aim.` / `no cause.` A `simple` aim that only patches the symptom must say so.

**`cavecrew-testwright`** — `file:` (n cases, convention), `run:`, `gaps:`. Or `tests only.` / `no sibling tests.` / `needs seam at path:line.`

**`cavecrew-testrunner`** — `cmd:`, `result: PASS | FAIL (n/total) | ERROR | HUNG`, `fails:`. PASS → 2 lines. Or `run-only.` / `ambiguous.`

**`cavecrew-benchwright`** — `subject:`, `harness:` (N per arm), `arms:` median + p95, `delta:` or `within noise`, `cost:` (+cached input yes/no), `bottleneck:`. No baseline → no verdict.

**`cavecrew-reviewer`** — `path:line: <emoji> <severity>: <problem>. <fix>.` + `totals:`. Or `No issues.` Sorted file → line.

**`cavecrew-challenger`** — `DISPUTED` / `MISSED` / `CONFIRMED` as line prefixes, `verdict: AGREE | DISPUTE-<n> MISSED-<n>` last. Needs the first reviewer's report. `AGREE.` is a common, legitimate result.

**`cavecrew-simplifier`** — `DELETE` / `COLLAPSE` / `DUPLICATE` / `EARNED` as line prefixes + `totals:`. Or `already minimal.` Every DELETE cites a zero-caller `lsp references` check; `EARNED` proves it judged rather than only cut.

**`cavecrew-sentinel`** — `path:line: <emoji> <severity>: <vuln>. Path: source -> sink. Fix:` + `traced:`. Every finding names a traced path; 🔴/🟠 carry a plain-English blast-radius line.

**`cavecrew-githistorian`** — `answer:` first, then `<sha7> <date> <author> — subject — file:line`. Or `No match in history.` / `read-only.`

**`cavecrew-plancritic`** — `plan:`, `<task-N>: <emoji> <severity>:`, `totals:`, `verdict: BLOCK | FIX-THEN-GO | GO` last.

## Chaining

**Locate → fix → verify**: investigator returns sites → builder edits 1-2 → reviewer audits diff.

**Bug to green**: testrunner confirms → debugger returns `cause:` → testwright writes the regression test → builder fixes → testrunner re-runs.

**Wide refactor**: investigator maps surface → refactorer rewrites (self-checks callsites) → reviewer + testrunner in parallel.

**Regression hunt**: testrunner confirms → githistorian finds suspect commit → debugger confirms mechanism → builder fixes.

**Optimization**: benchwright baselines → builder or refactorer changes one thing → benchwright re-measures. No baseline first = no claim after.

**Ship it** (parallel, one batch): sentinel (audit) + testrunner (full suite). No shared files, no ordering.

**Plan review**: plancritic + Momus in parallel, different model families by design. Both flag → fix. One flags a concrete defect → fix. Measured highest-yield critic pass here (plancritic 19.2 findings/receipt, Momus 5.3 design-level, 6-8% empty) — do not trade it away to save a barrier.

**Diverge then converge**: three lenses at the same problem, one batch, converge on main thread. Review → reviewer + sentinel + simplifier (three families). Bug → fixscout ×3 at `aim: simple|thorough|creative`, after debugger has the cause. Protocol and entry gate: `skill://diverge-converge`.

**Parallel scout**: 2-3 investigators in one message on different angles (defs vs callers vs tests), aggregate on main thread.

## What NOT to do

- Don't hand `cavecrew-builder` a file you haven't located — spawn investigator first.
- Don't chain investigator → builder for a 5-file refactor; builder returns `too-big.` Use refactorer.
- Don't send refactorer anything that changes behavior — it returns `not behavior-preserving.`
- Don't spawn debugger on an unreproduced failure; it returns `no-repro.`
- Don't ask testwright to touch production code, or testrunner/benchwright to fix anything.
- Don't ask benchwright for a verdict with no "before" — it needs a baseline ref.
- Don't ask sentinel for a generic sweep with no trust boundary in scope.
- Don't ask reviewer for architecture opinions — those stay on the main thread. Vanilla `reviewer` and `security-reviewer` are disabled; `cavecrew-reviewer` and `cavecrew-sentinel` replace them.
- Don't ask githistorian or plancritic to mutate anything. Both read-only.
- Don't ask simplifier or fixscout to edit. Simplifier hands off to refactorer, fixscout to builder.
- Don't spawn fixscout without an `aim` and a cause — it returns `no aim.` / `no cause.`
- Don't spawn challenger without the first reviewer's report; it has nothing to dispute.
- Don't fan three lenses at a problem with one defensible answer — check the gate in `skill://diverge-converge` first.
- Don't expect prose. Receipts are terse to the point of cryptic; paraphrase before showing a human.

## Auto-clarity (inherited)

Subagents drop caveman for security warnings, irreversible-action confirmations, and anywhere terseness could be misread. Resume after.
