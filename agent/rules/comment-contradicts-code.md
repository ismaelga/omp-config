---
description: Comments must be true of the code they annotate
question: "Does a comment added in this edit claim something untrue of the code it annotates?"
condition:
  - "//"
  - "/\\*"
  - "(?m)^\\s*#\\s"
scope: "tool:edit(**/*.{ts,tsx,js,jsx,mjs,cjs,py,rs,go,ex,exs,sol,sh,swift,kt}), tool:write(**/*.{ts,tsx,js,jsx,mjs,cjs,py,rs,go,ex,exs,sol,sh,swift,kt})"
---
A comment added in this edit disagrees with the code it describes (a count, a unit, a condition, a return value). Fix whichever side is wrong; a stale comment is a bug report nobody filed.
