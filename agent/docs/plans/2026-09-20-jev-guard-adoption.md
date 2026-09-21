# Tool-Call Guard Adoption Plan

**Goal:** Close the gap omp 18.2.6 does not cover natively — screening of tool calls before they execute — and decide what, if anything, replaces the custom Jev CLI stack.

**Status:** Plan only. Nothing here has been applied to `~/.omp/agent`.

**Revision 3 (2026-09-21).** A search of the Jev ecosystem found **`leepokai/jev-guard`**, which is a strictly better fit than the extension this plan was built around, and — unlike it — **has been observed working inside omp**. Option C is re-pointed accordingly; `y0usaf/pi-jev` moves to rejected alternatives. `screen` now has a real successor, which changes Task 6.

**Revision 2 (2026-09-20).** Rewritten after a four-lens review (executability, claim interrogation, threat model, fact-check). The first draft recommended adopting `y0usaf/pi-jev` as a config-only change; that premise was refuted.

## What the review overturned

Every item below was verified on this machine, not inferred. All pi-jev line anchors refer to **`y0usaf/pi-jev` @ `1b49337` (2026-09-19)**, the ref audited here; they are meaningless against a different clone.

1. **`y0usaf/pi-jev`'s gate is inert in omp 18.2.6 — but only the gate.** The extension itself is healthy: loaded from `.omp/extensions/pi-jev/` with no error, and its `jev_ask` tool ran end-to-end, returning `0.06` for "the sky is green" from model `jev-1.13.0`. What fails is the gate path alone. `lastUserRequest()` calls `ctx.sessionManager.buildContextEntries()` (`src/index.ts:625`); a live probe of omp's `sessionManager` returns `buildContextEntries=undefined` (the real methods are `getBranch()` and `buildSessionContext()`). That call is evaluated as an argument to `buildGateState` **inside** `judge()`'s `try` (`index.ts:319-325`), so the `TypeError` is caught at `:338` by `notifyError` and the handler returns `undefined` — **no verdict, ever**. The notice is rate-limited by `ERROR_NOTIFY_INTERVAL_MS` and its text ends in `(failing open)`, so even with a UI attached it is easy to miss. This, not the prompt-block confound, is why both 2026-09-20 test sessions contain zero `pi-jev` markers. Adoption requires a **source patch**, not configuration.
2. **Two opposite failure modes, both real.** The internal `catch` above **fails open** — that is what the code says and does today. Separately, omp documents that `tool_call` handler *errors* block execution (fail-closed). pi-jev defaults to `DEFAULT_TIMEOUT_MS = 20_000` × `DEFAULT_RETRIES = 2` (`src/client.ts:15-16`) ≈ 60 s, well past omp's 30 s handler budget, so a stalled TypeSafe endpoint reaches omp as a handler failure and blocks **every** gated bash/write/edit. A silently-disarmed gate and a wedged toolchain are therefore both reachable, by different routes.
3. **The egress claim was wrong.** `buildGateState` (`src/gate.ts:101-113`) sends `cwd` and, when `index.ts:325` supplies it, `user_request` truncated to 1200 chars — on top of `{tool, arguments, platform}`. My harness measurement omitted both because it never passed them. The privacy comparison against the alternatives was therefore measured-against-README, not like-for-like. Compounding it, **`output.enabled` defaults to `true` for `bash`** (`config.ts:126-127`), so out of the box the first 2000 chars of every bash result also leave the machine.
4. **The extension has no persistence.** Every verdict goes to `ctx.ui.notify`, a no-op headless, plus an in-memory store behind a `/jev` command. A shadow week produces **nothing to tabulate**.
5. **"Usage decayed to zero" is false.** `~/.omp/logs/jev.jsonl` now holds 202 rows: 177 on 09-17, 15 on 09-18, and **10 on 09-20** — including organic non-test use (`task9-step4-install-binary`, `task9-step9-ntfy-post`, `task9-launchd-install`, a `beachcam.meo.pt` screen). The custom stack is in live use in other sessions. The earlier figures were a 09-18 snapshot presented as current.
6. **`screen` has no successor anywhere in this plan.** The extension only ever sees `{tool, arguments, cwd, platform}` — never fetched content or its source — so prompt-injection screening of web/PR/issue text has no replacement. Retiring it is a capability *regression*.
7. **The 2026-09-20 anecdote was selectively told.** In the enforce-mode run the model self-restrained via the custom CLI; in the sibling shadow run the `rm` **executed**. Both are in `~/.omp/agent/sessions/--private-tmp-jevlab--/`.

