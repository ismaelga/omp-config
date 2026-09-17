"""jev — Jev (TypeSafe System One) decision layer for omp.

Run: python3 ~/.omp/agent/scripts/jev <subcommand> [...]

Subcommands:
  route  — task text -> agent/skill/MCP catalog picks (advisory)
  guard  — hazard-check an outgoing operation (blocking, fail-closed)
  screen — inbound prompt-injection check on external content (advisory)
  stuck  — loop/spin detection from goal + recent actions (advisory)
  ask    — raw typed-judgment escape hatch

Shared contract: exit 0 = clear/proceed, 1 = flagged/stuck (act on it),
2 = API failure (guard treats as flagged; screen/stuck/route degrade to
advisory fallbacks). Every decision is logged to ~/.omp/logs/jev.jsonl
for threshold tuning.

Guard/screen content transits api.typesafe.ai — deliberate user decision
2026-09-17, documented here so it is not re-litigated silently.
"""

import sys

from cli import main

if __name__ == "__main__":
    sys.exit(main())