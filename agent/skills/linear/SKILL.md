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
2. Find its matching Linear issue with `list_issues`, filtered on the `[T-###]` title prefix; create it with `save_issue` if absent, update it otherwise.
3. Copy the task text into the issue description and preserve `deps:`.
4. Map dependencies in Linear as relations: in the same `save_issue` call that creates or updates `[T-002]`, pass `blockedBy: ["T-006"]` — the tool takes identifiers directly.
5. When code lands:
   - post the commit hash/PR link as a `save_comment` on the issue
   - `save_issue` with `state` moved to Done and `links` set to the commit/PR URL
   - mark the checkbox in `docs/TODO.md`.

## Notes

- Write relations through `save_issue` from the start — each is one call with `blockedBy`, so there is nothing to hand-map first.
