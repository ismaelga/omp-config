---
name: deslop
description: Remove AI-generated code slop from the branch diff, covering type-silencing casts, swallowed errors, dead fallbacks, redundant wrappers, needless nesting, and comments that restate the code, each paired with the query that finds it.
disable-model-invocation: true
---

# Deslop

Remove code slop introduced on this branch. `unslop` does this for prose; this is the code half.

Scope is deletions and local flattenings that leave behavior unchanged. Structural rework is not this pass: a finding that needs a refactor rather than a delete belongs to `code-review` and a `reviewer` dispatch, not to a cleanup that quietly rewrites working code.

## Work the diff, not the repo

```bash
BASE=$(git merge-base main HEAD)
git diff --name-only "$BASE"...HEAD
git diff "$BASE"...HEAD -- <file>
```

Judge what the branch added or changed. Slop on untouched lines is out of scope. Read the whole file when you edit it — a change that fits the hunk and fights the file is still slop.

## The patterns, and the query that finds each

Pass `lang` to `ast_grep` explicitly. A directory works; files of another language in the tree report parse issues, so narrow `path` when that noise appears.

### Type-silencing casts

```
ast_grep  pat: "$X as any"                 lang: ts
ast_grep  pat: "$OBJ as unknown as $T"     lang: ts
grep      \bas\s+any\b|@ts-ignore|@ts-expect-error|#\s*type:\s*ignore|#\s*noqa
grep      \.cast\(|dyn Any|: Any\b              # python, rust
```

A double cast is the tell that the real boundary is missing: you cannot make one type satisfy another, so the code lies twice. Delete the cast and fix the type. If the fix outgrows this pass, report it — re-casting to silence the error is the thing this skill exists to stop.

Also delete `@ts-expect-error` and `# type: ignore` on lines that already type-check, and `@ts-ignore` anywhere (it suppresses the next error even after the original is fixed).

### Swallowed errors

```
ast_grep  pat: "try { $$$BODY } catch ($ERR) { $$$HANDLER }"   lang: ts
```

Read the handler, never the pattern alone. A handler that returns a default, logs and continues, or is empty has converted a failure into a silent wrong answer somewhere downstream. Remove the try/catch when the caller can handle the throw, or make the handling real. A `catch` whose only statement is `return null` is the classic.

### Dead fallbacks

```
ast_grep  pat: "$T || $FALLBACK"
ast_grep  pat: "$T ?? $FALLBACK"
```

Confirm with `lsp hover` (or the type annotation) that the left side can be null or undefined. If it cannot, the fallback is unreachable and the operator asserts a possibility the type denies. Same for `?? []` and `?? {}` guards on values that were never optional: they hide the real question, which is why the caller passed nothing.

### Redundant wrappers

```
ast_grep  pat: "function $NAME($$$ARGS) { return $CALLEE($$$CALLARGS); }"
```

A function whose entire body forwards its arguments buys a name and nothing else. Run `lsp references` before inlining: keep it if it is a deliberate seam with other implementations, or if callers cannot import the target.

### Nesting an early return removes

```
ast_grep  pat: "if ($A) { return $B; } else { return $C; }"
ast_grep  pat: "if ($A) { if ($B) { $$$BODY } $$$REST }"
```

Flatten to guard clauses. Keep the rewrite inside the function the diff already touched.

### Comments

The comment rule in this config is not "delete comments". Delete a comment when it restates the identifiers below it (`// increment the counter` above `counter++`) or narrates the next line, and delete banner comments that only mark sections the code already shows.

Keep every comment carrying what code cannot: why, constraints, invariants, units, provenance, rejected alternatives. The test is the load-bearing one — delete it, and does a competent reader lose something only the comment held? Public API keeps its doc comments (Go exported names, Rust `missing_docs`). If a comment fails the test but records a decision worth keeping, that decision goes in the commit message, not in a rewrite of the comment.

### Duplicated logic

```
grep      <the distinctive expression, an identifier or call shape>
lsp       references  on the helper you suspect already exists
```

Search before writing. Reuse the canonical helper instead of a near-duplicate.

### Tests that assert nothing real

```
grep  toMatchSnapshot|toBeDefined\(\)|toBeTruthy\(\)|toHaveBeenCalled\(\)|not\.toBeNull
```

A snapshot test, or a test whose only assertion is that a mock was called or that a value is defined, passes whatever the code does. Delete the assertion or the test. A test the diff added that would still pass with the implementation stubbed out is not covering anything.

### Dead code and unused exports

```
lsp  references   file, line, symbol     # includeDeclaration is on
lsp  diagnostics  file
```

A symbol whose only reference is its own declaration is dead. Confirm with a `grep` for the name across non-source files (configs, templates, docs) before removing, then remove with `ast_edit` across the call sites or `edit` for one.

## Tools

- `ast_grep` for structural search. `$X` binds one node, `$$$X` zero or more; use `$$$X`, not `$$X`.
- `ast_edit` for mechanical multi-file removal. It stages a proposal: finalize with a reason at `xd://resolve`, discard at `xd://reject`. Preview the diff before resolving.
- `lsp` for `references`, `hover`, and `diagnostics`. Run `lsp status` first — a server has to be installed for the file type, and most machines have only a few. No server covers the file? Fall back to `grep` plus reading the callers; say so rather than guessing.
- `grep` for text patterns an AST cannot express.
- `unslop` for the prose half: commit message and any comment you keep.

## Guardrails

- Behavior unchanged. Fix a clear bug only when you can say what it broke.
- Minimal edits over broad rewrites.
- Run the checks covering the touched files after a removal. A removal that changes behavior is reverted, not patched around.
- Summary is one to three sentences: what went, what stayed, what you left for review.
