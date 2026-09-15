---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Implement the work described by the user in the spec or tickets.

Build under /skill:test-driven-development at the seams the spec agreed. If a ticket genuinely cannot be test-driven -- no harness exists, no seam is reachable -- say so and get the human's explicit sign-off before writing production code without a failing test; "where possible" is not a sign-off.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, use /skill:code-review to review the work.

Commit your work to the current branch.
