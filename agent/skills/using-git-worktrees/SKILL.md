---
name: using-git-worktrees
description: "Use when feature work needs isolation from the current workspace, or before executing an implementation plan."
---

# Using Git Worktrees

## Overview

Ensure work happens in an isolated workspace. Prefer your platform's native isolation. For work the main thread does itself, create a herdr worktree under `~/.herdr/worktrees/`.

**Core principle:** Detect existing isolation first. Then use native tools. Then a herdr worktree. Never fight the harness.

**Announce at start:** "I'm using the using-git-worktrees skill to set up an isolated workspace."

## Step 0: Detect Existing Isolation

**Before creating anything, check if you are already in an isolated workspace.**

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)
```

**Submodule guard:** `GIT_DIR != GIT_COMMON` is also true inside git submodules. Before concluding "already in a worktree," verify you are not in a submodule:

```bash
# If this returns a path, you're in a submodule, not a worktree — treat as normal repo
git rev-parse --show-superproject-working-tree 2>/dev/null
```

**If `GIT_DIR != GIT_COMMON` (and not a submodule):** You are already in a linked worktree. Skip to Step 2 (Project Setup). Do NOT create another worktree.

Report with branch state:
- On a branch: "Already in isolated workspace at `<path>` on branch `<name>`."
- Detached HEAD: "Already in isolated workspace at `<path>` (detached HEAD, externally managed). Branch creation needed at finish time."

**If `GIT_DIR == GIT_COMMON` (or in a submodule):** You are in a normal repo checkout.

Has the user already indicated their worktree preference in your instructions? If not, ask for consent before creating a worktree — one `ask` call:
`questions[]: [{header: "Workspace", question: "Set up an isolated worktree? It protects your current branch from changes.", options: [{label: "Isolated worktree", description: "Branch + directory away from your checkout; changes merge back when reviewed"}, {label: "Work in place", description: "Work directly in the current checkout on a new branch"}], recommended: 0}]`.
Honor any existing declared preference without asking. If the user declines consent, work in place and skip to Step 2.

## Step 1: Create Isolated Workspace

**You have two mechanisms. Try them in this order.**

### 1a. `task` with `isolated: true` (preferred)

The user has asked for an isolated workspace (Step 0 consent). In omp the
native mechanism is a `task` dispatch with `isolated: true` — the item runs
in an isolated copy of the repo under `worktree.base` (`~/.herdr/worktrees`,
with `task.isolation.enabled` in config.yml): the workspace is created for
you, the subagent works in it, successful changes auto-apply to the parent
checkout, and cleanup is automatic. Name the work in the item's `task` field
and skip to Step 2's baseline expectations when reporting back.

Using `git worktree add` when `isolated: true` fits creates phantom state
your harness can't see or manage.

Only proceed to Step 1b for work the main thread does itself — you cannot
dispatch it to a subagent, so there is nothing for `isolated: true` to run.

### 1b. herdr worktree (main-thread work)

**Only use this if Step 1a does not apply** — the work stays on the main thread.

Every linked worktree lives at `~/.herdr/worktrees/<repo>/<branch-slug>`: herdr's `[worktrees] directory`, the same base omp's `worktree.base` uses. `<repo>` is the primary checkout's directory name; `<branch-slug>` is the branch with `/` replaced by `-`. Never create a worktree inside the repository (`.worktrees/`, `worktrees/`) or beside it.

#### Inside herdr (`test "${HERDR_ENV:-}" = 1`)

```bash
herdr worktree create --cwd "$(git rev-parse --show-toplevel)" --branch "$BRANCH_NAME" --no-focus
# --base <ref> branches from something other than HEAD
```

herdr picks the path, registers the git worktree, and opens it as a workspace without taking the user's focus. Read the checkout path from `.result.workspace.worktree.checkout_path` and run every later command there (`cwd` on tool calls).

#### Outside herdr

Same layout by hand — keep the full path inside the `git worktree add` command:

```bash
MAIN_ROOT=$(git -C "$(git rev-parse --git-common-dir)/.." rev-parse --show-toplevel)
git worktree add "$HOME/.herdr/worktrees/$(basename "$MAIN_ROOT")/${BRANCH_NAME//\//-}" -b "$BRANCH_NAME"
```

**Sandbox fallback:** If worktree creation fails with a permission error (sandbox denial), tell the user the sandbox blocked worktree creation and you're working in the current directory instead. Then run setup and baseline tests in place.

## Step 2: Project Setup

Auto-detect and run appropriate setup:

```bash
# Node.js
if [ -f package.json ]; then npm install; fi

# Rust
if [ -f Cargo.toml ]; then cargo build; fi

# Python
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
if [ -f pyproject.toml ]; then poetry install; fi

# Go
if [ -f go.mod ]; then go mod download; fi
```

## Step 3: Verify Clean Baseline

Run tests to ensure workspace starts clean:

```bash
# Use project-appropriate command
npm test / cargo test / pytest / go test ./...
```

**If tests fail:** Report failures, ask whether to proceed or investigate.

**If tests pass:** Report ready.

### Report

```
Worktree ready at <full-path>
Tests passing (<N> tests, 0 failures)
Ready to implement <feature-name>
```

## Quick Reference

| Situation | Action |
|-----------|--------|
| Already in linked worktree | Skip creation (Step 0) |
| In a submodule | Treat as normal repo (Step 0 guard) |
| Work dispatchable to a subagent | `task` with `isolated: true` (Step 1a) |
| Work stays on the main thread, inside herdr | `herdr worktree create --no-focus` (Step 1b) |
| Work stays on the main thread, outside herdr | `git worktree add ~/.herdr/worktrees/<repo>/<branch-slug>` (Step 1b) |
| Permission error on create | Sandbox fallback, work in place |
| Tests fail during baseline | Report failures + ask |
| No package.json/Cargo.toml | Skip dependency install |

## Common Mistakes

### Fighting the harness

- **Problem:** Using `git worktree add` when the harness already provides isolation
- **Fix:** Step 0 detects existing isolation. Step 1a is `task` with `isolated: true`.

### Skipping detection

- **Problem:** Creating a nested worktree inside an existing one
- **Fix:** Always run Step 0 before creating anything

### Worktree in the wrong place

- **Problem:** `.worktrees/` or a sibling directory needs ignore rules, and herdr never shows it as a workspace
- **Fix:** `~/.herdr/worktrees/<repo>/<branch-slug>`, created by `herdr worktree create` when inside herdr

### Proceeding with failing tests

- **Problem:** Can't distinguish new bugs from pre-existing issues
- **Fix:** Report failures, get explicit permission to proceed

## Red Flags

**Never:**
- Create a worktree when Step 0 detects existing isolation
- Use `git worktree add` when the work could run as a `task` item with `isolated: true`. This is the #1 mistake — if the work is dispatchable, use Step 1a.
- Skip Step 1a by jumping straight to Step 1b
- Create a worktree outside `~/.herdr/worktrees/`
- Skip baseline test verification
- Proceed with failing tests without asking

**Always:**
- Run Step 0 detection first
- Prefer `task` with `isolated: true` over manual git worktrees
- Create main-thread worktrees with `herdr worktree create` when inside herdr
- Auto-detect and run project setup
- Verify clean test baseline
