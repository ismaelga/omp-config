---
name: wayfinding
description: "Use when an effort is too big and foggy for one design session - destination not visible, decisions depend on decisions. Not for what one brainstorming session settles."
---

# Wayfinding

Some efforts cannot be designed in one sitting: you cannot name the third decision until the
first two are answered, and the whole chain does not fit in one context window. Wayfinding
charts the route as a **map file** on disk, then resolves its **open questions** one session at
a time until nothing is left to decide.

A question resolves to a **decision**, never to a deliverable. Wayfinding plans. It does not build.

## Gate: do you need a map?

Answer both before creating anything:

1. **Is the destination reachable in one design session?** If yes → use `brainstorming`, stop reading.
2. **Does any question depend on the answer to another question?** If no → use `brainstorming`.

Chart a map only when the answers are **no, then yes**: the effort spans sessions AND the
questions are ordered. Any other combination means no map — say so, name which gate question
failed, and hand the effort to `brainstorming`. Charting a small effort costs more than it saves.

## Destination first

Name the destination before any question exists. It is one or two lines describing what
reaching the end of this map looks like — a spec ready for `writing-plans`, a decision locked
before planning starts, or a migration whose shape is settled. The destination fixes the scope:
everything past it is out of scope, permanently.

If you cannot state the destination, you are not ready to chart. Run `brainstorming` breadth-first
until you can.

## The map

One file, canonical, human-editable: `.omo/maps/YYYY-MM-DD-<effort>.md`.

The map is an **index**, not a store. Each resolved question keeps its detail in its own
resolution block; the index carries a one-line gist so a fresh session can judge relevance
without loading everything.

```markdown
# <Effort name>

**Destination:** <what the end of this map looks like — 1-2 lines>

**Skills for this effort:** <skills every session on this map should invoke>

## Open questions

<!-- the frontier: takeable now, no unresolved blocker. One per session. -->

- [ ] Q4 (decision) — <the question, sharp enough to answer> — blocked by: none
- [ ] Q5 (research) — <the question> — blocked by: none

## Blocked

- [ ] Q6 (prototype) — <the question> — blocked by: Q4

## Decisions so far

<!-- index of resolved questions, newest last -->

- **Q1 — <question>** → <one-line answer>. Detail: `#q1` below.
- **Q2 — <question>** → <one-line answer>. Detail: `#q2` below.

## Not yet specified

<!-- fog: in-scope questions you can see coming but cannot phrase sharply yet -->

- <area to revisit once Q4 lands>

## Out of scope

<!-- ruled past the destination. Never graduates. -->

- <thing> — out because <reason>.

## Resolutions

### q1 — <question>

<the answer, the reasoning, and anything a later session needs. Assets get linked, not pasted.>
```

## Question types

Every question is **HITL** (needs the human's own words) or **AFK** (you resolve it alone).
Label it in the map. You NEVER answer a HITL question on the human's behalf.

| Type | Mode | Resolve with |
|---|---|---|
| `decision` | HITL | `brainstorming` — one question per message, your recommendation attached |
| `research` | AFK | `task` + `scout`; findings land in the resolution block. |
| `prototype` | HITL | `prototyping` — throwaway artifact, human reacts, verdict is the resolution |
| `task` | either | Manual work that unblocks a decision (provision access, move data so its shape is visible). Not product work. |

A `task` is AFK only if you can finish it with the access and authority you already have, and its
outcome is a fact rather than a judgement. Anything needing the human's credentials, money,
account, or approval is HITL: hand them a precise checklist and wait. When unsure, it is HITL.

`research` questions are the only ones you may resolve in parallel and in batches — fan them out
with one `task` call. Everything else is one per session.

## Fog, not pre-slicing

The map is deliberately incomplete. Do not chart what you cannot yet see.

**Question or fog?** The test is whether you can state it precisely now — NOT whether you can
answer it now.

- Sharp question, even if blocked → **Open questions** or **Blocked**.
- Cannot phrase it sharply → **Not yet specified**. One patch of fog may later graduate into
  several questions, or none.

Resolving a question clears the fog ahead of it: graduate whatever became sharp into new
questions and delete that patch from **Not yet specified**. Fog only gathers *toward* the
destination — anything past the destination goes to **Out of scope** and never returns.

## One question per session

Resolve exactly one non-research question per session, then stop and report. Two reasons, both
load-bearing:

- Answer quality falls off a cliff as context fills. Past roughly 120k tokens the model's
  attention is strained and its decisions get worse ([aihero.dev, "9 things people get wrong"](https://www.aihero.dev/things-people-get-wrong-with-grill-me-and-grill-with-docs)).
- The map on disk is the state. A session that resolves five questions writes five resolutions
  from one degraded context, and the human reviews none of them in isolation.

Recording a resolution means: write the resolution block, move the question into
**Decisions so far** with its gist, graduate fog, re-check blockers, then stop.

## Hard bans

<HARD-GATE>
- You NEVER write an "this effort carries execution" override into the map. Only the human's own
  words can authorize building, and they go in the map verbatim, attributed. An agent that grants
  itself execution licence and reads it back next session is the documented failure mode of the
  method this skill is ported from ([mattpocock/skills#683](https://github.com/mattpocock/skills/issues/683)
  — 25 tickets in, the agent built against a live server on its own authority).
- Building the product is NEVER evidence. A `prototype` question may produce throwaway code that
  answers one named question; it may not produce the thing itself. The test: **would this code
  survive the answer?** If yes, it is the product, not a prototype — stop
  ([#703](https://github.com/mattpocock/skills/issues/703) — seven implementation PRs merged
  while the gate they were supposed to inform was still open).
- A human's execution authorization is **narrow**: it covers the specific thing they named, and
  only after the question that motivated it is resolved. It NEVER converts the map into a build
  queue, NEVER licenses work on questions still open, and NEVER skips Exit — the rest of the map
  still finishes as decisions, then spec, then plan. "The human said this map carries execution"
  is not authority to start building tonight.
- You NEVER answer a HITL question yourself. Look up facts; put decisions to the human.
</HARD-GATE>

## Exit

The map is done when **Open questions**, **Blocked**, and **Not yet specified** are all empty.
Then, in a fresh session:

1. Write the spec from **Decisions so far** to `.omo/specs/YYYY-MM-DD-<effort>-design.md`. Every
   decision carries its resolution gist — a spec that drops the reasoning gets re-litigated
   during implementation.
2. `writing-plans` → `.omo/plans/`, then `subagent-driven-development`.

If the map stalls — the same question reopens twice, or the destination moves — the destination
was wrong. Redraw it as a fresh effort; do not resume a map whose destination changed.

## Sharing the map with humans

The map file is canonical. If other people need to see the frontier, mirror it to the repo's
issue tracker: map as parent issue, questions as sub-issues, `blocked by` as native dependencies
(`gh api repos/{owner}/{repo}/issues/{n}/sub_issues`,
`gh api repos/{owner}/{repo}/issues/{n}/dependencies/blocked_by` — read paths confirmed on
gh 2.96; exercise the write paths against a scratch repo before trusting them). Mirror one way
only: the file leads, the tracker follows. Two writable copies of the same map desynchronize
within a day.
