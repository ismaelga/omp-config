---
name: linear-cli
description: Use when reading or changing Linear issues or tickets, teams, projects, cycles, milestones, labels, comments, relations, or documents.
---

# Linear CLI

`linear` (schpet/linear-cli) replaces the Linear MCP server. Check `linear auth whoami`; if unauthenticated, tell the user to run `linear auth login` themselves.

## Quick reference

| Need | Command |
|---|---|
| Search all issues | `linear issue query --team ENG --search "login bug" --state started --label bug --assignee sam --json` |
| List mine | `linear issue list --state started --json` |
| View issue | `linear issue view ENG-123 --json` |
| Create issue | `linear issue create --team ENG --title "Fix login" --description-file ./description.md --no-input` |
| Update issue | `linear issue update ENG-123 --state started --assignee sam` |
| Change labels | `linear issue update ENG-123 --add-label bug --remove-label stale` |
| Replace labels | `linear issue update ENG-123 --label bug --label frontend` |
| Create child issue | `linear issue create --team ENG --title "Child task" --parent ENG-100 --no-input` |
| Blocked by | `linear issue relation add ENG-123 blocked-by ENG-456` |
| Comments | `linear issue comment add ENG-123 --body-file ./comment.md`; `linear issue comment list ENG-123 --json` |
| Link / attach | `linear issue link ENG-123 https://example.com`; `linear issue attach ENG-123 ./spec.pdf` |
| List entities | `linear team list --json`; `linear project list --team ENG --json`; `linear label list --team ENG --json`; `linear user list --json` |
| Projects / docs | `linear project view "Mobile launch" --json`; `linear document create --title "Spec" --content-file ./spec.md --team ENG --no-input`; `linear document view DOC-SLUG --raw` |

## Discovery

Discover with `linear --help`, `linear <command> --help`, or `linear schema`. Fallback: `linear api '{ viewer { id name } }'` accepts a GraphQL document argument or stdin; put `query`/`mutation` inside.

Use `--json` for JSON stdout; errors go to stderr. Unauthenticated `linear auth whoami` exits 4 on stderr and prints:
```
✗ Failed to get user info: No API key configured
  Set LINEAR_API_KEY, add api_key to .linear.toml, or run `linear auth login`.
```
Mutate only when requested.

Use `--description-file` / `--body-file` for multiline markdown (both accept `-`); `--no-input` prevents prompts. State types: `triage`, `backlog`, `unstarted`, `started`, `completed`, `canceled`, or a state name/ID, not `open`. `issue list` is mine-only; `issue query` supports team/state/label/assignee/project filters and returns 50 rows unless `--limit all`.
Exit codes: 0 success; 1 other/API; 2 usage; 3 not found; 4 auth; 5 unavailable (a write may succeed); 130 cancelled.

## Common mistakes

- Relation order: `linear issue relation add ENG-123 blocked-by ENG-456` (issue, relation, related); parent flag is `--parent`, not `--parent-ticket`.
- Use `linear issue comment add`, not `linear comment create`. `--add-label`/`--remove-label` preserve labels; repeated `--label` replaces all.
- Mentions require plain Linear URLs, not `@name` or Markdown links. Collapsibles: `+++ [title]` ... `+++`.

