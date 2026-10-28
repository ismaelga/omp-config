# Sources — writing-idiomatic-rust

Every rule in SKILL.md is consensus of at least two of these, or an explicit agent-failure rule from a guide. Rule-by-rule tables with per-rule anchors and enforcement mappings were extracted 2026-10-27 (session artifacts `rust-guides-*.md`); steward's adopted/deferred/rejected lint decisions live in `docs/research/rust-rules.md` §7 of the steward repo.

## Guides (ranked by value per token)

1. **Rust API Guidelines** — https://rust-lang.github.io/api-guidelines/checklist.html — naming (C-CASE, C-CONV, C-GETTER, C-ITER), interoperability (C-COMMON-TRAITS, C-GOOD-ERR), predictability (C-CTOR, C-NO-OUT, C-INTERMEDIATE), type safety (C-NEWTYPE, C-CUSTOM-TYPE), future-proofing (C-SEALED, C-STRUCT-BOUNDS), dependability (C-DTOR-FAIL/BLOCK).
2. **Effective Rust** (David Drysdale) — https://effective-rust.com/ — items 1-10 (types, errors, casts, newtype, std traits), 22 (visibility), 27 (documentation), 29 (listen to clippy).
3. **Google Rust Style Guide** — https://google.github.io/styleguide/rustguide.html — code organization, `&T`-family borrows, enum over bool, Option/Result/panic reporting, trait usage, getter/setter naming, assert context strings, iterator chains, docs discipline.
4. **Microsoft Pragmatic Rust Guidelines** — https://microsoft.github.io/rust-guidelines/ — M-WEASEL-WORDS, M-SHORT-NAMES, M-REGULAR-FN, M-DONT-LEAK-TYPES, M-ERRORS-CANONICAL-STRUCTS, M-TAUTOLOGICAL-TESTS, M-NO-META-DESIGN-DOCUMENTATION, M-PANIC-MESSAGE.
5. **ANSSI Secure Rust Guidelines** — https://anssi-fr.github.io/rust-guide/ — MEM-LEAK/MEM-FORGET (no intentional leaks), LANG-CMP-INV (comparison-trait invariants), LANG-LIMIT-PANIC.
6. **Tiger Style** (TigerBeetle) — https://github.com/tigerbeetle/tigerbeetle/blob/main/docs/TIGER_STYLE.md — assert the negative space, state invariants positively, say why in comments.
7. **canonical/rust-best-practices** — https://github.com/canonical/rust-best-practices — error message phrasing, error-type layering (`Internal(#[from])`), doc first-sentence form, test discipline.
8. Comprehensive Rust idiomatic chapter — https://google.github.io/comprehensive-rust/idiomatic/welcome.html — newtype "parse, don't validate", owned/view pairs, sealed traits.

## Known conflicts (repo lints win)

- Google: prefer `expect` over `unwrap` → many repos deny both.
- Google/Microsoft: `#[non_exhaustive]` on public enums → repos requiring exhaustive domain matching reject it.
- Microsoft M-PANIC-ON-BUG (panic on invariant violation) → blanket panic denies win.
- Canonical: lifetime names avoid `'a` → ecosystem default is `'a` for single local lifetimes; follow the codebase.
