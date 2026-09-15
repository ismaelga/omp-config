---
name: better-ui
description: "Static visual polish with exact values: concentric border radius, optical alignment, shadow-versus-border depth, image outlines, icon stroke weight and state pairs, icon cross-fades, theme-switch transition suppression, will-change discipline. Use when an interface works but looks subtly off."
disable-model-invocation: true
---

# UI polish

Polish comes from a pile of small details that compound. This skill is the reference for
which are worth having and what values they take.

Every duration, curve, scale and blur below is a specific value, not a range to
approximate. `cubic-bezier(0.2, 0, 0, 1)` is not `cubic-bezier(0.4, 0, 0.2, 1)`, and
`0.96` is not `0.95`. Use what is written.

Keep the project's component library, tokens and density, and match its motion language
except where a rule below prescribes an exact interaction.

**Scope.** This is the static surface: radius, alignment, depth, icons, and the two
cross-cutting details in [theme-and-layers.md](theme-and-layers.md). Motion design proper
belongs elsewhere and is deliberately not restated here, because the constants differ and
two answers is worse than one:

- Building an animation, picking a curve, duration, spring, stagger, exit or interruption
  -> `animate` (and its `RECIPES.md` for the standard components).
- Judging motion that already exists -> `review-animations`.
- Slow-motion inspection of a live animation, frame stepping, touch-device checks ->
  `emil-design-eng`, which carries the `eval` browser recipes for all three.
- Accessibility, focus order, hit areas, reduced motion, forms, i18n ->
  `web-interface-guidelines`.
- Typography scale, wrapping, tabular numbers -> `frontend-design`.

## Concentric border radius

Outer radius = inner radius + padding. Mismatched radii on nested elements is the most
common thing that makes an interface feel off. Past `24px` of padding, treat the layers as
separate surfaces and pick each radius independently. Recipes in
[surfaces.md](surfaces.md).

## Optical over geometric alignment

When geometric centering looks off, align optically. Buttons with icons, play triangles
and asymmetric icons all need a manual nudge: icon-side padding `2px` tighter than the
text side, play glyphs shifted `2px` right, asymmetric glyphs fixed in the SVG rather than
with margin. See [surfaces.md](surfaces.md).

## Shadows for elevation, borders for structure

Where a border exists only to create depth, prefer layered transparent `box-shadow`
values, which adapt to any background where a solid border color cannot. Keep borders that
communicate structure or state: dividers, separators, table cell boundaries, input
outlines, selected and focus states. Three-layer light-mode recipe and the single white
ring for dark mode are in [surfaces.md](surfaces.md).

## Image outlines

Give images a `1px` outline at low opacity for consistent depth. Pure black in light mode
(`oklch(0 0 0 / 0.1)`), pure white in dark (`oklch(1 0 0 / 0.1)`), always with
`outline-offset: -1px`. Never a near-black like slate or zinc and never a tinted neutral: a
tinted outline picks up the surface underneath and reads as dirt on the image edge.
`outline` rather than `border` because it never affects layout.

## Match icon stroke to text weight

An icon next to text carries the text's optical weight: `1.5px` stroke beside regular
(400) text, `2px` beside medium or semibold (500-600), `2.5px` beside bold. One stroke
convention and one icon library per surface. Size icons to the text's cap height,
`1em`-`1.25em` inline. Sizing grids and RTL flipping are in [icons.md](icons.md).

## One SVG, recolored per state

Icons use `currentColor` and take hover, selected and disabled states from CSS color and
opacity, never from separate assets. Strip hardcoded fills like `fill="#666"` on import.
Outline is the default variant; fill marks the active state, as a pair and never
interchangeably.

## Contextual icon animations

Animate icon swaps with `opacity`, `scale` and `blur` rather than toggling visibility.
Exact values: scale `0.25` to `1`, opacity `0` to `1`, blur `4px` to `0px`, and with a
motion library `transition: { type: "spring", duration: 0.3, bounce: 0 }` where bounce is
always `0`. Without one, keep both icons in the DOM with one absolutely positioned and
cross-fade with `cubic-bezier(0.2, 0, 0, 1)`. Both recipes, and the scope note on why
`0.25` is right here and wrong for page elements, are in
[icon-transitions.md](icon-transitions.md).

## Suppress transitions on theme switch

A theme flip changes color, background, border and shadow on nearly every element at once.
Every transition on those properties fires together and the switch smears instead of
snapping. Inject `*,*::before,*::after{transition:none !important}`, force a reflow, then
remove it on the next frame. Recipe in [theme-and-layers.md](theme-and-layers.md).

## Use `will-change` sparingly

Only for `transform`, `opacity` and `filter`, which the GPU can composite. Never
`will-change: all`, never on properties that cannot be composited anyway. Add it when you
see first-frame stutter, not before: each extra compositing layer costs memory. Table of
what is worth promoting is in [theme-and-layers.md](theme-and-layers.md).

## Before you finish

| Mistake | Fix |
| --- | --- |
| Nested corners look wrong | Outer radius = inner + padding, or split the surfaces |
| Icons look off-center | Nudge optically with padding, or fix the SVG |
| Border disappears over an image or gradient | Layered transparent shadow instead |
| Image edge reads as dirty | Pure black or white at `/0.1`, never a tinted neutral |
| Hairline icon beside bold text | Match the stroke width to the text weight |
| Separate assets per icon state | One SVG on `currentColor`, states in CSS |
| Theme toggle crossfades the whole page | Disable transitions for the swap, force a reflow, restore next frame |
| First-frame animation stutter | `will-change: transform`, sparingly |

Reporting a review is `code-review`'s job, not this skill's. Cite `path:line`, name the
rule from this file that the code violates, and give the exact value it should use.
