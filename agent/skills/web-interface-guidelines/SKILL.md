---
name: web-interface-guidelines
description: Audit UI code against the Web Interface Guidelines — accessibility, focus, forms, animation hygiene, typography detail, hydration, i18n, dark mode. Returns terse file:line findings. Correctness pass, not a taste pass.
license: MIT, see LICENSE
---

# Web Interface Guidelines

Read `GUIDELINES.md` in this directory, then review the files named by the user
against every rule in it.

This is the compliance half of UI quality. It will not choose a typeface, a
palette or a layout — `frontend-design` does that, `emil-design-eng` does motion.
What this catches is the detail that separates shipped software from a demo:
missing `aria-label`, `outline-none` with no focus replacement, `transition: all`,
straight quotes and `...` where `…` belongs, number columns without
`tabular-nums`, headings without `text-wrap: balance`, layout reads in render.

## Output

Group by file, one finding per line, no preamble:

```
## src/Button.tsx
src/Button.tsx:42 - icon button missing aria-label
src/Button.tsx:18 - input lacks label
src/Button.tsx:55 - animation missing prefers-reduced-motion
src/Button.tsx:67 - transition: all → list properties
```

State issue and location. Explain only when the fix is non-obvious.
