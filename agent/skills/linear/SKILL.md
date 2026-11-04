---
name: linear
disable-model-invocation: true
description: Create/update Linear issues from this repo's docs/TODO.md task IDs (T-###), including mapping dependencies, syncing status, and adding links to commits/PRs.
metadata:
  short-description: Sync TODOs to Linear
---

# Linear

Use this skill when you want to turn `docs/TODO.md` into Linear issues and keep them in sync.

## Conventions (Repo)

- Each actionable top-level task has an ID like `[T-001]` and a dependency field like `(deps: T-006)`.
- One `[T-###]` maps to one Linear issue.
- Linear issue title format: `[T-001] Alerts refresh`.
- Linear issue description starts with:
  - `deps: T-006, T-010` or `deps: -`
  - links to relevant files/modules
  - acceptance criteria checklist

## Workflow

1. Open `docs/TODO.md` and pick the next `P0`/`P1` task.
2. Find its matching issue with `linear issue query --team TEAM --search "[T-###]" --json` and note its Linear key (e.g. `ENG-42`); `T-###` is only the title prefix, never an issue ID. Create it if absent, update it otherwise, with the commands in [skill://linear-cli](skill://linear-cli).
3. Copy the task text into the issue description and preserve `deps:`.
4. For each `deps:` entry, look up that task's Linear key the same way, then `linear issue relation add <KEY> blocked-by <DEP-KEY>`.
5. When code lands: `linear issue comment add <KEY> --body "<commit/PR URL>"`, `linear issue link <KEY> <URL>`, `linear issue update <KEY> --state completed`, then mark the checkbox in `docs/TODO.md`.