## What native omp already covers (do not rebuild)

Verified against omp 18.2.6 — still the latest release tag — and the live `config.yml`:

| Custom command | Superseded by | Status in this config |
| --- | --- | --- |
| `stuck` | `features.unexpectedStopDetection` | already `smart` (`config.yml:228`) |
| effort routing | `defaultThinkingLevel: auto` on the TypeSafe judgment backend | already `auto` (`:220`), `autoThinkingMaxEffort: max` (`:95`) |
| `ask` | eval `judge()` — undocumented but real | measured 0.28–0.34 s warm |
| `route` | nothing needed | 76 of 103 calls returned `task`; on organic (non-fixture) lines the margin is far narrower, so treat this as weak evidence, not a proof of uselessness |

`providers.judgmentProvider` is unset → `auto`, and `TYPESAFE_API_KEY` is in the environment, so Jev already backs auto-thinking, stop detection, and git AI staging.

Not native: per-turn model routing, skill relevance ranking, semantic tool-call screening, prompt-injection screening of fetched content.

## The standing exposure

`tools.approvalMode` is unset → defaults `yolo`, and under yolo a bare critical-pattern override is ignored. `bash.patterns` absent, `secrets.enabled` false, `security.enabled` false (all verified by grep; the only `security` hit in `config.yml` is the `security-reviewer` role at `:29`).

Two prior attempts exist and **neither is enforcing anything**:

- `docs/plans/2026-08-12-agent-safety-limits.md` — 827 lines, two-layer design, code marked bun-tested 61 pass / 0 fail. Never deployed: `extensions/` holds only `herdr-omp-agent-state.ts`.
- `scripts/jev-ts/` (743 LOC) plus the `<!-- jev-begin -->` block at `APPEND_SYSTEM.md:18-53`. Working, in organic use, but invoked only when the model elects to.

## Options, re-ranked after review

| Option | Latency | Catches | Fails | Ready? |
| --- | --- | --- | --- | --- |
| **A. Config exact-match denies** (Aug plan layer 1) | none | literal catastrophic shapes | novel/obfuscated forms | **yes, today** |
| **B. `safety-guard` hook** (Aug plan layer 2) | none — pure regex + path logic, no network | the 20 critical patterns, root-aware deletes | semantic intent | **yes — code already written and bun-tested** |
| **C. `leepokai/jev-guard`** @ `94996ea` | ~0.6–0.8 s per assessed call; read-only tools skipped without a call | semantic intent, *plus* planted-instruction detection, *plus* prompt injection in tool results, *plus* instruction-file audit | fails **open** by default; 20 s budget against omp's 30 s; sends tool calls **and tool results** to a third party | **yes — observed blocking inside omp** |

**A + B remain the floor.** Both are deterministic and offline; jev-guard needs the network and its authors call it "a guardrail, not a sandbox". But C is no longer speculative — it is the layer that catches what regex cannot, and it now has a working implementation.

### Why C changed targets

`y0usaf/pi-jev` is rejected (see "Rejected alternatives"). `leepokai/jev-guard` is better on every axis this plan spent two revisions identifying, which is suspicious enough to state explicitly — it is not that it happens to be good, it is that its author solved the same problems:

