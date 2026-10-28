---
name: writing-idiomatic-rust
description: "Use when writing, reviewing, or refactoring Rust code — API design, naming, doc comments, error types, tests, ownership — before finishing or shipping any Rust change. Reference of judgment-call rules from Google, Microsoft Pragmatic, Rust API Guidelines, Effective Rust, ANSSI, Tiger Style, and Canonical that clippy cannot check."
---

# Writing Idiomatic Rust

Clippy + rustfmt catch the mechanical layer; when a repo pins its own lint config, that config wins (e.g. many repos deny `unwrap`/`expect`/`panic` outright — do not "fix" that to `expect` because Google prefers it). What remains are judgment calls. All rules below are consensus from multiple established guides; sources at `skill://writing-idiomatic-rust/sources.md` if you need the citation.

Before finishing a Rust change: scan the sections you touched. Missing `# Errors` docs and `assert!` without context are the two most frequent real failures.

## API shape

- `enum` over `bool` when a call site can't say what `true` means: `resize(w, Exact, Round)` not `resize(w, true, false)`. Two+ bools = smell.
- Implement the std trait instead of the same-shaped inherent method: `impl FromStr`, not `fn from_str`. Pair important `From` impls with a named constructor (`new`/`new_with_foo`/`try_new` when fallible/`from_foo`).
- Implement expected sets together: `len` + `is_empty`; `new` + `Default`; `PartialEq` + `Eq` (and `Hash` if it can be a map key); `iter` + `IntoIterator`.
- Borrow flexibly: `&str` not `&String`, `&[T]` not `&Vec<T>`, `Option<&T>` not `&Option<T>`. Library code: return iterators, accept `impl IntoIterator`; application code: `Vec` and slices are fine — simplicity over premature generalization.
- Getters/setters follow std naming: `foo()`/`foo_mut()`, `set_foo()`, `take_foo()` (clears + returns old), `with_foo(|f| …)` when behind interior mutability. Never `get_foo()`.
- Conversion prefixes encode cost: `as_` borrowed→borrowed (free), `to_` may allocate, `into_` consumes.
- Only smart pointers get `Deref`; never Deref-as-inheritance on a newtype. No out-params (`&mut Bar` output); return values. Expose intermediate results (`binary_search`'s `Result<usize, usize>`, not just `bool`).
- Define a trait only for generic bounds, `dyn`, or extension traits (`ForeignTypeExt` suffix); otherwise inherent impls. Newtype for anything unit- or domain-distinct (`Miles` vs raw `f64`); validate in the constructor, keep fields private.

## Naming

- No abbreviations a newcomer can't decode; no weasel words (`Manager`, `Service`, `Factory`) — say what the type *is*.
- Names ≤2 words; no module-name prefix on items (`foo::FooId` is noise).
- Acronyms are words: `Uuid`, not `UUID`.

## Doc comments

- Every public item documented; `# Errors` on anything returning `Result`; `# Panics` if it can panic; `# Safety` on `unsafe`.
- First sentence says *when* to use the item, not what its name already says. Never restate the identifier (`/// Removes an element.` on `remove_element`).
- Doctests use `?` with `# fn main() -> Result<…>`, never `unwrap`.
- Prose backticks code identifiers; skip parameter tables; mix `//` implementation comments with `///` freely — doc comments carry contract, `//` carries why.

## Errors

- `Option` = simple obvious absence; `Result` = caller needs the why; panic = violated invariant (bug), only where repo policy permits.
- Error types: `Display` + `std::error::Error` + `Send + Sync` + `Copy`/small variants. Never `Result<_, ()>`, never stringly-typed `Err(format!(…))` in a domain layer.
- Preserve causes (`source`) or flatten deliberately — never `format!` a nested error away. Convert foreign errors once via `From` at the boundary, not `map_err` at every call site.
- Messages lowercase, verb-first: `cannot sign the transaction: nonce is unknown`.

## Implementation

- Annotate the type where inference hides it: `let x: u32 = s.parse()?`, results of long combinator chains. Not every intermediate.
- Pattern-match instead of check-then-unwrap (`if let Some(v)`, never `if o.is_some() { o.unwrap() }`).
- `assert!` with a context string: the invariant's reason or the offending value — `assert!(refund > 0, "refund must be positive, got {refund:?}")`. The message must not restate the condition.
- `for` loops over `Iterator::for_each`; no combinator chain in a `for` header (bind it to a named variable first); switch to a loop when a chain grows conditionals, mutation, or early returns.
- `format!`/`write!` to concatenate or substitute (never `a + b + c` or `push_str(&format!…)`).
- No `Option<Option<T>>` unless the tri-state is documented at the type; no type-changing shadowing; no `let x = &f()` temporaries.
- No `mem::forget`, `Box::leak`, or `catch_unwind` at call sites (guides: ANSSI MEM-LEAK, Google); no code before `main` (`ctor` tricks).
- No `Default` derive on safety-critical config — missing limits must not silently become zero-or-permissive.

## Tests

- `assert!(r.is_ok())` proves nothing — `.unwrap()` the value and assert on it (unwrap in tests is fine everywhere).
- No tautological tests: a test whose expected value is the implementation's own output pins nothing.
- Test the negative space (invalid inputs, empty, boundary), not just the golden path.

## Ownership

- Borrow first; `.clone()` is a decision, not a reflex — and never the borrow-checker appeasement (restructure borrows, or `mem::take`/`mem::replace`).
- `Rc`/`Arc` only when the ownership graph genuinely demands it; prefer unique ownership + borrowing. Refcount bumps (`Arc::clone(&h)`) are the cheap kind.
- Guard-dropped state in `Drop` must not fail or block; give fallible teardown an explicit `close() -> Result` sibling.

For the type-model thinking behind these (illegal states, exhaustive matching, boundaries), apply **skill://principle-type-system-discipline**.
