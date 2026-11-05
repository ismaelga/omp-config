# jev — Jev decision layer (Bun/TS)

Advisory or blocking decisions via TypeSafe System One (Jev). Daemon holds a
warm TLS connection to the API: ~0.3s per call vs ~1.3s fresh-connection CLI.
`TYPESAFE_API_KEY` is in the omp shell env.

```
bun ~/.omp/agent/scripts/jev-ts/jev.ts guard  --op push --target origin [--content ...] [--note ...] [--stage preflight|execute]
bun ~/.omp/agent/scripts/jev-ts/jev.ts screen --source <url|tool> --content "<external content>"
bun ~/.omp/agent/scripts/jev-ts/jev.ts stuck  --goal "<goal>" --actions "<one per line>"
bun ~/.omp/agent/scripts/jev-ts/jev.ts ask    --state '<json>' --questions '<json>'
```

`ask` question types: `noul` (yes/no), `choice`, `score`, `bounding_box`.

Exit codes (all subcommands): `0` clear/proceed, `1` flagged/stuck —
act on it, `2` API failure. Guard is fail-closed (2 treated as 1);
screen/stuck degrade to advisory fallbacks. `guard --stage`: metadata only —
identical verdict either way; `preflight` marks a planning-time check
(recorded, not stopping), `execute` the real op. Stage is echoed in output
and the decision log.

`route` (agent/skill/MCP pick before dispatch) was retired 2026-11-05: against
three-family labels it picked the right agent on 55 of 67 logged items, where
the main model choosing without it got 63 (`docs/plans/2026-11-05-jev-usage.md`).

`screen-extension.ts` is an omp extension (listed under `extensions:` in
`config.yml`) that runs `cmdScreen` on every `read` of a URL and every
`web_search` result, and appends a system reminder when it flags.

Every verdict appends to `~/.omp/logs/jev.jsonl` — the tuning corpus.
Guard/screen content transits api.typesafe.ai (user decisions 2026-09-17 for
elective calls, 2026-11-05 for automatic screening of every external fetch).

## Architecture

```
jev.ts (client) ──unix socket──> daemon.ts ──keep-alive──> api.typesafe.ai
   │  socket missing/dead?           │
   └── direct dispatch + spawn       └── stale-socket sweep on bind
       daemon for next call          (lockfile single-flight spawn)
```

- **core.ts**: System One client (SDK retry policy: 408/429/5xx and network
  errors, up to 2 retries, honoring `Retry-After`, all inside a 15 s
  budget; 4xx fatal), decision log (answering model id + latency per row),
  and the four command bodies.
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