| Defect found in `pi-jev` | What `jev-guard` does |
| --- | --- |
| gate silently returns nothing in omp | uses `ctx.sessionManager?.getBranch?.() ?? []` — omp's real method, optional-chained. **Verified producing verdicts in omp.** |
| binary block/allow | three-way **deny / ask / allow**, thresholds in env vars |
| headless never blocks, so the test is vacuous | `if (!ctx.hasUI) return { block: true, … }` — headless blocks on `ask` |
| no persistence | per-session memory under `~/.jev-guard/sessions/`, scan cache by content hash |
| no notion of what the user asked for | `user_requested` Noul over session context turns `ask` into `allow`; never lifts a `deny` |
| nothing detects planted instructions | `from_untrusted` Noul denies a call that serves content the agent read, whatever its risk |
| cannot replace `screen` | `tool_result` hook scans results for injection/canaries and **prepends a warning into the content the model sees** |
| 60 s worst case vs omp's 30 s | 20 s total budget including retries; README names the ~30 s host limit explicitly |
| fail-open, undocumented | fail-open **documented and reversible** via `JEV_GUARD_FAIL_CLOSED` |
| no calibration data | published measured table (`ls -la` 0.0 → allow; `git push --force` 2.0/0.96 → ask; `rm -rf /`, `curl | sh`, `wrangler deploy --env production` 3.0 → deny) |

## Global constraints

Carried from `docs/plans/2026-08-12-agent-safety-limits.md`, with one necessary correction — that plan's "Repo is `~/.omp/agent`" is imprecise, and its tokenizer-import constraint applies only to its own Task 1:

- Worktree root is `~/.omp` (private `omp-config`), `agent/` a tracked subdirectory. `.gitignore` paths are rooted at `~/.omp`. Branch `main`, substantial pre-existing uncommitted work. **Do not stage, revert, or clean anything you did not create.**
- **Never run `git commit`, `git push`, or `git rebase` without explicit user approval in the conversation.**
- `bash.patterns` rule keys are exactly `match` and `approval` (`allow`/`deny`/`prompt`). Malformed entries are **silently dropped** — assert the rule count, never assume it.
- Rule order is significant: first match wins. `deny` before any broader `prompt` for the same family.
- **No wildcard `rm` rules in `config.yml`** — exact-match forms only; they compile to an anchor and carry zero collateral cost.
- Config and extension changes require an omp restart. Remind the user; nothing takes effect until then.
- Preserve existing config comment style.
- Do not delete anything under `scripts/jev-ts/` or `APPEND_SYSTEM.md` until Task 6.

## Out of scope

- `tools.approvalMode: write` — prompts on every exec-tier call including every subagent spawn. Rejected in the Aug plan for the same reason.
- Per-turn **main model** routing. `redrossa/pi-model-router` rates as a likely drop-in from source reading — a static rating; no third-party extension has been observed working live, and the one that was tested turned out to be inert. Effort routing, the half that pays, is already native and on.
- Skill relevance ranking. Upstream PRs #12364/#12373 remain open and unmerged; revisit when they land.
- `secrets.enabled` / `security.enabled` — separate decisions.

---

### Task 1: Land the deterministic floor (option A)

Do this first. It is the cheapest closure of the yolo exposure, needs no extension, no key, and no third-party code.

- [ ] **Step 1:** Add the exact-match `bash.patterns` deny entries from `docs/plans/2026-08-12-agent-safety-limits.md` (its Task 3) to `config.yml` — the literal forms of `rm -rf /` and `rm -rf $HOME` plus the 12 conventional shapes. Exact-match only; no wildcards.
- [ ] **Step 2:** Assert the rule count after restart — malformed entries are dropped silently, so a count that does not match what you wrote means entries were rejected.
- [ ] **Step 3:** Verify one deny fires: attempt a literal blocked form in a scratch directory and confirm the harness refuses it.

**Acceptance:** rule count matches, and a literal `rm -rf $HOME` form is refused by the harness with a policy message. Independent of every later task.

### Task 2: Make this work tracked

The repo root is `~/.omp` and `.gitignore` line 4 is a bare `*` default-deny allowlist. Neither `agent/docs/` nor `agent/extensions/` is whitelisted, so both plans are untracked and any vendored extension would be unbacked-up — the failure `AGENTS.md` records at cost.

