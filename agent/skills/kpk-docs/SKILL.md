---
name: kpk-docs
description: Use when answering questions about KPK (Karpatkey) vaults, funds, onchain accounting, NAV calculator, price feeds, balance adapters, subscriptions/redemptions, or deployment addresses — anything documented at docs.kpk.io
---

# KPK Docs

GitBook site at https://docs.kpk.io — fully agent-readable over plain HTTP. Three mechanisms, no MCP needed:

| Mechanism | URL | Use |
|---|---|---|
| Page index | `https://docs.kpk.io/llms.txt` | Every page URL with one-line summaries |
| Markdown page | `<page-url>.md` | Read any page as clean markdown |
| Ask endpoint | `<page-url>.md?ask=<urlencoded question>&goal=<end goal>` | Direct answer + source excerpts when answer spans pages or isn't on a known page |

## Workflow

1. Fetch `llms.txt` first — 0.3s, gives every candidate URL. Never guess page paths.
2. If question matches 1–2 obvious pages (index summaries are specific), fetch those `.md` pages directly.
3. Otherwise, or when a page doesn't fully answer, use `?ask=` on the closest section's page. Self-contained question; `goal` tailors the excerpt.
4. Broad questions: fetch many candidate pages **in parallel**.

## Parallel fetch

Broad questions hit many candidate pages; HTTP reads serialize in the `read` tool. Use the shipped script:

```bash
python3 skills/kpk-docs/kpk_docs.py index 'nav|price-feed'   # find candidate URLs
python3 skills/kpk-docs/kpk_docs.py fetch <url1> <url2> ...   # parallel page reads
python3 skills/kpk-docs/kpk_docs.py ask <page-url> "<question>"  # ask endpoint
```

Measured: llms.txt + 43 candidate pages in ~3.2s via parallel fetch.

## Gotchas

- `?q=` does not search — returns the same page. `?ask=` is the only query mechanism.
- Section pages (`price-feeds.md`, `balance-adapters.md`) have child pages with per-topic detail — follow them for depth.
- Changelog pages exist per vault (`vaults/vaults/<protocol>/change-log.md`) — check when answering "current" strategy questions.