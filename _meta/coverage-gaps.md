---
title: Coverage Gaps (what the book does not cover yet)
type: meta
tags: [meta, rulebook, backlog]
---

# Coverage gaps — the backlog

The known-missing topics, so the answer to *"what's left?"* travels via **git rather than chat history** (same rationale as [[improvement-ledger]]). Scope of this ledger: **classical compiler / LLVM**. ML-compiler topics (MLIR dialects, tensor/XLA-style stacks) are deliberately **out of scope** and are not tracked here.

> [!warning] Planned note names are written as `code`, never as double-bracket links
> A double-bracket link to a note that does not exist yet is a **broken wikilink**, which `vault-lint` reports as an ERROR — so this ledger keeps planned names in backticks and converts them to links only once the note lands. (Writing the literal syntax here, even inside backticks, trips the linter: it scans the whole file, code spans included.)

## How this list was produced

Grep each candidate topic across the content folders (`concept/ data-structure/ implementation/ theory/ algorithm/ application/`), then separate **"mentioned in passing"** from **"has a dedicated note."** A topic named in five notes but titled in none is still a gap. Re-run:

```bash
grep -rIliE '<topic pattern>' concept data-structure implementation theory algorithm application
grep -rhiE '^title:' concept data-structure implementation theory algorithm application   # is it TITLED anywhere?
grep -rhE '^stage:' concept data-structure implementation theory algorithm application | sort | uniq -c   # density per phase
```

Use `-E` with plain `|` alternation — `\|` inside `-E` matches a literal pipe and silently finds nothing.

## Tier 1 — recommended next

Each closes a real hole in the pipeline. `concepts:` is a *proposal*; confirm against [[controlled-vocabulary]] and the [[classification-protocol]] before authoring.

| Topic | Would cover | `src:` | Proposed facet · stage · concepts |
|---|---|---|---|
| `pgo-and-profile` | instrumentation vs sampling PGO; `BranchProbabilityInfo` / `BlockFrequencyInfo`; how profiles reach [[inlining]] and block placement | `llvm/lib/Transforms/Instrumentation/PGOInstrumentation.cpp`, `llvm/lib/Analysis/BlockFrequencyInfo.cpp` | concept · analysis · **new key** (gate) |
| `exception-handling` | `invoke`/`landingpad`/personality, EH tables, `DwarfEHPrepare`; the Clang half is `CGException.cpp` | `llvm/lib/CodeGen/DwarfEHPrepare.cpp`, `clang/lib/CodeGen/CGException.cpp` | concept · codegen · `code-generation` |
| `atomics-and-memory-model` | LLVM's ordering (`monotonic`→`seq_cst`), fences, `AtomicExpandPass`; pairs with [[thread-sanitizer]] | `llvm/lib/CodeGen/AtomicExpandPass.cpp` + LangRef | concept · ir · **new key** (gate) |
| `machine-level-optimizations` | the MIR counterparts of the middle end: MachineLICM/CSE/Sink, BranchFolding, MachineBlockPlacement | `llvm/lib/CodeGen/` | concept · codegen · `code-generation` |
| `stack-protector` | stack canaries, `-fstack-protector-strong`, where the check is inserted | `llvm/lib/CodeGen/StackProtector.cpp` | implementation · codegen · `memory-safety` |
| `tablegen` | how target descriptions/`.td` generate the backend; why ISel and MC are table-driven | `llvm/utils/TableGen`, `llvm/lib/Target/*/*.td` | concept · meta · `code-generation` |

## Tier 2 — smaller, or currently folded into a larger note

| Topic | Status today | `src:` |
|---|---|---|
| `loop-idiom-recognition` | uncovered; distinct from [[memcpy-optimization]] | `llvm/lib/Transforms/Scalar/LoopIdiomRecognize.cpp` |
| `coroutines` | uncovered (niche) | `llvm/lib/Transforms/Coroutines` |
| SelectionDAG deep-dive (legalization, DAGCombine) | [[instruction-selection]] covers ISel broadly | `llvm/lib/CodeGen/SelectionDAG` |
| Module-level IPO (`globalopt`, `globaldce`, `argpromotion`, `deadargelim`) | partly via [[interprocedural-dead-code-elimination]] and [[call-graph]] | `llvm/lib/Transforms/IPO` |
| Prologue/epilogue insertion & stack layout | partly via [[shrink-wrapping]] | `llvm/lib/CodeGen/PrologEpilogInserter.cpp` |

## Tier 3 — a "Clang Tooling" chapter

Front-end-*adjacent*: how out-of-tree tools consume the AST. Deliberately excluded from the front-end chapter (see [[Source-Level-Analysis.MOC]]) because it is tooling, not the front end proper.

| Topic | Would cover | `src:` |
|---|---|---|
| `libtooling` | `ClangTool`, `CompilationDatabase`, how clang-tidy/out-of-tree tools run | `clang/lib/Tooling` |
| `ast-matchers` | promote the matcher DSL out of [[ast-traversal]] into its own note | `clang/lib/ASTMatchers` |
| `clang-rewrite` | `Rewriter`, fix-its, source-to-source transformation | `clang/lib/Rewrite` |
| `clangir` | CIR: an MLIR-based IR between AST and LLVM IR (emerging → `version-sensitive`) | `clang/lib/CIR` |

## Judged adequate — not gaps

Recorded so they don't get re-proposed each session:

- **Abstract interpretation**, **lattice theory** — no standalone note, but well covered across [[dataflow-foundations]], [[data-flow-analysis]], [[dataflow-relational-octagon]] and [[lazy-value-info]].
- **Parsing / lexing theory** (Dragon Ch.3–4: regex→DFA, LL/LR tables) — the vault is **LLVM-first**; [[clang-preprocessor]] and [[clang-frontend-pipeline]] describe what Clang actually does instead.
- **Loop unrolling / rotation / fusion** — folded into [[loop-transformations]] by design.
- **UBSan** — not an IR pass; it is emitted in Clang CodeGen, and is noted as such in [[sanitizers]].

## Coverage snapshot

Notes per pipeline phase (`stage:`), to spot the next thin area:

```dataview
TABLE length(rows) AS Notes
FROM "concept" OR "data-structure" OR "implementation" OR "theory" OR "algorithm" OR "application"
WHERE stage
GROUP BY stage
SORT length(rows) DESC
```

> [!note] As of 2026-07-20
> `optimization` 31 · `analysis` 27 · `codegen` 12 · `ir` 10 · `frontend` 9 · `runtime` 4 · `meta` 1.
> `runtime` was **0** until the [[sanitizers]] chapter; it is still the thinnest real phase, which is why Tier 1 leans that way (PGO, atomics, stack-protector).

> [!quote] Related process notes
> [[note-checklist]] (definition of done, incl. what `verified` means) · [[classification-protocol]] (how to file a new topic) · [[controlled-vocabulary]] (axis values; minting a new `concepts:` key triggers the confidence gate) · [[chapter-bridge-pipeline]] (textbook chapter → LLVM) · [[improvement-ledger]] (per-note improvement queue).