This is about **backup, not loading**. Verified: a gitignored extension is still discovered and loaded (`.omp/extensions/disc.ts` under a bare `*` gitignore executed normally), despite native discovery globbing with `gitignore: true`. Nothing here blocks Task 3.

- [ ] **Step 1:** Decide whether to widen the allowlist at all. It is deliberate: `~/.omp` holds live credentials, transcripts, and blobs. **Ask the user before widening.**
- [ ] **Step 2:** If yes, add the block below. Two traps, both confirmed against a scratch repo: every intermediate directory needs its own negation (git will not descend into an excluded parent, so `!agent/docs/**/*.md` alone leaves plans ignored), and `!agent/extensions/**/*.ts` would also un-ignore the machine-provisioned `herdr-omp-agent-state.ts` because `**` matches zero directories. `AGENTS.md` names four doc directories; all four are covered below so `decisions/` and `maps/` do not hit the same trap silently later.

```gitignore
!agent/docs/
!agent/docs/plans/
!agent/docs/plans/*.md
!agent/docs/specs/
!agent/docs/specs/*.md
!agent/docs/decisions/
!agent/docs/decisions/*.md
!agent/docs/maps/
!agent/docs/maps/*.md
!agent/extensions/
!agent/extensions/jev-guard/
!agent/extensions/jev-guard/*.ts
```

- [ ] **Step 3:** Confirm the split: `git check-ignore -v` reports no match for the plan files and for `agent/extensions/jev-guard/index.ts`, and **still matches** `agent/extensions/herdr-omp-agent-state.ts`.

**Acceptance:** intended files show as untracked-but-not-ignored. Committing them still needs explicit approval.

### Task 3: Deploy the tested hook (option B)

- [ ] **Step 1:** Create `extensions/safety-guard/policy.ts` and `policy.test.ts` verbatim from the Aug plan's Task 1. Do not "improve" the tokenizer or path logic without re-running its suite.
- [ ] **Step 2:** Run `bun test` in that directory from a bare directory with no local `node_modules` — the real deployment shape. Expect 61 pass / 0 fail.
- [ ] **Step 3:** Wire the `tool_call` hook per the Aug plan's Task 2 and restart.
- [ ] **Step 4:** Retire **only the guard clause** from the `<!-- jev-begin -->` block now — not the whole block. Without this the verification below cannot pass: with the prompt clause live the model self-restrains via the custom CLI and never issues the call, so there is no harness refusal to observe. The clause is superseded by a deterministic, offline, fail-closed hook, and the window it leaves is covered by Task 1's denies. **Keep the `screen` and egress-hygiene clauses** — Task 6 handles those.
- [ ] **Step 5:** Verify a block end-to-end with a sacrificial target in `/tmp`, and confirm the refusal appears as a **harness** message (`Command blocked: … → error <reason>`), not as model narration.

**Acceptance:** suite passes, and a root-adjacent delete is refused by the hook with its own reason string, confirmed in the session JSONL as a bash call that was *issued and blocked* — not self-restrained.

### Task 4: Deploy the semantic layer (option C — `leepokai/jev-guard`)

Only after Tasks 1 and 3. Unlike the previous revision, this task installs working software rather than repairing broken software — the steps are about *policy and egress*, not defect repair.

