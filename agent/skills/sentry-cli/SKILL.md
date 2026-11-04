---
name: sentry-cli
description: Use when checking Sentry issues, events, logs, traces, spans, projects, organizations, or SDK setup, or when creating or updating Sentry issue status.
---

# Sentry CLI

`sentry` (`getsentry/cli`) replaces Sentry MCP. Check auth with `sentry auth status`; if unauthenticated, tell the user to run `sentry auth login`. Legacy `sentry-cli` handles releases/sourcemaps and is not installed.

## Quick reference

| Need | Command |
|---|---|
| Search issues | `sentry issue list kpk-ee/<project> --period 14d --query 'is:unresolved'` |
| Issue details + latest event | `sentry issue view kpk-ee/<project>#PROJ-ABC` |
| Event history + stack traces | `sentry issue events PROJ-ABC --full` |
| Single event | `sentry event view <event-id>` |
| Seer analysis / plan | `sentry issue explain PROJ-ABC` / `sentry issue plan PROJ-ABC` |
| Resolve / reopen / archive | `sentry issue resolve PROJ-ABC` / `sentry issue unresolve PROJ-ABC` / `sentry issue archive PROJ-ABC --until auto` |
| Projects / organizations | `sentry project list kpk-ee/` / `sentry org list` |
| Traces / logs / spans | `sentry trace list kpk-ee/<project> --period 24h`; `sentry log list kpk-ee/<project> --query 'severity:error'`; `sentry span list kpk-ee/<project>/<trace-id>` |
| Details | `sentry trace view kpk-ee/<project>/<trace-id>`; `sentry log view kpk-ee/<project> <log-id>`; `sentry span view <trace-id> <span-id>` |
| SDK docs | `sentry docs query <question>`; `sentry docs list <keywords>` |
| API / schema | `sentry schema --search <keyword>`; `sentry api organizations/ --method GET` |

## Targeting, search, and diagnostics

Selectors: uppercase short ID (`PROJ-ABC`), numeric ID, org/ID (`kpk-ee/API-2F`), org/project#ID (`kpk-ee/api#API-2F`), `@latest`, `@most_frequent`. No `--org`. Auto-detection uses DSN or `.env`; explicit targets require org/project **slugs**, never numeric IDs. Org-wide listing needs `kpk-ee/`.

Search terms imply AND; `OR` is unsupported. Use `key:[a,b]` for alternatives. `--period` accepts `24h`, `14d`, and date ranges. `--json` emits JSON; `--fields` narrows output.

Stack traces: `issue view` includes latest event; `issue events --full` includes full bodies; `event view` shows one event. No `--full-stacktrace` flag. Seer `issue explain`/`issue plan` may take minutes and consume quota; run only when asked or traces are insufficient. Plans require GitHub integration and code mappings.

`trace list`, `log list`, and `span list` accept `--query`/`--period`; log targets `<org>/<project>`. API paths are relative to `/api/0/`: use `organizations/…`, not `/api/0/organizations/…`; method flag is `--method`/`-X`. `--dry-run` previews. `sentry schema` explores endpoints; `sentry docs` answers SDK questions. Discover flags with `sentry --help` or `sentry <command> --help`.

Unauthenticated calls print `Error: Not authenticated. Run 'sentry auth login' first.` and exit 10 (stderr).

## Common mistakes

- Use `issue view`, `issue events --full`, or `event view`, not an invented stacktrace flag.
- Use selectors and slugs, not `--org` or numeric project IDs.
- Org listing: `kpk-ee/`; no `OR`.
- `sentry` differs from `sentry-cli`. Make changes only when requested.
