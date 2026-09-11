---
name: grilling
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
---

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round, then wait for the user's answers before the next round.

A round is **one `ask` call**, not a markdown list. The frontier goes in `questions[]`, one entry per decision. The harness tells you to ask sparingly and default to action; this skill overrides that — here the interrogation _is_ the task, and a round that prints questions as prose throws away the selection UI, the recommended defaults, and the structured answers.

| Field | What goes in it |
|---|---|
| `id` | stable snake_case handle for the decision; reuse it if the question comes back |
| `header` | the question's short title |
| `question` | the body — multiple paragraphs are fine; say what hangs on the answer |
| `options` | the candidate answers you actually see, 2–5, each with a `description` carrying its trade-off |
| `recommended` | index of your answer. Every question carries one: a frontier question you have no opinion on is one you have not thought about yet |
| `multi` | `true` where answers can co-exist instead of competing |

Answering outside the options stays open to the user at all times, so a short option set never boxes them in — and never write your own "Other" option.

A question with no enumerable answers ("what does _done_ look like here?") stays in prose beneath the call — but reach for that rarely. Naming 2–5 concrete answers is most of the work of grilling; a question you cannot option is usually a question you have not sharpened.

Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a `task` batch of `scout` agents to find it; don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the scout to report; ask the rest of the frontier now. Scout results auto-deliver, and the full report stays at `agent://<id>`. The _decisions_ are the user's: put each to them and wait.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.