- [ ] **Step 1:** Pin the ref: `git clone https://github.com/leepokai/jev-guard && git checkout 94996ea` (MIT, zero runtime dependencies, node ≥ 20.3). Prefer the pinned clone over `npm i -g jev-guard` so the audited bytes are the running bytes.
- [ ] **Step 2:** **Read `src/guard.js`, `src/context.js`, `src/session.js` before running it.** It runs in-process on every tool call with full harness privileges, and `tool_call` may rewrite tool `input`, not merely block. The adapter is 47 lines (`extensions/jev-guard.ts`) but the policy it calls is not.
- [ ] **Step 3:** Decide the egress question **before** enabling, because it is larger than the previous option's. The `tool_result` hook sends the *contents* of what the agent read — web pages, files, command output — to `api.typesafe.ai` (ZDR requested; results under 200 chars and local edit/search tools are skipped). That is the price of injection detection. If it is unacceptable for this repo, set `JEV_GUARD_SKIP_SCAN` for the sensitive tools, or run Task 5 first and route it through a proxy you control.
- [ ] **Step 4:** **Set `JEV_GUARD_FAIL_CLOSED=1`.** The default is fail-open with a warning on stderr, which in a headless omp session is invisible. A guard that silently stops guarding is the exact failure this plan already documented once.
- [ ] **Step 5:** Keep `JEV_GUARD_TIMEOUT_MS` at or below `20000` (its default). That is the total budget including retries and stays inside omp's ~30 s handler limit. With fail-closed set, a timeout blocks rather than waves through — verify that tradeoff is what you want before leaving it on.
- [ ] **Step 6:** Load the adapter via `extensions:` in `config.yml` pointing at the pinned clone's `extensions/jev-guard.ts`, or `jev-guard install pi`. Restart. Note the adapter imports `../src/*.js` by relative path, so the repo layout must be preserved — a bare copy of the `.ts` file will not resolve.
- [ ] **Step 7:** Prove it is live with an instrumented threshold rather than trusting silence: run one session with `JEV_GUARD_DENY_SCORE=0` and confirm an ordinary command is refused with a `jev-guard blocked this call (...)` message carrying all four probabilities. Then remove the override. This is the test the previous option failed.
- [ ] **Step 8:** Run a week at default thresholds. `~/.jev-guard/sessions/` holds the per-session record; tabulate `ask` and `deny` outcomes against whether they were correct. Watch specifically for `ask` fatigue — the published table puts `git commit && git push` and `gh pr create` at `ask`, which in this repo's normal workflow may be constant.
- [ ] **Step 9:** Tune from your own data, not the README's. `JEV_GUARD_ASK_SCORE` and `JEV_GUARD_ASK_P` are the two dials that matter; `JEV_GUARD_USER_P` controls how readily an explicit user request downgrades `ask` to `allow`.
- [ ] **Step 10:** Run `jev-guard scan-skills` once against this agent directory. It audits skills, plugins, rules, and `AGENTS.md` for instructions their installer would not expect. With 40+ skills loaded here, this is the one capability with no counterpart anywhere else in this plan.

**Acceptance:** an observed block carrying four probabilities, `JEV_GUARD_FAIL_CLOSED` set, and a week of session records showing an `ask` rate that is tolerable rather than reflexively dismissed.

**Known upstream wart:** the deny message advises lowering `JEV_GUARD_DENY_SCORE` to permit the call, but lowering it denies *more* — the remedy is to raise it. Cosmetic, but it will mislead. Worth an upstream issue.

### Task 5 (optional): Egress control via LiteLLM

Generic pass-through is a documented LiteLLM core feature — `general_settings.pass_through_endpoints` with `path`, `target`, `headers`, `include_subpath` — so no named `typesafe` provider is needed.

- [ ] **Step 1:** Add the route:

```yaml
general_settings:
  pass_through_endpoints:
    - path: "/typesafe"
      target: "https://api.typesafe.ai"
      include_subpath: true
      headers:
        Authorization: "bearer os.environ/TYPESAFE_API_KEY"
        content-type: application/json
```

- [ ] **Step 2:** Point omp at it with `TYPESAFE_BASE_URL=http://<proxy>:4000/typesafe`. omp appends `/v1/systemone`, which is why `include_subpath: true` is required.
- [ ] **Step 3:** Note the tradeoff: this centralises the key and the spend ledger, but adds a hop that sees the same payloads. It reduces key exposure, not content exposure.

**Acceptance:** `TYPESAFE_API_KEY` no longer needed in the omp environment; Jev calls attributable in the proxy ledger.

