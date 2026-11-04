---
name: cf-cli
description: Use when managing Cloudflare zones, DNS records, Workers, storage, Access applications, Zero Trust, tunnels, or account resources with the `cf` CLI; use skill://wrangler for Workers project development and deployment, and skill://cloudflare for product or architecture choices.
---

# Cloudflare CLI

Use `cf` (`npm install --global cf@latest`) instead of Cloudflare MCP. Check `cf auth whoami`; if unauthenticated, tell the user to run `cf auth login` themselves.

| Task | Command |
|---|---|
| List zones | `cf zones list` |
| List DNS records | `cf dns records list --zone <zone-name-or-id>` (filters: `--type`, `--name`, `--proxied true`) |
| Create DNS record (only when requested) | `cf dns records create --zone <zone-name-or-id> --body '{"type":"A","name":"<host>","content":"<address>"}' --dry-run` |
| Delete DNS record (only when requested) | `cf dns records delete <dns-record-id> --zone <zone-name-or-id> --dry-run` |
| List Workers | `cf workers list` |
| Workers runtime logs/traces (Observability) | `cf o11y telemetry query` (see its `--help`; there is no `cf workers tail`) |
| Workers build logs | `cf builds logs get <build-uuid>` |
| List KV namespaces | `cf kv namespaces list` |
| List R2 buckets | `cf r2 buckets list` |
| Query D1 | `cf d1 query <database-id> --sql 'SELECT 1'` |
| List Access applications | `cf zero-trust access applications list` |
| List tunnels | `cf tunnels list` |
| Tail tunnel logs | `cf tunnels tail <tunnel-id>` |
| List accounts | `cf accounts list` |

Search first: `cf cli search "list Access applications"`. Use generic action/resource terms only, never account IDs, domains, names, or tokens. Example match: `cf zero-trust access applications list`. Inspect it with `cf schema zero-trust access applications list`; use command `--help` for options. Preview with `--dry-run`, execute only if requested. Search docs with `cf docs search "DNS records"`. Repeat the search → schema → dry-run → run loop for other tasks.

JSON is default stdout; messages go to stderr. `--json` is invalid. `--dry-run` previews only. Per Cloudflare's agent docs, a non-interactive destructive command without `--force` prints `Aborted.` and exits 0 with nothing deleted. `--yes` does not exist (`Unknown argument: yes`, exit 1); `-f`/`--force` skips confirmation, only for an authorized write. DNS delete takes a positional record ID, not `--id`; boolean `--proxied true` is valid. `--force` can also be an API parameter, so inspect schema. Account selection: `CLOUDFLARE_ACCOUNT_ID`, then saved per-project selection; multiple accounts without an interactive prompt fail. `--zone` accepts a zone name or ID.

For `wrangler.jsonc`/`wrangler.toml` projects without `cloudflare.config.ts`, use Wrangler for dev/build/deploy (`skill://wrangler`); use `cf` for resource operations.

## Common mistakes

- Exit 0 from `cf auth whoami` may still report unauthenticated; inspect JSON output.
- Neither dry-run nor `Aborted.` means a write occurred; verify state after authorized writes.
- Do not add `--json`, use `--yes`, pass IDs as `--id`, or guess boolean syntax.
- Use `skill://cloudflare` for product/architecture choices; use `skill://wrangler` for Workers project workflows.
