# Theme flips and compositing layers

Two details that are invisible until they are wrong: a theme swap that smears because
every transitioned property animates at once, and a first-frame stutter because the
compositor promotes the layer late. General motion rules live in the `animate` skill;
these two are surface-level correctness, not motion design.

## Suppress transitions on theme switch

Flipping the theme changes `color`, `background-color`, `border-color` and `box-shadow` on nearly every element at once. Everything carrying a transition on those properties animates together, so the switch reads as a slow smear rather than an instant change. Disable transitions for the swap and restore them right after.

Inject a stylesheet that turns off every transition, force a reflow so the new colors commit while it still applies, then drop it on the next frame:

```tsx
"use client";

import { useEffect } from "react";

export function DisableThemeTransitions() {
  useEffect(() => {
    const mql = window.matchMedia("(prefers-color-scheme: dark)");

    const handleChange = () => {
      const style = document.createElement("style");
      style.append(
        document.createTextNode(
          "*,*::before,*::after{transition:none !important}"
        )
      );
      document.head.append(style);

      const _flushReflow = document.body.offsetHeight;

      requestAnimationFrame(() => {
        requestAnimationFrame(() => style.remove());
      });
    };

    mql.addEventListener("change", handleChange);
    return () => mql.removeEventListener("change", handleChange);
  }, []);

  return null;
}
```

`document.body.offsetHeight` is read for its side effect, forcing a synchronous style flush so the new theme resolves while the override is still in the document and no transition starts. The nested `requestAnimationFrame` removes the override only after that paint, restoring transitions before the next interaction.

That covers the OS-level change. An in-app toggle needs the same treatment around its own flip: apply the override, change the theme, flush, remove. `next-themes` ships this as `disableTransitionOnChange`.

## Use `will-change` sparingly

`will-change` hints the browser to pre-promote an element to its own GPU compositing layer. Without it the browser promotes only when the animation starts, and that one-time promotion can cause a micro-stutter on the first frame.

It helps most for `scale`, `rotation` and movement through `transform`. For other properties it does little, because the browser cannot composite them on the GPU anyway.

### Rules

```css
/* Good: specific property that benefits from GPU compositing */
.animated-card {
  will-change: transform;
}

/* Good: multiple compositor-friendly properties */
.animated-card {
  will-change: transform, opacity;
}

/* Bad: never use will-change: all */
.animated-card {
  will-change: all;
}

/* Bad: properties that can't be GPU-composited anyway */
.animated-card {
  will-change: background-color, padding;
}
```

### Useful properties

| Property | GPU-compositable | Worth using `will-change` |
| --- | --- | --- |
| `transform` | Yes | Yes |
| `opacity` | Yes | Yes |
| `filter` (blur, brightness) | Yes | Yes |
| `clip-path` | Newer Chromium only | Rarely; not reliable cross-browser |
| `top`, `left`, `width`, `height` | No | No |
| `background`, `border`, `color` | No | No |

### When to skip

Modern browsers optimize well on their own. Add `will-change` only when you see first-frame stutter, which Safari benefits from most. Never add it preemptively to every animated element, since each extra compositing layer costs memory.