### Task 6: Retire only what is genuinely superseded

Last, and only with Task 3 (and optionally Task 4) proven.

**Coordination gate, not just a measurement gate.** `jev.jsonl` shows the custom stack in active use by *other concurrent sessions* on 09-20: `route` for a surf CLI at 03:45, four organic `task9-*` guard preflights at 03:56 and 05:02, `screen beachcam.meo.pt` at 12:52. Deleting these commands breaks workflows outside this one, potentially mid-sequence for `task9`-style chains. **When to delete is the user's call.** The accurate retirement rationale is *long-session decay*, not disuse — fresh-session organic use is ongoing.

- [ ] **Step 1:** Delete `scripts/jev-ts/daemon.ts`, `scripts/jev-ts/jev.ts`, and the `route`/`stuck`/`ask` bodies in `core.ts` — after confirming with the user that no in-flight sequence depends on them.
- [ ] **Step 2:** **`screen` now has a successor — but only if Task 4 ships.** jev-guard's `tool_result` hook scans every result for injection and canaries and prepends a warning into the content the model sees, which is strictly better than an elective CLI call: it is automatic, it cannot be forgotten, and it covers `read`/`web_search`/MCP output uniformly. Retire `screen` **only** once Task 4 is deployed and Step 7's liveness check has passed. If Task 4 is declined, `screen` stays — in the logged corpus it had the *highest* flag rate of any command (4/11).
- [ ] **Step 3:** The guard clause is already gone (Task 3 Step 4). Remove the `screen` clause only alongside Step 2's condition. **Keep the egress-hygiene rule** ("never pass actual secret values") regardless — jev-guard sends tool arguments *and* tool results to a third party, so that rule governs more traffic after Task 4, not less.
- [ ] **Step 4:** Keep `skills/typesafe-ai/` — vendor MIT skill for *building* on TypeSafe, unrelated to the harness guard.
- [ ] **Step 5:** Keep `~/.omp/logs/jev.jsonl` as the historical corpus.

**Acceptance:** no orphaned command bodies without callers; `screen` still reachable; the hygiene rule still present.

## Rollback

Per task, in reverse:

- Task 6: `git checkout` the deleted files — **only if they were tracked and committed**; `scripts/jev-ts/*.ts` is whitelisted so it is recoverable, but verify before deleting, not after.
- Task 5: unset `TYPESAFE_BASE_URL`, remove the proxy route.
- Task 4: remove the `extensions:` entry and the `JEV_GUARD_*` environment, delete the pinned clone and `~/.jev-guard/`, restart.
- Task 3: delete `extensions/safety-guard/`, restart.
- Task 2: revert the `.gitignore` negation lines.
- Task 1: remove the `bash.patterns` block from `config.yml`, restart.

Rollback of an uncommitted change is a manual file edit, not a git operation. Nothing in this plan authorises a commit.

## Rejected alternatives

- **`y0usaf/pi-jev`** @ `1b49337` — superseded by `leepokai/jev-guard`, which is better on every axis and demonstrably works here. Its findings are retained above because they are the reason the evaluation criteria exist. Its `jev_ask` tool is genuinely useful and could be loaded on its own if a typed-question tool is ever wanted, independent of any gate.
- **`mejiasd3v`, `tamaratran`, `redrossa` extensions** — rejected on egress (192 KB conversation to Vercel; whole history; prompt plus 8 messages). Not re-examined this revision.
- **`jev-belay`** — Claude Code Stop hook that checks for evidence before trusting a "done" claim. Conceptually close to omp's `session_stop`, but omp's `unexpectedStopDetection: smart` already occupies this slot natively and is already on.
- **`jev-cli` / `jev-axi` / `jevkit`** — maintained CLIs covering `screen`, `verify`, `route`, `rerank` with exit-code gating. Strictly better engineered than the hand-rolled `scripts/jev-ts/`, but they are the same *elective* shape: the model must choose to call them. They would be a sensible replacement if Task 4 is declined and the CLI path is kept.
- **`jev-pref`** — encodes `AGENTS.md` preferences as rules checked against diff hunks. Interesting fit for this repo's code-slop rules, but it is a review tool, not a guard. Out of scope here.

