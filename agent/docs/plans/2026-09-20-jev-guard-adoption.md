# Tool-Call Guard Adoption Plan

**Goal:** Close the gap omp 18.2.6 does not cover natively — screening of tool calls before they execute — and decide what, if anything, replaces the custom Jev CLI stack.

**Status:** Plan only. Nothing here has been applied to `~/.omp/agent`.

**Revision:** Rewritten 2026-09-20 after a four-lens review (executability, claim interrogation, threat model, fact-check). The first draft recommended adopting `y0usaf/pi-jev` as a config-only change. **That premise was refuted** — see "What the review overturned". The recommendation has changed accordingly.

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
| **C. `y0usaf/pi-jev`** @ `1b49337` | 0.3–0.7 s per judged call | semantic intent: exfiltration, scope, impact | gate returns nothing on every call until patched; wedges on a stalled endpoint; no persistence; egress incl. `user_request` and, by default, bash *output* | **no — needs source patch** |

The first draft ranked C first. That was wrong. **A + B is the recommended floor**: both are deterministic, neither touches the network, neither sends anything anywhere, and B's code already exists and passed its own suite. C becomes an optional semantic layer *after* its defects are fixed and its **gate** — not merely its `jev_ask` tool — has been observed producing a verdict inside omp.

A and B are not redundant with C, and C cannot replace `screen` for either of them.

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

### Task 4 (optional): Patch and evaluate the semantic layer (option C)

Only after Tasks 1 and 3. Every step here exists because the review found a defect.

- [ ] **Step 1:** Acquire the exact audited ref — `git clone https://github.com/y0usaf/pi-jev && git checkout 1b493375ef52e6d8f59dfe83e84402b024536625` (2026-09-19, `@y0usaf/pi-jev` 0.2.0, manifest `pi.extensions: ["./src/index.ts"]`). Vendor `src/{client,config,gate,index,output}.ts` into `extensions/jev-guard/`, recording URL, SHA, and date in a header comment.
- [ ] **Step 2:** **Re-anchor before patching.** Every line number below is valid only at `1b49337`. If you take a newer ref, re-confirm all four findings against it first: `index.ts:625` `buildContextEntries()`, `index.ts:319-338` the swallow, `client.ts:15-16` `20_000`/`2`, `gate.ts:101-113` the `cwd` + `user_request` payload, and `config.ts:126-127` `output.enabled` defaulting true. A patch applied to shifted lines is worse than no patch.
- [ ] **Step 3:** **Read the code before running it.** It executes in-process on every tool call with full harness privileges, and `tool_call` can rewrite tool `input`, not merely block — an import grep is not a review.
- [ ] **Step 4:** Patch `lastUserRequest()` (`index.ts:624-625`): replace `ctx.sessionManager.buildContextEntries()` with the documented `getBranch()`, or drop `user_request` entirely. Dropping it is the better default — it removes the 1200-char conversation excerpt from egress at the same time.
- [ ] **Step 5:** Add a persistence sink: append every verdict as JSONL to `~/.omp/logs/jev-guard.jsonl`. Without this, Step 9 has no data. Log `no-verdict` outcomes too — the current failure is invisible precisely because nothing records a non-answer.
- [ ] **Step 6:** Redact before transmit in the vendored `client.ts`: strip `Authorization:`/`Bearer` values, `sk-`-style tokens, and `--password`/`--token` arguments from `arguments` before the payload leaves the process. The gate needs command *shape*, not credential values. Pairs naturally with the persistence patch above — both touch the same egress path.
- [ ] **Step 7:** Set `timeoutMs` ≤ 8000 and `retries: 0` in `pi-jev.json`, so the worst case stays inside omp's 30 s handler budget and a stalled endpoint cannot wedge every gated tool.
- [ ] **Step 8:** Configure shadow mode and restart:

```json
{
  "timeoutMs": 8000,
  "retries": 0,
  "gate": {
    "enabled": true,
    "mode": "shadow",
    "tools": ["bash", "write", "edit"],
    "cacheSeconds": 120,
    "blockOn": { "destructive": 0.9, "exfiltration": 0.7, "beyondScope": 0.85, "impact": 2.5 }
  },
  "output": { "enabled": false }
}
```

`output.enabled` is **false** deliberately — it defaults to `true`. The output judge ships the first 2000 chars of every bash result to TypeSafe. Turn it on only as a separate, explicit decision.

