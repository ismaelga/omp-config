# jev — Jev decision layer (Bun/TS)

Advisory or blocking decisions via TypeSafe System One (Jev). Daemon holds a
warm TLS connection to the API: ~0.3s per call vs ~1.3s fresh-connection CLI.
`TYPESAFE_API_KEY` is in the omp shell env.

```
bun ~/.omp/agent/scripts/jev-ts/jev.ts route  --item "<task text>"     # agent/skill/MCP picks + recommended
bun ~/.omp/agent/scripts/jev-ts/jev.ts guard  --op push --target origin [--content ...] [--note ...]
bun ~/.omp/agent/scripts/jev-ts/jev.ts screen --source <url|tool> --content "<external content>"
bun ~/.omp/agent/scripts/jev-ts/jev.ts stuck  --goal "<goal>" --actions "<one per line>"
bun ~/.omp/agent/scripts/jev-ts/jev.ts ask    --state '<json>' --questions '<json>'
```

`ask` question types: `noul` (yes/no), `choice`, `score`, `bounding_box`.

Exit codes (all subcommands): `0` clear/proceed, `1` flagged/stuck —
act on it, `2` API failure. Guard is fail-closed (2 treated as 1);
route/screen/stuck degrade to advisory fallbacks.

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
  `agents/*.md` + builtins, `skills/*/SKILL.md` with symlink follow,
  `mcp.json`), System One client (one retry on network errors, none on
  HTTP status), decision log, and the five command bodies. Question
  wording is inference input: copied verbatim from the Python original,
  do not rephrase casually.
- **daemon.ts**: `Bun.listen` unix socket at `~/.omp/jev.sock`,
  line-delimited JSON request/response. Bind failure sweeps a stale
  socket file and retries once. Clears its spawn lock once listening.
- **jev.ts**: client. Socket fast path → direct in-process fallback
  (fresh connection) → lazy daemon spawn guarded by `O_CREAT|O_EXCL`
  lockfile so concurrent cold clients spawn exactly one daemon.

Latency measured 2026-09-17: direct 1.3s (0.07s boot + 0.44s TLS +
inference); daemon warm 0.27–0.33s. Cold start costs one direct call.

Replaced the Python package (`scripts/jev/`, removed 2026-09-17) —
same exit contract, same question wording, same log.