## Verification record (2026-09-20/21, omp 18.2.6)

Executed, with captured output.

**omp extension mechanics (09-20):**

- Synthetic probe extension loaded: `EXT_LOADED setModel=function len=1 setThinkingLevel=function getTL=function setServiceTier=function`; `TL xhigh -> high`; `TOOL_CALL_SEEN bash`; command refused — **confirming a `tool_call` hook blocks even under `approvalMode: yolo`**.
- Control with a bad import: `Failed to load extension … Cannot find package` — proving omp reports load failures loudly, so a silent extension really did load.
- A gitignored extension is still discovered and loaded (`.omp/extensions/disc.ts` under a bare `*` gitignore ran normally). Task 2 is a backup concern, not a loading prerequisite.
- Proposed `.gitignore` block tested in a scratch repo: plans and specs trackable, nested extension dir trackable, `herdr-omp-agent-state.ts` still ignored.

**`y0usaf/pi-jev` @ `1b49337` (09-20/21):**

- `SM_PROBE buildContextEntries=undefined getBranch=function` — the defect.
- Both module-scope imports resolve under omp's compat shim: `IMPORT_OK StringEnum=function Type=object`, `StringEnum(["a","b"])` → `{"type":"string","enum":["a","b"]}`. A review claim that `@earendil-works/pi-ai` lacks `StringEnum`, and a counter-claim that omp refuses to rewrite bare `typebox`, are **both refuted**. `Type.Object(...)` is a lazy builder (`JSON.stringify` → `undefined`), which raised a `registerTool` concern the next item settles.
- Loaded into `.omp/extensions/pi-jev/` with no error, and `jev_ask` worked end-to-end — `0.06` for "the sky is green", model `jev-1.13.0`, 278 in / 23 out. The lazy-schema concern is a non-issue. **The fault is the gate alone**, so a working tool must never be read as a working gate.
- `judgeOutput` (`index.ts:257-285`) does **not** call `lastUserRequest`, so the output judge is fully functional while the gate is dead — and `output.enabled` defaults `true`. Installed as-is with a key present, it gives **zero gate protection and full bash-output egress**: the broken half is the safety half.
- Gate logic driven directly under `bun` against the live API: `rm -rf` destructive 0.96, `~/.ssh` exfil curl exfiltration 0.98, `echo hi` clear; 318–716 ms.

**`leepokai/jev-guard` @ `94996ea` (09-21):**

- CLI against the live API: `jev-guard check Bash '{"command":"rm -rf ~/"}'` → `DENY … risk 3.0/3, approval p=0.98, confidence 0.99`, exit 2.
- **The pi adapter works inside omp.** Loaded with `-e extensions/jev-guard.ts` under `JEV_GUARD_DENY_SCORE=0`, an ordinary `bash: echo hi` was refused with all four probabilities: `risk 0.0/3, approval p=0.07, user-asked p=0.97, from-untrusted p=0.02, confidence 1.00`. Session context is live — it correctly recognised the user had asked for exactly that command.
- **Coverage is not bash-only.** When the agent attempted to reach the same result through `eval`, that call was independently assessed and blocked (`risk 0.2/3, approval p=0.52, user-asked p=0.16`). The hook sees every tool, and a refusal is not trivially routed around.
- Source review: the adapter uses `ctx.sessionManager?.getBranch?.() ?? []` — omp's documented method — which is why it works where `pi-jev` does not. `extensions/jev-guard.ts:25` blocks on `ask` when `!ctx.hasUI`, so headless sessions do not silently allow.
- README content screened before acting on it: `injection 0.04, credential_leak 0.03, verdict clear`.

Not executed: a week of real traffic at default thresholds, and `jev-guard scan-skills` against this agent directory. Those are Task 4 Steps 8 and 10.
