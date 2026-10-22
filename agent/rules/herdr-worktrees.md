---
description: Linked git worktrees live under ~/.herdr/worktrees, created through herdr
# Fires on `git worktree add` / `omp worktree add` whose command segment never
# names .herdr/worktrees. The match must reach the segment's end (; & | newline,
# or the closing quote of the JSON string) so a call still streaming its path
# cannot fire early; the per-character lookahead halts at the first
# `.herdr/worktrees`, which then never reaches an end and fails. Patterns read
# raw JSON tool arguments: `\"` is a quote inside the command, a bare `"` ends
# it, and a newline arrives as a literal `\n`, which `\b` alone misses.
condition:
  - '(?:\b|(?<=\\n))(?:git(?:\s+-[cC]\s+\S+|\s+--\S+)*\s+worktree|omp\s+(?:worktree|wt))\s+add\b(?:(?!\.herdr/worktrees)(?:[^;&|\n\\"]|\\[^n]))*(?=[;&|\n"]|\\n)'
scope: "tool:bash, tool:eval"
---
Linked worktrees go under `~/.herdr/worktrees/<repo>/<branch-slug>`, never inside the repository (`.worktrees/`, `worktrees/`) or beside it. Inside herdr (`HERDR_ENV=1`) create them with herdr so the checkout opens as a herdr workspace:

`herdr worktree create --cwd <repo-root> --branch <branch> [--base <ref>] --no-focus`

Take the checkout path from the JSON response. Outside herdr keep the same layout: `git worktree add ~/.herdr/worktrees/<repo>/<branch-slug> -b <branch>`, where `<repo>` is the primary checkout's directory name and `<branch-slug>` is the branch with `/` replaced by `-`.
