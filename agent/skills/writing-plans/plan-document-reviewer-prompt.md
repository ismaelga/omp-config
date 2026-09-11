# Plan Document Reviewer Prompt Template

Use this template when dispatching a plan document reviewer subagent.

**Purpose:** Verify the plan is complete, matches the spec, and has proper task decomposition.

**Dispatch after:** The complete plan is written.

`task` item (agent: `reviewer`):
  description: "Review plan document"
  outputSchema: {"status": "Approved|Issues Found",
                 "issues": [{"task": "Task N, Step M (or 'plan-level')",
                             "issue": "specific issue",
                             "why": "why it matters for implementation"}],
                 "recommendations": ["advisory, non-blocking"]}
  prompt: |
    You are a plan document reviewer. Verify this plan is complete and ready for implementation.

    **Plan to review:** [PLAN_URI] — a `local://` URI from your dispatch
    **Spec for reference:** [SPEC_URI] — also a `local://` URI, or "none"

    ## What to Check

    | Category | What to Look For |
    |----------|------------------|
    | Completeness | TODOs, placeholders, incomplete tasks, missing steps |
    | Spec Alignment | Plan covers spec requirements, no major scope creep |
    | Task Decomposition | Tasks have clear boundaries, steps are actionable |
    | Buildability | Could an engineer follow this plan without getting stuck? |

    ## Calibration

    **Only flag issues that would cause real problems during implementation.**
    An implementer building the wrong thing or getting stuck is an issue.
    Minor wording, stylistic preferences, and "nice to have" suggestions are not.

    Approve unless there are serious gaps — missing requirements from the spec,
    contradictory steps, placeholder content, or tasks so vague they can't be acted on.

    ## Output Format

    Your final message must be only the JSON object matching the dispatch's
    `outputSchema`: `status` (Approved | Issues Found), `issues` (each with
    the task/step it applies to, the specific issue, and why it matters for
    implementation), and `recommendations` (advisory, do not block
    approval).

**Reviewer returns:** the validated `outputSchema` object — `status`,
`issues[]`, `recommendations[]` — auto-delivered; the full result also
stays reachable at `agent://<id>`.

