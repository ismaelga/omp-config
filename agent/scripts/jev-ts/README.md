# jev — Jev decision layer (Bun/TS)

Advisory or blocking decisions via TypeSafe System One (Jev). Daemon holds a
warm TLS connection to the API: ~0.3s per call vs ~1.3s fresh-connection CLI.
`TYPESAFE_API_KEY` is in the omp shell env.

```
bun ~/.omp/agent/scripts/jev-ts/jev.ts route  --item "<task text>"     # agent/skill/MCP picks + recommended
bun ~/.omp/agent/scripts/jev-ts/jev.ts route  --item "<task text>" --human-gate "<human step>"  # blocking step needs a human
bun ~/.omp/agent/scripts/jev-ts/jev.ts guard  --op push --target origin [--content ...] [--note ...] [--stage preflight|execute]
bun ~/.omp/agent/scripts/jev-ts/jev.ts screen --source <url|tool> --content "<external content>"
bun ~/.omp/agent/scripts/jev-ts/jev.ts stuck  --goal "<goal>" --actions "<one per line>"
bun ~/.omp/agent/scripts/jev-ts/jev.ts ask    --state '<json>' --questions '<json>'
```

`ask` question types: `noul` (yes/no), `choice`, `score`, `bounding_box`.

Exit codes (all subcommands): `0` clear/proceed, `1` flagged/stuck —
act on it, `2` API failure. Guard is fail-closed (2 treated as 1);
route/screen/stuck degrade to advisory fallbacks.

`route --human-gate`: the item's blocking step needs a human (wallet
signature, passphrase, console). `recommended` is always "none"; the
`delegable_share` score (0–1, asked only with this flag) says whether the
software half is worth delegating. `guard --stage`: metadata only —
identical verdict either way; `preflight` marks a planning-time check
(recorded, not stopping), `execute` the real op. Stage is echoed in output
and the decision log.

Every verdict appends to `~/.omp/logs/jev.jsonl` — the tuning corpus.
Guard/screen content transits api.typesafe.ai (user decision 2026-09-17).

## Architecture

```
jev.ts (client) ──unix socket──> daemon.ts ──keep-alive──> api.typesafe.ai
   │  socket missing/dead?           │
   └── direct dispatch + spawn       └── stale-socket sweep on bind
       daemon for next call          (lockfile single-flight spawn)
```

- **core.ts**: catalogs (agents/skills/MCP loaded live from disk —
  `agents/*.md` + builtins, `skills/*/SKILL.md` with symlink follow and
  `disable-model-invocation` skills dropped, `mcp.json`), System One client
  (SDK retry policy: 408/429/5xx and network errors, up to 2 retries,
  honoring `Retry-After`, all inside a 15 s budget; 4xx fatal), decision
  log (answering model id + latency per row), and the five command bodies.
  Question wording is inference input: copied verbatim from the Python
  original, do not rephrase casually.
- **daemon.ts**: `Bun.listen` unix socket at `~/.omp/jev.sock`,
  line-delimited JSON request/response, buffered per connection (requests
  span several reads past ~8 KB). Bind failure sweeps a stale
  socket file and retries once. Clears its spawn lock once listening.
- **jev.ts**: client. Socket fast path → direct in-process fallback
  (fresh connection) → lazy daemon spawn guarded by `O_CREAT|O_EXCL`
  lockfile so concurrent cold clients spawn exactly one daemon; a lock
  older than 30 s is a spawn that died before binding and is swept.

Latency measured 2026-09-17: direct 1.3s (0.07s boot + 0.44s TLS +
inference); daemon warm 0.27–0.33s. Cold start costs one direct call.

Replaced the Python package (`scripts/jev/`, removed 2026-09-17) —
same exit contract, same question wording, same log.