# omp-config

My [omp](https://github.com/can1357/oh-my-pi) (oh-my-pi) user config. The working tree **is** `~/.omp`, the live agent directory — so the repo tracks config in place, no symlink layer.

`~/.omp` also holds credentials (`agent/agent.db` → `auth_credentials`), session transcripts, blobs and caches. `.gitignore` is therefore **default-deny**: `*` ignores everything and each hand-written config path is whitelisted explicitly. Anything new is ignored until you add it.

## What is tracked

| Path | What |
|---|---|
| `agent/AGENTS.md` | User-level context: caveman mode + stack map. Native provider, so it shadows `~/.config/opencode/AGENTS.md`, `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`. |
| `agent/config.yml` | Model roles, provider order, retry/fallback chains, TUI, memory, tool settings. |
| `agent/models.yml` | Override-only: `contextPromotionTarget` per model + corrected `gpt-5.6-luna`/`terra` prices. |
| `agent/mcp.json` | MCP servers. Secrets come from `!echo` shell substitution, never inline. |
| `agent/lsp.json` | LSP overrides. |
| `agent/agents/*.md` | 13 cavecrew subagents + `momus`. |
| `agent/commands/*.md` | Caveman slash commands. |
| `agent/skills/*/SKILL.md` | Vendored skills: superpowers + caveman + `wayfinding`/`prototyping`. Edit freely. |

Everything else under `~/.omp` — `agent.db`, `history.db`, `models.db`, `sessions/`, `blobs/`, `banks/`, `cache/`, `logs/`, `run/` — is state or secrets and stays local.

## Restore on a new machine

```sh
mkdir -p ~/.omp
cd ~/.omp
git init
git remote add origin ssh://git@github.com/ismaelga/omp-config.git
git fetch origin
git checkout -f main
```

Safe to run against an existing `~/.omp`: state files are ignored, so checkout only lays down config.

Then authenticate providers with omp (`/login` or `omp auth`) — no credentials live in this repo.

## Machine-local prerequisites

Not in the repo, needed by the tracked config:

- `OLLAMA_API_KEY` — the `ollama-cloud` provider (`modelRoles.smol`/`tiny`/`vision`/`commit`, and the flat-rate tier most fallback chains land on).
- ChatGPT-plan auth for `openai-codex` (`modelRoles.task` = `gpt-5.6-luna:max`, `slow` = `gpt-5.6-sol:high`), plus Anthropic auth for the `default`/`plan` role (`claude-opus-5:high`).
- `~/.secrets/worldcoin-portal-token` — bearer token for the `worldcoin-developer-portal` MCP server. Absent → that server fails to start; nothing else breaks.

## Notes

- Config changes (`config.yml`, `models.yml`, `mcp.json`, `lsp.json`) require an omp restart.
- Sibling repo: [`opencode-config`](https://github.com/ismaelga/opencode-config), the same setup for opencode. The skills under `agent/skills/` are **copies**, not shared — a skill edited in one repo does not propagate to the other.
- `caveman-stats` is not vendored here: it depends on an opencode plugin hook that has no omp equivalent.
