<!-- stack-map-begin -->
# Stack

Harness: omp (oh-my-pi). User config = `~/.omp/agent/` (this repo: `omp-config`, private).

Facts:
- Plans → `.omo/plans/`, specs → `.omo/specs/`, decisions → `.omo/decisions/`, maps → `.omo/maps/`.
- Feature done = project checks pass. Before claiming complete: run test + lint + typecheck + build (whatever the project defines — package.json scripts, Makefile, justfile). Any fail → not done. Evidence before the claim, always.
- Code slop banned: duplicated logic (search before writing), casts to silence types (`as any`, `# type: ignore`), tests that assert nothing real (mock-everything, snapshot-only, testing the mock), dead fallbacks.
- Comments carry what code cannot: why, constraints, invariants, units, provenance, rejected alternatives. Load-bearing test — delete it, does a competent reader lose something only the comment held? Keep those. A comment assembled from the identifiers below it is that line spelled twice. Public API keeps its doc comments (Go exported names, Rust `missing_docs`).
- Reasoning about a change goes in the commit message or the reply. New `.md` files (summary, notes, report, plan) only when asked.
- Committing is not the same permission as pushing. "Never commit unless asked" governs whether work lands at all; once asked, land it in completed units instead of accumulating a dirty tree. Before dispatching each subagent, commit what the previous one finished. Measured cost of not doing this, 2026-09-11 in `lp-hedge`: three subagents ran a banned `git checkout`/`stash` in one session despite an explicit prohibition in every dispatch, one destroyed six files of uncommitted work, and git held nothing — never staged, no stash, 4148 unreachable blobs with zero matches, beams recompiled past it. Recovery was replaying edit calls out of the session JSONL, which expires. Instructions to subagents are advisory; a commit is not.
- Document was asked for: cover the substance, skip the padding — no filler sections, redundant summaries, boilerplate.
- Config changes (`config.yml`, `models.yml`, `mcp.json`, `lsp.json`) need omp restart — remind user.

<!-- Process guidance (cavecrew routing, mandatory review barriers, skill
     prescriptions) removed 2026-08-13 after A/B benchmark in ~/.omp/bench/:
     minimal guidance matched or beat the full config on all 6 tasks at ~1/3
     the turns and tokens, and the agent fleet never activated. Machinery is
     preserved in git history and inert on disk; re-enable via config.yml
     (skills.enabled, task.disabledAgents, advisor.enabled) if a future model
     regime warrants re-measuring. -->

<!-- Comment/doc rules (2026-08-26): positive phrasing and only three lines are
     both deliberate. Rationale, sources, and what was omitted on purpose:
     .omo/research/comment-and-doc-volume.md (untracked). Adding more prose here
     is the one fix the evidence rules out. -->
<!-- stack-map-end -->
