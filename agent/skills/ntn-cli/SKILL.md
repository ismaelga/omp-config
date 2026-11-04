---
name: ntn-cli
description: Use when an agent needs Notion pages, databases/data sources, blocks, comments, search, users, file uploads, or Notion Workers.
---

# Notion CLI

Use `ntn` instead of Notion MCP; check authentication with `ntn whoami` (`ntn doctor` for setup problems). If unauthenticated, tell the user to run `ntn login`.

| Operation | Command |
|---|---|
| Search page titles | `ntn api v1/search query=roadmap filter:='{"property":"object","value":"page"}'` |
| Read page Markdown | `ntn pages get "$PAGE_ID"` |
| Read page content blocks | `ntn api "v1/blocks/$PAGE_ID/children" page_size==100` |
| Query data source (filtered) | `ntn datasources query "$DATA_SOURCE_ID" --filter '{"property":"Status","select":{"equals":"In progress"}}' --limit 100 --json` |
| Resolve database to data source IDs | `ntn datasources resolve "$DATABASE_ID" --json` |
| Create a page from Markdown | `ntn pages create --parent "page:$PAGE_ID" --content "$(cat ./note.md)" --json` (parent also `data-source:<id>`) |
| Create a data-source page with title + select | `ntn api v1/pages 'parent[data_source_id]='"$DATA_SOURCE_ID" "properties:={\"Name\":{\"title\":[{\"text\":{\"content\":\"New row\"}}]},\"Status\":{\"select\":{\"name\":\"In progress\"}}}"` |
| Update page properties | `ntn api "v1/pages/$PAGE_ID" -X PATCH 'properties:={"Status":{"select":{"name":"In progress"}}}'` |
| Append a paragraph block | `ntn api "v1/blocks/$PAGE_ID/children" -X PATCH 'children[0][type]=paragraph' 'children[0][paragraph][rich_text][0][text][content]=New paragraph'` (`ntn pages edit` REPLACES the whole page) |
| Add a page comment | `ntn api v1/comments 'parent[page_id]='"$PAGE_ID" 'rich_text[0][text][content]=Please review'` |
| List page comments | `ntn api v1/comments "block_id==${PAGE_ID}"` |
| List users | `ntn api v1/users` |
| Upload a file | `ntn files create < ./report.pdf` |
| List Notion Workers | `ntn workers list` |
| Deploy a Worker (only when asked) | `ntn workers deploy` |

## Discovery

Run `ntn --help` and `ntn <group> --help`; inspect API paths with `ntn api v1/<endpoint> --help`, `--spec -X METHOD`, or `--docs -X METHOD`. See `https://developers.notion.com/cli/reference/commands.md` and Notion API endpoint docs for bodies. `ntn api` supplies Authorization and Notion-Version.

## Output and common mistakes

- `--json` requests structured output where supported. Errors go to stderr and return nonzero. An isolated unauthenticated `ntn api v1/users` returned `No workspace selected` and exit 4; run `ntn login` to authenticate.
- Inline `path=value` is a string; `path:=json` preserves types. Body input defaults to POST; use `-X PATCH` for updates. `--data`, stdin JSON, and inline body cannot be combined.
- `pages get` returns Markdown, but full content is block children: follow `next_cursor` with `start_cursor` while `has_more`, and recursively read blocks marked `has_children`.
- Query filters are Notion filter JSON, not expressions. Continue `--start-cursor` from `next_cursor`; there is no `--all` flag. Use `datasources resolve` for a database with multiple data sources, then query the intended data source ID.
- Page properties use the data source's schema: title is `{"title":[{"text":{"content":"..."}}]}`; select is `{"select":{"name":"..."}}`. Rich text uses an array of text objects, not a `--text` shortcut.
- `ntn files list` returns only its first page. Personal access tokens cannot list workspace users (`v1/users`); require a connection with user-information capability. Comment read/write also requires comment capabilities. Writes happen only when the user asked.
