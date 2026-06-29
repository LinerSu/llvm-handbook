---
title: Controlled Vocabulary
type: meta
tags: [meta, rulebook]
---

# Controlled Vocabulary

Single source of truth for axis values and tags. Reuse a value before minting a new one; this prevents tag drift (`torch` vs `pytorch`, `opt` vs `optimization`).

## facet (finite — also the folder)
`concept` · `theory` · `algorithm` · `data-structure` · `implementation` · `application`

## stage (finite)
`frontend` · `ir` · `analysis` · `optimization` · `codegen` · `runtime` · `meta`

## ecosystem (open — extend with care)
`general` (cross-cutting) · `llvm` · `mlir` · `clang` · `lld` · `lldb` · `polly` · `rust` · `swift` · `jax` · `pytorch`
> Synonyms to normalize: `torch`→`pytorch`, `clang-frontend`→`clang`, `xla`→`jax` (when about JAX's backend).

## status (finite)
`stub` (placeholder) · `draft` (content, unchecked) · `unverified` · `verified` · `disputed` · `needs-review` · `migrated` (ported from the old vault, pending re-verify)

## kind/* tags (free-ish, reuse existing)
`kind/concept` · `kind/theory` · `kind/algorithm` · `kind/data-structure` · `kind/transform` · `kind/analysis` · `kind/pass` · `kind/moc`

## concepts (the chapter keys — grows over time)
`llvm-architecture` · `llvm-ir` · `addressing` · `ssa` · `memory-analysis` · `loop-optimization` · `redundancy-elimination` · `value-numbering` · `peephole-optimization` · `canonicalization` · `alias-analysis` · `points-to` · `dataflow-analysis` · `control-flow` · `dominance` · `code-generation` · `intermediate-code` · `three-address-code` · `control-flow-translation` · `type-checking` · `type-systems` · `unification` · `type-inference` · `register-allocation` · `instruction-selection` · `lattice-theory` · `partial-redundancy` · `scalar-evolution` · `call-graph` · `interprocedural` · `inlining` · `instruction-scheduling` · `polyhedral` · `dependence-analysis` · `induction-variables` · `strength-reduction` · `dead-code` · `memory-optimization` · `constant-propagation` · `tail-call` · `garbage-collection` · `visitor-pattern` · `ir-traversal` · `range-analysis`

## Optional `book:` field & book bridges

Notes ported from or connected to a textbook carry an optional `book:` frontmatter field (e.g. `book: "Dragon Book (…) §6.2"`). **Book-bridge MOCs** live in `_moc/book/` (e.g. [[dragon-book-ch6.MOC]]) and crosswalk a chapter's sections to vault notes + LLVM realizations.

## LLVM version

The LLVM release the vault tracks lives in one place — [[llvm-version]] (frontmatter `llvm_stable`). Don't hardcode release numbers in content notes. A note whose accuracy depends on the version carries the **`version-sensitive`** tag and links to `[[llvm-version]]`; a monthly scheduled task re-checks the latest release.
