# omp Tool Mapping

Skills speak in actions ("dispatch a subagent", "create a todo", "read a file"). On omp these resolve to the tools below.

| Action skills request | omp equivalent |
| --- | --- |
| Dispatch a subagent (`Subagent (general-purpose):` template) | `task` with a `tasks[]` array — agent types `scout` (read-only investigation), `reviewer`, `security-reviewer`, `task` (general). No per-spawn `model` field; model comes from the agent type and `task.agentModelOverrides` in config.yml |
| Task tracking ("create a todo", "mark complete") | the `todo` tool |
| Isolated workspace ("git worktree add …") | `isolated: true` on a `task` item — a dedicated worktree that auto-applies on success |
| Long-running process, server, or REPL | `hub start {name, application, args[], ready:{log?, port?}}` — never a backgrounded `bash` |
| Ask the user a question | the `ask` tool — `questions[]` with 2–5 options each; the UI appends "Other (type your own)" |
| Large payload to a subagent | `local://<name>.md` — subagents read the parent's `local://` root |
| A subagent's result | `agent://<id>` (full output, `?q=.field` for one field), `history://<id>` for its transcript |
| Skill addressing | `skill://<name>` — never the `superpowers:` prefix, which resolves to nothing in omp |

## Subagents

One `task` call takes the whole batch: a shared `context` string plus one item per subagent (`{name, agent, task}`). Items are independent slices; results auto-deliver, no polling. Read-only investigation runs on `scout`. Give each item everything it needs — subagents start blank, with no conversation history.

## Long-running processes

Anything that outlives one command — a dev server, a watcher, a REPL you drive over stdin — belongs to `hub` (`start`/`logs`/`send`/`stop`/`restart`), not a backgrounded shell call. Readiness MUST be observed via `ready.log` (a JS RegExp) or `ready.port` before use.