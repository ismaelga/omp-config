---
name: prototyping
description: "Use when a design question cannot be settled on paper — does this state model feel right, does this interaction work, which of these two shapes is less awkward. Builds throwaway code that answers ONE named question, gets a verdict, then dies. Not for building the real thing."
---

# Prototyping

A prototype is **throwaway code that answers one question**. Write the question down before you
write any code; if you cannot name it in one sentence, you are not prototyping, you are building.

The question decides the shape. Getting the shape wrong wastes the whole prototype.

## Pick the branch

| The question is… | Build | Verdict comes from |
|---|---|---|
| "Does this state model / logic feel right?" | A tiny runnable script that drives the state machine through the cases that are hard to reason about on paper. Print the full state after every action. | Reading the state transitions |
| "What should this look like / how should it feel?" | Several deliberately different variants on one route or one screen, switchable without a rebuild (query param, env var, keypress) | The human looking at it |
| "Is A or B less awkward to use?" | Both call sites, written out as the caller would write them. No implementation behind them. | Comparing the two call sites |

If the question is ambiguous and the user is reachable, ask. If not, pick by what surrounds the
code — a module → logic; a screen → UI — and state the assumption at the top of the prototype.

## Rules

1. **Throwaway from line one, and named so.** `prototype-<question>.<ext>`, sitting next to the
   code it informs. A reader must not mistake it for production.
2. **One command to run**, using whatever runner the project already has. No new toolchain.
3. **No persistence.** State lives in memory. If the question genuinely involves storage, use a
   scratch file named `PROTOTYPE-wipe-me`.
4. **No tests, no error handling beyond runnable, no abstractions.** The prototype has no future
   to design for.
5. **Surface the state.** Every action prints or renders what changed. A prototype you cannot
   observe answers nothing.
6. **Timebox it.** Say the box out loud before starting (30-60 minutes of work is typical). Blown
   box means the question was too big — split it or take it back to `brainstorming`.

## Capture, then kill

1. Write the verdict where the decision lives: the map's resolution block (`wayfinding`), the
   spec, or the plan. Verdict = the question, the answer, and what you saw that settled it.
2. Fold the validated decision into the real code — by hand, deliberately. You NEVER promote
   prototype code to production; it was written without tests, error handling, or boundaries.
3. Delete the prototype, or park it on a scratch branch and link it from wherever the verdict
   went. `main` keeps the decision, never the prototype.

## Stop signals

<HARD-GATE>
- **The sharp test: would this code survive the answer?** A prototype is dead the moment the
  question is settled. If what you are writing is meant to still be there afterwards, you are
  building the product under a prototype's licence — no tests, no boundaries, no review. Stop.
- The prototype is growing tests, abstractions, or error handling → it is becoming the product.
  Stop. Take the verdict you have.
- You are about to keep the prototype "because it mostly works" → that is how untested code
  reaches production. Rewrite it properly or delete it.
- The prototype answered its question two hours ago and you are still extending it → the answer
  is in; write the verdict.
</HARD-GATE>

## Not this skill

- **Understanding a dependency's behaviour** → read its source (`librarian`), or reimplement its core
  in 50-200 lines to find where it diverges from your mental model.
- **Measuring whether something is fast enough / cheap enough** → `cavecrew-benchwright`.
- **The question is "what should we build"** → `brainstorming`. Prototype only once a specific
  design question resists discussion.
