---
name: decision-log
description: "Use when work involves an architectural decision, technology or model choice, or a non-obvious tradeoff. Logs decision, alternatives, reasoning as a 5-line ADR."
---

# Decision Log

> "The most expensive bug is the architectural decision nobody remembers why was made." — paraphrasing common engineering wisdom

## Why this skill

Every project accumulates decisions:
- "We chose Postgres over SQLite because we'd need concurrent writes later"
- "We use Opus for orchestration but Sonnet for execution because cost"
- "The retry budget is 3 because higher caused thundering herd"
- "We don't use the framework's auth because it doesn't support our SSO"

Six months later, nobody remembers. The decision gets relitigated. Often reversed. Then re-reversed when the original reason re-emerges.

In AI-assisted development this is worse — the AI doesn't know why your codebase looks the way it does. Without a decision log, every refactor risks re-introducing the bug the original decision avoided.

## The format

Lightweight ADR (Architecture Decision Record), 5 sections, <100 words total:

```markdown
## DEC-NNN: <Short title>

**Date:** YYYY-MM-DD
**Status:** Accepted | Proposed | Superseded by DEC-XXX | Deprecated

**Context:** <The problem in 1-2 sentences>

**Decision:** <What we chose, 1-2 sentences>

**Alternatives considered:** <List 2-3 options not chosen, with 1-line reason each>

**Consequences:** <What this commits us to / closes off, 1-2 sentences>
```

That's it. 5 sections. < 100 words. Stored in `docs/decisions/`. Then `retain` the one-line decision plus the file path — a file only helps a session that thinks to look; memory brings it to the next session that logs in the same area. Before logging a new decision, `recall` on the topic so you supersede the old entry rather than duplicate it.

## When to write a decision

Write one when:
- You chose between two non-obvious alternatives
- The decision will be hard to reverse
- A future reader would predictably ask "why was this done this way?"
- The decision is contrary to common wisdom or framework conventions
- You picked a model/variant/provider over an alternative for non-obvious reasons
- You added a workaround for a known bug or limitation

Don't write one when:
- The decision is universal best practice ("we use HTTPS")
- The decision was obvious given the constraints
- The artifact itself (code, config) is self-documenting

A good test: would a smart new team member be confused without the explanation?

## Example: ADRs from your own current setup

These would be the right level of granularity for your project:

```markdown
## DEC-001: Sisyphus orchestrator on Claude Opus 4.7 max

Date: 2026-05-26
Status: Accepted

Context: Sisyphus uses a ~1100-line prompt with complex tool orchestration. Cheaper models degraded behavior on multi-step plans.

Decision: anthropic/claude-opus-4-7 at variant max, with kimi-k2.6 → glm-5.1 → deepseek-v4-pro as fallbacks via OpenCode Go.

Alternatives considered:
- Opus 4.7 high: ~25% cheaper but degrades on long tool chains in maintainer benchmarks
- Kimi K2.6 as primary: 5-6x cheaper but 23pt FlowGraph correctness gap vs Opus
- GPT-5.5: no Sisyphus prompt path exists; would degrade significantly

Consequences: Bound to Anthropic for primary; cost spike risk on heavy ulw sessions; fallback chain mitigates outages.
```

```markdown
## DEC-002: Explore/Librarian on DeepSeek V4 Flash

Date: 2026-05-26
Status: Accepted

Context: Need fast, cheap retrieval/exploration agents. Default canonical was gpt-5.4-mini-fast.

Decision: opencode-go/deepseek-v4-flash primary. Higher SWE-Verified than other "small" models (79.0%), 158K req/month under Go subscription.

Alternatives considered:
- Gemini 3 Flash: weaker on code-related research
- gpt-5.4-mini: canonical default but no Go-included pricing
- Claude Haiku 4.5: 3x more expensive at our volume

Consequences: Dependent on OpenCode Go availability; degrades gracefully via fallbacks.
```

## The discipline

### When AI is making the decision

When delegating to an agent for an architectural choice, dispatch via `task` with an `outputSchema` for the decision record (context, decision, alternatives, consequences). The entry forces the agent to justify in writing, which catches sloppy reasoning. The main thread then writes the ADR file and calls `retain` — a subagent's memory is not the parent's to manage.

### When you're making the decision

Write the entry FIRST, then implement. Forces clarity. If you can't write the alternatives + reason, you haven't fully thought through the decision.

### When you reverse a previous decision

Don't delete. Mark the old one Superseded-by and create a new entry. The history is the value.

## Naming

`DEC-NNN-short-title.md` in `docs/decisions/`.

`NNN` is sequential, never reused. If DEC-007 is superseded, DEC-007 stays in place (marked Superseded), DEC-024 is the new one.

## What decisions to log in a typical project

Roughly the categories that matter:
- **Stack choices**: language, framework, database, hosting
- **Model/variant choices**: per agent, per category
- **Architectural patterns**: monolith vs services, sync vs async, etc.
- **Trade-off resolutions**: latency vs cost, simplicity vs flexibility
- **Workarounds**: bug X in library Y, why we use Z instead
- **Explicit non-choices**: "we deliberately do NOT do X because..."

## What NOT to log

- Naming conventions (those go in style guide, not ADR)
- Refactors that didn't change the architecture
- Bug fixes (unless they reveal a structural decision)
- Things settled by team convention without controversy

## Anti-patterns

- **Long ADRs.** Past ~200 words you're writing a design doc, not an ADR. Different tool.
- **ADRs without alternatives.** "We chose X" without "we considered Y and Z" is hindsight, not reasoning.
- **Updating accepted ADRs in place.** Mark Superseded, create new entry. History is the asset.
- **No status field.** Without status, readers can't tell if the ADR is current.
- **Writing ADRs at the end.** They're meant to capture decisions at the time they're made.

## Integration with your skills

- **`writing-plans`** (superpowers) → Plans should reference relevant ADRs
- **`docs/specs/`** → A spec's "decisions" section can reference ADRs
- **`pre-mortem`** → Surface decisions that should be ADR'd before they're forgotten
- **repo `AGENTS.md`** (auto-loaded by omp) → link to the decision log so every session starts knowing it exists.

## Single-sentence test

> *"If I left the team tomorrow, would the person inheriting this codebase understand why it looks the way it does?"*

If no → start logging decisions. Backfill the top 5-10 most important ones from memory.
If yes → keep logging as new decisions appear.