- [ ] **Step 9:** Confirm the gate is actually alive before trusting silence. `/jev last` must show a gate verdict and `jev-guard.jsonl` must have rows *from a real bash call*, not merely from `jev_ask`. Note that `jev_ask` working proves nothing about the gate — at `1b49337` the tool worked perfectly while the gate returned nothing on every call. Silence meant "inert", not "clean".
- [ ] **Step 10:** Run a week in shadow. Tabulate true vs false positives from the JSONL, **and** count `no-verdict` results — a rising no-verdict rate is a silent disarm and must gate the decision to enforce.
- [ ] **Step 11:** Only then consider `mode: enforce`, with `blockWithoutUI: true` if the verification run is headless (otherwise the test is vacuous — headless never blocks without it).

**Acceptance:** a measured false-positive rate and no-verdict rate over real traffic, from durable rows, before any enforcement.

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
- [ ] **Step 2:** **Keep `screen`.** Nothing in this plan replaces prompt-injection screening of fetched content; the gate never sees it, and in the logged corpus `screen` had the *highest* flag rate of any command. Either keep the CLI path plus its prompt clause, or port it to a `tool_result` hook over `read`/`web_search`/MCP output first.
- [ ] **Step 3:** The guard clause is already gone (Task 3 Step 4). Remove nothing further from `APPEND_SYSTEM.md` except clauses whose mechanism is now a hook. **Keep the `screen` clause and keep the egress-hygiene rule** ("never pass actual secret values") — the latter is the only standing control over what reaches a third party in a command line.
- [ ] **Step 4:** Keep `skills/typesafe-ai/` — vendor MIT skill for *building* on TypeSafe, unrelated to the harness guard.
- [ ] **Step 5:** Keep `~/.omp/logs/jev.jsonl` as the historical corpus.

**Acceptance:** no orphaned command bodies without callers; `screen` still reachable; the hygiene rule still present.

## Rollback

Per task, in reverse:

- Task 6: `git checkout` the deleted files — **only if they were tracked and committed**; `scripts/jev-ts/*.ts` is whitelisted so it is recoverable, but verify before deleting, not after.
- Task 5: unset `TYPESAFE_BASE_URL`, remove the proxy route.
- Task 4: delete `extensions/jev-guard/` and `pi-jev.json`, restart.
- Task 3: delete `extensions/safety-guard/`, restart.
- Task 2: revert the `.gitignore` negation lines.
- Task 1: remove the `bash.patterns` block from `config.yml`, restart.

Rollback of an uncommitted change is a manual file edit, not a git operation. Nothing in this plan authorises a commit.

## Verification record (2026-09-20, omp 18.2.6)

Executed, with captured output:

- Synthetic probe extension loaded: `EXT_LOADED setModel=function len=1 setThinkingLevel=function getTL=function setServiceTier=function`; `TL xhigh -> high`; `TOOL_CALL_SEEN bash`; command refused — **confirming a `tool_call` hook blocks even under `approvalMode: yolo`**.
- Control with a bad import: `Failed to load extension … Cannot find package` — proving omp reports load failures loudly, so pi-jev's silence meant it *did* load.
- `SM_PROBE buildContextEntries=undefined getBranch=function` — the defect behind Task 4 Step 4.
- **pi-jev's two module-scope imports both resolve under omp's compat shim** — `IMPORT_OK StringEnum=function Type=object`, with `StringEnum(["a","b"])` producing `{"type":"string","enum":["a","b"]}`. A review claim that `@earendil-works/pi-ai` lacks `StringEnum`, and a counter-claim that omp refuses to rewrite bare `typebox`, are **both refuted**. The shim's `Type.Object(...)` is a lazy builder rather than a plain object (`JSON.stringify` → `undefined`); that raised a concern about `registerTool` schemas, which the next item settles.
- **The real extension, vendored at `1b49337` into `.omp/extensions/pi-jev/` and loaded by omp: no load error, and `jev_ask` worked end-to-end** — returned `0.06` for "the sky is green" from model `jev-1.13.0`, 278 in / 23 out tokens. So the lazy-schema concern is a non-issue, the compat shim is sufficient, and the API path functions from inside omp. **The fault is the gate alone**, which is why `jev_ask` succeeding must never be read as the gate being alive.
- A gitignored extension is still discovered and loaded (`.omp/extensions/disc.ts` under a bare `*` gitignore ran normally). Task 2 is a backup concern, not a loading prerequisite.
- y0usaf gate logic driven directly under `bun` against the live API: `rm -rf` destructive 0.96, `~/.ssh` exfil curl exfiltration 0.98, `echo hi` clear; 318–716 ms.
- Proposed `.gitignore` block tested in a scratch repo: plans and specs trackable, `jev-guard/*.ts` trackable, herdr still ignored.

Not executed: the **patched** extension producing a gate verdict inside omp. That is Task 4 Step 9, and nothing about option C should be trusted until it passes.
