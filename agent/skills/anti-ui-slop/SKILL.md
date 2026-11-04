---
name: anti-ui-slop
description: "Use when building, redesigning, polishing, or simplifying a web or iOS interface whose visual direction is already set, or running a quick pre-ship defect audit of one. Visual direction is frontend-design; a scored design critique is design-critique."
license: MIT
metadata:
  version: "1.2.13"
  author: "UIZZE <business@uizze.com>"
  tags: "ui-design, design-system, design-review, frontend, web-ui, ios-ui"
---

# Stop Making UI Slop

Adapted from UIZZE's free anti-ui-slop skill, v1.2.13 (MIT). The branch that called UIZZE's paid reference service is removed; the playbooks are the skill.

## Overview

Use the product brief, existing UI, components, and local design system to make intentional interfaces.

## Prerequisites

- A screen or component to build, redesign, or review — a file path or a short description.
- The product's existing components, design tokens, and visual language, so the build extends them instead of inventing a new system.

## Work from the product

Read the brief, existing UI, components, tokens, and constraints before designing. They always outrank this skill. Keep familiar interaction conventions and make the product's own objects, workflow, and priorities visually clear. Do not add novelty for its own sake.

## Load one playbook

Choose at most one file for the current request:

- New interface or major redesign: `reference/new-work.md`
- Product or dashboard work: `reference/operate.md`
- Refinement and polish: `reference/polish.md`
- Simplification or distillation: `reference/distill.md`
- Explicit audit: `reference/audit.md`
- Native iOS work: `reference/ios.md`

Do not load a second playbook. Apply judgment rather than treating its examples as a checklist.

## Finish

Complete the requested scope. Render and inspect: open the page with `eval`'s `browser` global (`browser.open`), then `screenshot` and `observe` it at 1280 and 390 px wide, each with `emulate({ colorScheme: "light" })` and `"dark"`. The managed browser follows the OS scheme, so an unset scheme inspects only half the page. A screenshot does not show contrast ratios: in each scheme run `await tab.evaluate(await read("skill://anti-ui-slop/contrast.js:raw"))`, fix until its `failing` list is empty, and check each `unmeasured` element (text on an image or gradient) by eye in the screenshots. Fix observable breakage such as clipping, overlap, distorted media, inaccessible controls, or inert interactions, and re-shoot what you fixed. Keep the handoff concise.
