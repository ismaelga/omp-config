# Phase-Boundary Reviewer Prompt Template

Use this template at a phase boundary (roughly every 3-4 tasks), for the one task that lands
genuinely risky code, or for the final whole-branch pass. The reviewer reads the accumulated diff
once and returns two verdicts: spec compliance and code quality.

Do NOT dispatch this once per task. Per-task spec checking is the controller's own job — see
SKILL.md "Per-Task Spec Check" for the measurement that settled it.

**Purpose:** Verify the work in range matches its requirements (nothing more, nothing less) and is
well-built (clean, tested, maintainable)

`task` item (agent: `reviewer` — there is no per-spawn model parameter; model
  resolves from the agent type and `task.agentModelOverrides` in config.yml):
  description: "Review tasks N-M (spec + quality)"
  outputSchema: {"status": "Approved|Needs fixes",
                 "specCompliance": "compliant|issues",
                 "cannotVerify": "requirements not checkable from this diff, or empty",
                 "strengths": "specific, brief",
                 "critical": [{"file": "path:line", "issue": "what's wrong", "fix": "how to fix"}],
                 "important": [{"file": "path:line", "issue": "what's wrong", "fix": "how to fix"}],
                 "minor": [{"file": "path:line", "issue": "what's wrong", "fix": "how to fix"}],
                 "reasoning": "1-2 sentence technical assessment"}
  prompt: |
    You are reviewing the accumulated implementation of one or more tasks: first
    whether it matches its requirements, then whether it is well-built. This is a
    phase-scoped gate, not a merge review — a broad whole-branch review happens
    separately after all tasks are complete.

    ## What Was Requested

    Read your task brief: [BRIEF_FILE] — a `local://` URI passed in your
    dispatch.

    Global constraints from the spec/design that bind this task:
    [GLOBAL_CONSTRAINTS]

    ## What the Implementer Claims They Built

    Read the implementer's report: [REPORT_FILE] — also a `local://` URI.

    ## Diff Under Review

    **Base:** [BASE_SHA]
    **Head:** [HEAD_SHA]
    **Review package:** [REVIEW_PACKAGE]

    Read the review package once — it contains the commit list, a stat
    summary, and the full diff with surrounding context, and it is your view
    of the change. The diff's context lines ARE the changed files: do not
    Read a changed file separately unless a hunk you must judge is cut off
    mid-function — and say so in your report. Do not re-run git commands.
    If the review package is missing, fetch the diff yourself:
    `git diff --stat [BASE_SHA]..[HEAD_SHA]` and `git diff [BASE_SHA]..[HEAD_SHA]`.
    Do not crawl the broader codebase. Inspect code outside the diff only
    to evaluate a concrete risk you can name — one focused check per named
    risk, and name both the risk and what you checked in your report.
    Cross-cutting changes are legitimate named risks: if the diff changes
    lock ordering, a function or API contract, or shared mutable state,
    checking the call sites is the right method.

    Your review is read-only on this checkout. Do not mutate the working
    tree, the index, HEAD, or branch state in any way.

    ## Do Not Trust the Report

    Treat the implementer's report as unverified claims about the code. It
    may be incomplete, inaccurate, or optimistic. Verify the claims against
    the diff. Design rationales in the report are claims too: "left it per
    YAGNI," "kept it simple deliberately," or any other justification is the
    implementer grading their own work. Judge the code on its merits — a
    stated rationale never downgrades a finding's severity.

    ## Tests

    The implementer already ran the tests and reported results with TDD
    evidence for exactly this code. Do not re-run the suite to confirm their
    report. Run a test only when reading the code raises a specific doubt
    that no existing run answers — and then a focused test, never a
    package-wide suite, race detector run, or repeated/high-count loop. If
    heavy validation seems warranted, recommend it in your report instead of
    running it. If you cannot run commands in this environment, name the
    test you would run.

    Warnings or other noise in the implementer's reported test output are
    findings — test output should be pristine.

    ## Part 1: Spec Compliance

    Compare the diff against What Was Requested:

    - **Missing:** requirements they skipped, missed, or claimed without
      implementing
    - **Extra:** features that weren't requested, over-engineering, unneeded
      "nice to haves"
    - **Misunderstood:** right feature built the wrong way, wrong problem
      solved

    If a requirement cannot be verified from this diff alone (it lives in
    unchanged code or spans tasks), put it in `cannotVerify` instead of
    broadening your search — say what the controller should check.

    ## Part 2: Code Quality

    **Code quality:**
    - Clean separation of concerns?
    - Proper error handling?
    - DRY without premature abstraction?
    - Edge cases handled?

    **Tests:**
    - Do the new and changed tests verify real behavior, not mocks?
    - Are the task's edge cases covered?

    **Structure:**
    - Does each file have one clear responsibility with a well-defined interface?
    - Are units decomposed so they can be understood and tested independently?
    - Is the implementation following the file structure from the plan?
    - Did this change create new files that are already large, or
      significantly grow existing files? (Don't flag pre-existing file
      sizes — focus on what this change contributed.)

    Your report should point at evidence: file:line references for every
    finding and for any check you would otherwise answer with a bare
    "yes." A tight report that cites lines gives the controller everything
    it needs.

    Your final message must be only the JSON object matching the dispatch's
    `outputSchema` — status, specCompliance, cannotVerify, strengths,
    critical/important/minor findings, reasoning. Keep each finding short;
    the controller reads the diff itself.

    ### Calibration

    Not everything is Critical. Important means this task cannot be trusted
    until it is fixed: incorrect or fragile behavior, a missed requirement, or
    maintainability damage you would block a merge over — verbatim duplication
    of a logic block, swallowed errors, tests that assert nothing. "Coverage
    could be broader" and polish suggestions are Minor.
    If the plan or brief explicitly mandates something this rubric calls a
    defect (a test that asserts nothing, verbatim duplication of a logic
    block), that IS a finding — report it as Important, labeled
    plan-mandated in the issue text. The plan's authorship does not grade
    its own work; the human decides.
    Acknowledge what was done well in `strengths` — accurate praise helps the
    implementer trust the rest of the feedback.
```

**Placeholders:**
- `[GLOBAL_CONSTRAINTS]` — the binding requirements copied verbatim from
  the plan's Global Constraints section or the spec: exact values, formats,
  and stated relationships between components (not process rules — those
  are already in this template)
- `[REPORT_FILE]` — REQUIRED: the `local://` URI of the file the implementer
  wrote its detailed report to
- `[BASE_SHA]` — commit before this task
- `[HEAD_SHA]` — current commit
- `[REVIEW_PACKAGE]` — REQUIRED: the `local://` URI the controller wrote the
  review package to; the package never enters the controller's context

**Reviewer returns:** the `outputSchema` object — `status`
(Approved | Needs fixes), `specCompliance`, `strengths`, and
Critical/Important/Minor findings — delivered validated; the full result is
also reachable at `agent://<id>?q=.status` and friends.

A fix dispatch can address spec gaps and quality findings together;
re-review after fixes covers both verdicts.
