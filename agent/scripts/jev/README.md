# jev — Jev decision layer

Advisory or blocking decisions via TypeSafe System One (Jev), ~1-2s and
a few hundred tokens per call. `TYPESAFE_API_KEY` is in the omp shell env.

```
python3 ~/.omp/agent/scripts/jev route  --item "<task text>"     # agent/skill/MCP picks + recommended
python3 ~/.omp/agent/scripts/jev guard  --op push --target origin [--content ...] [--note ...]
python3 ~/.omp/agent/scripts/jev screen --source <url|tool> --content "<external content>"
python3 ~/.omp/agent/scripts/jev stuck  --goal "<goal>" --actions "<one per line>"
python3 ~/.omp/agent/scripts/jev ask    --state '<json>' --questions '<json>'
`ask` question types: `noul` (yes/no), `choice`, `score`, `bounding_box`.
```

Exit codes (all subcommands): `0` clear/proceed, `1` flagged/stuck —
act on it, `2` API failure. Guard is fail-closed (2 treated as 1);
route/screen/stuck degrade to advisory fallbacks.

Every verdict appends to `~/.omp/logs/jev.jsonl` — the tuning corpus.
Guard/screen content transits api.typesafe.ai (user decision 2026-09-17).

Layout: `__main__.py` entry, `cli.py` subcommands, `api.py` System One
client with one retry on network errors, `catalogs.py` live disk loaders
(config.yml disabledAgents, skills frontmatter, mcp.json), `log.py`
JSONL decision log with truncation.