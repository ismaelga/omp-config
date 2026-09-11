---
name: context-curation
description: "Use in long-running sessions or multi-step agent loops, or when conversation history grows past ~30k tokens."
---

# Context Curation

> "The context window is the bottleneck, not the model. Most agent failures are context-management failures, not reasoning failures." — Andrej Karpathy (recurring 2026 theme)

## Why this skill exists

Modern frontier models have 200k-1M token windows. They still fail. The failure mode is rarely "couldn't reason" — it's "drowning in irrelevant context, lost the thread, made a bad choice on stale information."

You can have the smartest model in the world. If its working memory is full of tool outputs from 30 minutes ago, search results that didn't pan out, and three abandoned implementation attempts, it will perform worse than a smaller model with a clean context.

## The core discipline

Treat context as a working set, not a log. **Curate, don't accumulate.**

A surgeon doesn't keep every tool on the operating table. They keep the ones they need for this step.

## The 4 curation moves

### 1. Summarize and discard

After any multi-step investigation that produced a conclusion, replace the trail with the conclusion.

❌ Bad: 15 file reads, 6 grep searches, 3 LSP calls, then "the bug is in src/auth/jwt.ts line 42 — token validation uses the wrong signing key"

✅ Good: Drop all 24 tool calls from working context. Keep: "Bug: src/auth/jwt.ts:42 uses wrong signing key. Verified via JWT_SECRET env var trace."

### 2. Prune dead branches

When an approach is abandoned, remove its artifacts from the working set. The fact that you tried it and it didn't work is one sentence; the 4000 tokens of tool calls supporting that conclusion are dead weight.

### 3. Separate scratch from canon

- **Canon**: the spec, the eval, the current plan, the final code
- **Scratch**: exploration, attempts, search results, debugging traces

Keep canon in front. Push scratch behind. When in doubt about what to keep, ask: "would I read this again in 5 minutes?"

### 4. Externalize before the context burns

If a piece of information is important and might be needed later, externalize it BEFORE the context gets compacted. Real targets: a file on disk (AGENTS.md, a planning doc, a scratch file in `.omo/`); `local://<name>.md` when a subagent must read it; `artifact://<id>` for tool output that already spilled (spilled output is recoverable, not lost — page it back with `:N-M`). Files and artifacts persist, context doesn't.

## When to curate

- **Every ~30k tokens of conversation growth** — proactive pruning. For background jobs, a settled `hub jobs` snapshot consumes the auto-delivery, and `agent://<id>` / `history://<id>` keep a subagent's full output out of your window until you actually need it.
- **Before any delegated subagent task** — give them a clean working set. A `task` subagent starts blank by construction, so the curation that matters is what you put in `context` and `local://`, not what you prune from your own window.
- **After completing a logical unit of work** — discard exploration debris
- **Before context compaction kicks in** — better that you choose what to keep than the compactor does it for you
- **When you notice the agent referencing stale info** — symptom of bloated context

## Symptoms your context is too dirty

- Agent suggests an approach it already tried and abandoned earlier
- Agent re-reads a file it already read
- Agent quotes old tool output that's been superseded
- Agent's plan references TODOs from a previous task
- Response quality drops noticeably mid-session

When you see any of these: stop, summarize, prune, continue.

## Anti-patterns

- **"Just keep everything, the model has 1M tokens"** — Cost. Latency. Quality degradation. All three suffer.
- **"I'll prune at the end"** — Too late. The agent already made decisions on bloated context.
- **"Compaction will handle it"** — Compaction is automatic damage control. Curation is intentional design.
- **"More context = more accurate"** — Only if it's the *right* context. Wrong context is worse than less context.

## Integration with your setup

- **`checkpoint` / `rewind`** (`checkpoint.enabled: true`) — the active mechanism for move #1. Open `checkpoint {goal}` before exploratory work, close `rewind {report}` after: the intermediate reads, greps, and lsp calls leave the context, only the written report stays.
- **AGENTS.md files** — externalization done right. Use them.

## Quick test

> *"If I summarized this session right now in 200 tokens, would I lose anything I actually need going forward?"*

If yes → keep going, you're already curated.
If no → 80% of your context is dead weight. Summarize and prune.
