---
description: Comments carry what the code cannot
question: "Does this edit add a comment that restates the adjacent code with no reason, constraint, or gotcha?"
condition:
  - "//"
  - "/\\*"
  - "(?m)^\\s*#\\s"
scope: "tool:edit(**/*.{ts,tsx,js,jsx,mjs,cjs,py,rs,go,ex,exs,sol,sh,swift,kt}), tool:write(**/*.{ts,tsx,js,jsx,mjs,cjs,py,rs,go,ex,exs,sol,sh,swift,kt})"
---
A comment added in this edit only repeats what the code below it says. Delete it, or replace it with what the code cannot carry: why, a constraint, an invariant, units, provenance, or a rejected alternative.
