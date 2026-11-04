---
name: design-critique
description: Use when asked to critique, score, rate, or give expert design feedback on a built web page or UI — hierarchy, typography, detail, taste — rather than to build or fix it. Accessibility compliance audits are web-interface-guidelines.
license: Apache-2.0, see LICENSE
---

# Design Critique

Adapted from `design-templates/critique` in [nexu-io/open-design](https://github.com/nexu-io/open-design) (Apache-2.0, `LICENSE` here), itself after the huashu-design expert critique. Changed for omp: evidence comes from screenshots instead of reading CSS, the report goes in chat with an inline SVG radar instead of an HTML artifact, and the slide-deck prompts are gone.

A critique scores five dimensions, each from what the rendered page shows. Source code is for citing the rule behind something already seen.

## Look before scoring

1. Local file: serve its directory (`python3 -m http.server`) and open the URL; `file://` needs a dedicated browser with `allow_file_access`.
2. `browser.open` at 1280×800 and take a full-page `screenshot`; then `emulate` 390×844 and screenshot again, and record `scrollWidth` against `clientWidth`.
3. `emulate({ colorScheme: "light" })`, screenshot; `emulate({ colorScheme: "dark" })`, screenshot. The managed browser follows the OS scheme, so leaving it unset reviews only whichever half the OS happens to pick; identical screenshots are a valid result.
4. Click every control that claims a state (toggles, tabs, `aria-pressed`, disclosure) and screenshot the after-state.

Done when every score below cites something visible in a screenshot or a measured value.

Critiquing a page you built in this session: dispatch the critique to a fresh `task` subagent with the URL and `skill://design-critique`, and relay its report.

## The five dimensions

| Dimension | The question | Evidence to look for |
|---|---|---|
| Philosophy | Does one direction run through every element? | Styles that fight; decoration serving nothing; emoji standing in for icons; a palette that is the framework default |
| Hierarchy | Can a stranger tell what to read first, second, third? | Display-to-body type ratio; equal cards competing for the eye; where the primary action sits |
| Detail | Is the 90/10 work done? | Column tops and baselines aligned; spacing rhythm; one radius/shadow language; clean wrapping at 390 |
| Functionality | Does it work for its job? | Fits 390 and 1280 without sideways scroll; text readable in both schemes; controls change what they claim; destructive actions look destructive |
| Innovation | Is there one move worth stealing, earned by the brief? | Interchangeable template vs. a memorable choice; 5 is a fine score for production UI |

Bands: **0–4** Broken · **5–6** Functional · **7–8** Strong · **9–10** Exceptional. A dimension scores its worst sustained band, never the average of good and bad areas. A mean above 8 means look again.

## Report

Reply in chat with these parts, in order, and modify nothing unless asked:

1. **Verdict**: one line.
2. **Radar**: a ` ```svg ` block. `viewBox="0 0 320 300"`, centre (160,150), axis *i* (Philosophy first, clockwise) at angle −90° + 72°·*i*. Draw the outer pentagon at radius 110 with `stroke="var(--border)"`, the score polygon at radius 11·score with `fill="var(--accent)" fill-opacity="0.25" stroke="var(--accent)"`, and labels with `fill="currentColor"` at radius 130.
3. **Scores**: table of Dimension | Score | Evidence. Evidence is 30–80 words naming the element, the viewport or state, and the selector or line.
4. **Keep**: 3–5 things working that the next iteration must not break.
5. **Fix**: 3–6 items ordered by visual cost saved per minute, one sentence each.
6. **Quick wins**: 3–5 tweaks of 5–15 minutes each.
