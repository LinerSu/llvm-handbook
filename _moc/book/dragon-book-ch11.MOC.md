---
title: Dragon Book Ch.11 — Optimizing for Parallelism and Locality → LLVM
type: book-moc
book: "Aho, Lam, Sethi, Ullman — Compilers: Principles, Techniques & Tools (Dragon Book, 2e)"
chapter: 11
tags: [moc, kind/moc, book]
status: draft
verified_on: 2026-06-28
---

# Dragon Book Ch.11 — Optimizing for Parallelism and Locality → LLVM

> 🧭 **Book bridge** · Chapter of [[Home]] · ecosystem map [[LLVM.MOC]]
> **Source:** Dragon Book (2e) Chapter 11, pp. 769–899.

> [!abstract] What this bridge delivers
> A **reading map** for the polyhedral/loop-parallelism chapter. Its affine-loop machinery is LLVM's **Polly**; its dependence theory is LLVM's `DependenceAnalysis`; its locality/parallelism payoffs are the loop vectorizer and tiling.

## 🗂 Section-by-section crosswalk

| § | Book topic | LLVM realization | Vault note |
|---|---|---|---|
| 11.1–11.2 | Basic concepts; matrix-multiply tiling | the polyhedral model; tiling for locality | [[polyhedral-model]] |
| 11.3 | Iteration spaces | iteration polytope of a SCoP | [[polyhedral-model]] |
| 11.4 | Affine array indexes | affine subscripts (recovered via SCEV) | [[polyhedral-model]], [[scalar-evolution]] |
| 11.5 | Data reuse | locality / cache modeling | [[polyhedral-model]] |
| 11.6 | **Array data-dependence analysis** | **`DependenceAnalysis`** / `LoopAccessAnalysis` | [[dependence-analysis]] |
| 11.7–11.8 | Synchronization-free parallelism; sync between loops | auto-parallelization (Polly); OpenMP lowering | [[polyhedral-model]], [[dependence-analysis]] |
| 11.9 | Pipelining (loops) | software pipelining | [[instruction-scheduling]] |
| 11.10 | Locality optimizations (tiling, interchange) | Polly tiling; `LoopInterchange`; vectorization | [[polyhedral-model]], [[loop-transformations]] |
| 11.11 | Other uses of affine transforms | affine reschedulings in Polly | [[polyhedral-model]] |

## 📚 Suggested reading path (book ↔ vault)

1. **§11.1–11.4 → [[polyhedral-model]]** (with [[scalar-evolution]] for affine indexes) — the iteration space and affine framing.
2. **§11.6 → [[dependence-analysis]]** — the legality oracle for everything else.
3. **§11.7–11.11 → [[polyhedral-model]] + [[loop-transformations]]** — parallelism, tiling, and where the vectorizer does the practical work.

## 📝 Reading notes — what's different in modern LLVM

> [!info] Three things to keep in mind while reading the book
> - **The polyhedral engine is Polly, and it's opt-in.** §11's affine transforms live in **Polly** (ISL-backed, on SCoPs), *not* the default `-O2/-O3` pipeline ([[polyhedral-model]]).
> - **In practice, vectorization carries the day.** Most of LLVM's locality/parallelism wins come from the **loop/SLP vectorizer** and simpler loop passes ([[loop-transformations]]); full polyhedral restructuring is the heavy option.
> - **Dependence analysis is the gate.** §11.6 is the legality test the vectorizer, loop passes, and Polly all consult ([[dependence-analysis]]).

```dataview
TABLE facet, stage, status
WHERE book AND contains(book, "§11")
SORT file.name ASC
```
