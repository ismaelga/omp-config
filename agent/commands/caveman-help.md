---
description: Quick reference card for caveman modes, slash commands, and triggers
---
Show the caveman quick-reference card.

| Command | What |
|---|---|
| `/caveman` | Activate at default level (full) |
| `/caveman lite` | Light compression — ~30% tokens dropped |
| `/caveman ultra` | Maximum compression |
| `/caveman wenyan[-lite\|-ultra]` | Classical Chinese compression |
| `/caveman off` | Deactivate |
| `/caveman-commit` | Terse commit message |
| `/caveman-review` | One-line review findings |
| `/caveman-compress <file>` | Compress a Markdown file |

Caveman is on by default: `~/.omp/agent/APPEND_SYSTEM.md` carries the caveman
block, rendered at the very end of the system prompt, so every session starts at
`full`. Change the default by editing that file; switch per-session with
`/caveman <level>`.

Natural language also works: "turn on caveman", "stop caveman", "normal mode".

Code, commits, security warnings: caveman drops out automatically.
