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
2. Create or find its matching Linear issue.
3. Copy the task text into the issue description and preserve `deps:`.
4. Map dependencies in Linear as relations:
   - If `[T-002] (deps: T-006)`, then `[T-002]` is *blocked by* `[T-006]`.
5. When code lands:
   - add the commit hash/PR link to the issue
   - move the issue to Done
   - mark the checkbox in `docs/TODO.md`.

## Notes

- Prefer manual dependency relations in Linear initially; automation is optional once the mapping is stable.
- Keep live trading work in Elixir; treat Linear as planning/tracking only.
