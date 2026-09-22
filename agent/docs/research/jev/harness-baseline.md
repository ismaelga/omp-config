# Harness baseline: what omp already does about tool count

Written by the parent session, 2026-09-22, against omp 18.2.6 and the live config in `~/.omp/agent/`. The five research agents survey the outside world; this file records what is already true *here*, so nobody proposes building something the harness ships.

**Bottom line**

- omp already has progressive tool disclosure: `tools.xdev` collapses discoverable tools into `xd://<name>` routes carrying a one-line description, with the full JSON schema fetched only on `read xd://<name>`.
- MCP tools go through the same door, exposed as `xd://mcp__<server>_<tool>`.
- That mechanism is **already saturated**: this session's own prompt truncates the MCP route list with `Additional mounted MCP tool mappings omitted: prompt bounded`.
- Truncation appears to be budget-driven, not relevance-driven. That is the actual gap a selector would fill — not "too many tools", but "the wrong ones get dropped".
- The current relevance selector is the user, manually setting `"enabled": false` per server in `mcp.json`.

## What is mounted

`~/.omp/agent/mcp.json` — four live web MCP servers, three disabled:

| Server | Transport | State | Tools mounted (measured via `read xd://`) |
| --- | --- | --- | --- |
| `linear` | `http` → `https://mcp.linear.app/mcp` | live | **79** |
| `sentry` | `http` → `https://mcp.sentry.dev/mcp` | live | **9** |
| `cloudflare` | `http` → `https://mcp.cloudflare.com/mcp` | enabled | **0 devices present** |
| `voyager` | `http` → `http://127.0.0.1:4040/mcp` | enabled (local) | **0 devices present** |
| `notion`, `alchemy`, `slack` | `http` | `enabled: false` | — |

`read xd://` reports **99 mounted tool devices**: 11 internal (`ast_grep`, `ast_edit`, `debug`, `github`, `lsp`, `checkpoint`, `rewind`, `memory_edit`, `retain`, `recall`, `reflect`) and 88 MCP. Two configured servers contribute no devices at all — `cloudflare` and `voyager` are enabled in `mcp.json` but absent from the device list, so they are either failing to connect or exposing nothing, and the session surfaces no error either way.

So the "many remote MCP servers" scenario is not hypothetical here; it is the current configuration, and the route list already overflows the prompt budget with two servers actually contributing tools.

## The native mechanism, from omp's own docs

- `ToolDefinition` carries `loadMode: "essential" | "discoverable"`, defaulting to `"discoverable"` (`omp://extensions.md:452`, `omp://custom-tools.md:153`). Only the canonical built-ins — `read`, `write`, `bash`, `edit`, `glob`, `computer`, `eval`, `task`, `hub`, `learn`, `manage_skill` — default to `"essential"`.
- In a `tools.xdev` session, discoverable built-ins are presented as `xd://<name>` rather than as top-level tools; an explicitly requested tool stays top-level (`omp://tools/checkpoint.md:19`, `omp://tools/recall.md:22`, `omp://tools/memory_edit.md:14`).
- `xd://` lists mounted tool devices; `xd://<name>` returns that device's input documentation; writing JSON to the same URI dispatches it (`omp://tools/read.md:232`).
- MCP tools are bridged as `mcp__<server>_<tool>` (`omp://mcp-server-tool-authoring.md:14`) and surface through the same `xd://` routing.

Net effect: a tool costs one line of description until it is actually used. This is the boring baseline any Jev-based selector has to beat.

## Where the baseline actually breaks

The one-line-per-tool floor is still linear in tool count, and it has already been hit. Two observations from this session's own system prompt:

1. ~60 `xd://mcp__linear_*` routes are listed individually, each with a description line.
2. The list then ends with `Additional mounted MCP tool mappings omitted: prompt bounded`, followed by `Inspect xd:// for exact current paths`.

So with four servers the budget is exhausted and the tail is dropped. Adding more web MCP servers does not degrade gracefully — it silently pushes tools past the cutoff.

**[actionable]** The interesting question for a judgment layer is therefore *not* "which tool should the model call" — the model picks fine from a described list. It is "which subset of the catalogue should occupy the budget this turn", which is a ranking problem over descriptions, and it is currently answered by list order.

## The answer is already mounted: compare Sentry against Linear

Two vendors, one harness, opposite strategies — and the measured difference is the whole argument.

**Linear mounts 79 flat tools.** `save_issue`, `save_comment`, `save_document`, `list_issues`, `list_projects`, `retire_issue_label`, `restore_issue_label`, … Every one costs a description line, forever, whether or not this session touches Linear. This is the half of the catalogue that gets truncated.

**Sentry mounts 9**, two of which are the pattern:

- `mcp__sentry_search_sentry_tools` — "Search the available Sentry MCP tool catalog by name and description."
- `mcp__sentry_execute_sentry_tool` — "Execute an available Sentry MCP tool discovered through search_sentry_tools."

That is server-side tool search plus a generic dispatcher: a catalogue of arbitrary size behind a constant two-line prompt cost, with the selection done by the server that owns the tools and knows their semantics. No classifier, no embedding index on our side, no per-turn judgment call, no third-party descriptions fed to a model for ranking.

**[actionable]** This is the design to copy if tool count becomes a real problem, and it is strictly better than a Jev selector on every axis we care about:

| | Sentry's search+execute | A Jev tool selector |
| --- | --- | --- |
| Prompt cost | constant (2 lines) | constant, but selection list must still be built |
| Per-turn latency | zero unless used | one API round trip every turn |
| Fails | open — search returns nothing, model retries with different words | must be engineered to fail open, and a wrong shortlist is a dead end |
| Untrusted descriptions | never leave the owning server | shipped to a third party and used for ranking |
| Who knows the semantics | the vendor | a general classifier reading one-line descriptions |
| Cost | free | per call, forever |

The corollary is that the lever here is **not** building a selector. It is preferring MCP servers that expose a search+execute facade, and pressing the ones that do not. Linear's 79 flat tools are the problem; Sentry has already solved it for its own surface.

## Constraints any selector must respect

- **Fail open, toward more tools.** A guard that fails open is a hole; a selector that fails closed is a dead end where the model cannot reach a tool and cannot see why. Opposite defaults in the same codebase — do not share the fail policy between them.
- **Tool descriptions from remote servers are untrusted input.** A third-party server can word a description to win selection, or to carry instructions to whatever reads it. A selector consuming them is an injection surface, the same `from_untrusted` problem as the guard plan, arriving through a different door.
- **Per-turn cost is the whole argument.** A selector call on every turn trades main-model prompt tokens for a round trip plus latency. If the saving is a few hundred description tokens, it loses.
- **The cheap baselines must be beaten explicitly:** static curation (what the user does now, by hand), keyword match against the turn's text, embedding similarity over descriptions, and simply raising the prompt budget.

## Not established here

- Whether the `prompt bounded` truncation is order-based, priority-based, or something else — the omp docs searched (`mcp-runtime-lifecycle`, `mcp-config`, `mcp-server-tool-authoring`, `custom-tools`, `extensions`) describe registration and lifecycle but no ranking or budget policy for the route listing. Grep for `prompt bounded` across `omp://` returns nothing.
- The actual mounted tool count. `mcp.json` names the servers, not their tool inventories.
- Whether omp exposes any hook for choosing which discoverable tools are surfaced per turn. If it does not, a selector would need an upstream change, not an extension — which materially raises the cost of the whole idea.
