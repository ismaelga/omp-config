---
name: interrogate
description: Adversarial multi-model review panel — four reviewers from four model families stress-test a changeset or PR against a fixed prompt, rubric, and code-quality lens, then the lead synthesizes an intent-anchored verdict with act-on / consider / noted / dismissed buckets. Never auto-applies changes.
disable-model-invocation: true
---

# Interrogate

Spawn one reviewer per configured model to adversarially review code changes. Each model gets the same prompt and rubric. The adversarial signal comes from model diversity, not assigned personas.

The deliverable is a synthesized verdict. Do NOT auto-apply changes.

## Step 1, Determine Scope

Identify what to review from context:

- If the user points at specific files or a diff, use that
- If on a feature branch, run `git diff main...HEAD` (or the appropriate base branch) for the full changeset
- If reviewing a GitHub PR, read `pr://<N>/diff` for the file list and per-file slices, or `pr://<N>/diff/all` for the whole diff
- If the user's message references recent work, gather the relevant files

Package the diff (or file contents) plus any surrounding context files the reviewers need to understand the code. Reviewers are spawned cold: they inherit none of this conversation. Write the package — intent statement, diff, rubric, code-quality lens — to `local://interrogate-package.md` and hand each reviewer that path. Never paste the diff inline in a task prompt; a large diff blows the subagent's context before it reads a line of the rubric.

## Step 2, State the Intent

Before spawning reviewers, state the intent explicitly. Derive this from:

- The user's message
- Commit messages
- PR description if one exists
- The code itself

Write one clear paragraph. If you're unsure about the intent, ask the user before proceeding.

## Step 3, Spawn Reviewers

Launch all reviewers in **one `task` tool call** — a single `tasks[]` batch of four items. They run in parallel; results auto-deliver. The `task` tool has no per-item `model` field, so model diversity comes from the agent each item runs on. Each of those four agents is meant to be pinned to a different model family:

| Reviewer | Agent | Model family |
|----------|-------|--------------|
| Reviewer A | `reviewer` | OpenAI (`@critic`, gpt-6-astra) |
| Reviewer B | `security-reviewer` | GLM (`@sentinel`, glm-5.3) |
| Reviewer C | `interrogator` | Anthropic (`@plan`, claude-opus-5-5) |
| Reviewer D | `task` | GLM (`@task`, glm-5.3-flash) — same family as B |

DeepSeek, which D used to carry, is off every pin and chain since 2026-09-23 (costs more than glm-5.3). Until `@task` or another agent is pinned to a fourth family, D duplicates B's family — see the rule below.

Reviewer C is pinned by `model: "@plan"` in `agent/agents/interrogator.md`, which is the shape to copy if you want a differently-pinned arm. The other three are built-ins: their pins live in `task.agentModelOverrides` and `modelRoles` in `config.yml`, and `omp agents unpack` materializes them as files if you need to read them.

The adversarial signal is family diversity: four independently trained models miss different things, and a finding two unrelated families reach independently is the highest-signal finding in the review. The four agents are only vehicles for four families; their own instructions differ (B carries the security lens, C the panel-arm lens), but all four get the same filled prompt and rubric, so the persona is not what makes them disagree. If a role pin later moves so two arms share a family, the panel loses an arm's worth of signal: check the pins before trusting this table, and swap in a different-family agent rather than shipping a two-model review.

Before spawning, read `references/reviewer-prompt.md` and fill in the template with:

1. The stated intent
2. The diff or file contents (referenced as the `local://` package path — do not inline it)
3. The review rubric from `references/rubric.md`
4. The code-quality lens from `references/code-quality-review.md`

Each item is `{name, agent, task}`:

- `name`: `Reviewer A` … `Reviewer D` (stable handles for addressing them and collecting results)
- `agent`: the agent from the table above
- `task`: the filled reviewer prompt, pointing at the `local://` package path

The same filled template goes to all reviewers, so every model applies the code-quality lens.

Two of the four arms enforce their own output schemas and will return a JSON envelope instead of the `## Findings` prose the template asks for: `reviewer` returns `{overall_correctness, explanation, confidence, findings[]}` and `security-reviewer` returns `{coverage_summary, findings[]}`. `interrogator` and `task` return the prose form. Parse both shapes in Step 4; the envelope's own `overall_correctness` / `severity` values are per-arm verdicts worth citing in the Agreement Map.

`readonly` does not exist as a field, and only `interrogator` is read-only at the tool level. `task` has full edit and write access and `reviewer` has `bash`. The read-only sentence at the top of the reviewer template is what keeps them from touching the code — do not drop it when filling the template, and check `git status` after a panel run if you handed it a live checkout.

## Step 4, Synthesize

As results come back, build a unified picture:

1. **Parse all findings** from the reviewers
2. **Identify consensus**. Findings raised by 2+ models independently are highest signal.
3. **Identify lone-model findings**. Still worth reading, but weight accordingly.
4. **Deduplicate**. Different models may describe the same issue differently. Merge these and note which models raised it.
5. **Note disagreements**. If one model flags something and another explicitly says the opposite, that's useful context for the verdict.

## Step 5, Lead Judgment

You are the lead reviewer, a pragmatic senior engineer, not a neutral aggregator.

Read `references/lead-judgment.md` for the full framework.

Categorize every finding using these buckets:

- **Act on**. Real issues affecting correctness, security, or maintainability given the actual goals. These would block a real PR.
- **Consider**. Legitimate points, but you're not sure they outweigh the cost of addressing them right now. Worth the user's attention.
- **Noted**. Technically valid but not actionable. Context-dependent, premature optimization, or low-impact given the current stage.
- **Dismissed**. Wrong, nitpicky, or missing context. Brief explanation why.

For each finding, include:
- Which model(s) raised it
- The category (act on / consider / noted / dismissed)
- A one-line rationale for the categorization

## Output Format

Present the verdict in this structure:

### Intent
> [The stated intent paragraph from Step 2]

### Reviewers
- Reviewer [label]: [agent + model], [N findings] (one bullet per reviewer)

### Act On
[Findings that should be addressed. For each: description, which models raised it, why it matters.]

### Consider
[Findings worth thinking about. For each: description, which models raised it, tradeoff involved.]

### Noted
[Valid but low-priority. Brief list.]

### Dismissed
[Rejected findings with brief rationale.]

### Agreement Map
[Where did models agree, where did they diverge, and what does the pattern of agreement/disagreement tell us?]
