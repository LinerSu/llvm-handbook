---
title: Dragon Book Ch.12 — Interprocedural Analysis → LLVM
type: book-moc
book: "Aho, Lam, Sethi, Ullman — Compilers: Principles, Techniques & Tools (Dragon Book, 2e)"
chapter: 12
tags: [moc, kind/moc, book]
status: draft
verified_on: 2026-06-28
---

# Dragon Book Ch.12 — Interprocedural Analysis → LLVM

> 🧭 **Book bridge** · Chapter of [[Home]] · ecosystem map [[LLVM.MOC]]
> **Source:** Dragon Book (2e) Chapter 12, pp. 903–958.

> [!abstract] What this bridge delivers
> A **reading map** into LLVM's interprocedural layer (IPO): each §12 section points to the vault note covering the same idea in LLVM. Notes describe LLVM directly; the book is the optional companion.

## 🗂 Section-by-section crosswalk

| § | Book topic | LLVM realization | Vault note |
|---|---|---|---|
| 12.1 | Basic concepts (call graph, call sites, contexts) | `CallGraph` / `LazyCallGraph`, CGSCC bottom-up | [[call-graph]] |
| 12.2 | Why interprocedural analysis? | inlining as the motivating IPO | [[inlining]] |
| 12.3 | A logical (Datalog) representation of data flow | Andersen's points-to as **inclusion constraints** | [[pointer-alias-analysis]] |
| 12.4 | A simple pointer-analysis algorithm (Andersen) | inclusion-based AA (LLVM `cfl-anders-aa`); cf. equality-based [[unification|Steensgaard]] | [[pointer-alias-analysis]], [[unification]] |
| 12.5 | Context-insensitive interprocedural analysis | flow-/context-insensitive AA | [[pointer-alias-analysis]] |
| 12.6 | Context-sensitive pointer analysis (cloning) | **DSA** bottom-up/top-down cloning | [[pointer-alias-analysis]] |
| 12.7 | Datalog implementation by BDDs | (niche; not a core LLVM technique) | — |

## 📚 Suggested reading path (book ↔ vault)

1. **§12.1 → [[call-graph]]** — the graph and the bottom-up CGSCC order.
2. **§12.2 → [[inlining]]** — the flagship interprocedural transform (and why callee-before-caller order matters).
3. **§12.3–12.4 → [[pointer-alias-analysis]] + [[unification]]** — Andersen (inclusion) vs Steensgaard (equality/unification).
4. **§12.6 → [[pointer-alias-analysis]]** — context sensitivity via DSA's BU/TD cloning.

## 📝 Reading notes — what's different in modern LLVM

> [!info] Three things to keep in mind while reading the book
> - **Interprocedural ≈ run bottom-up over the call graph.** LLVM's CGSCC pass manager visits SCCs callee-first; that order *is* the practical face of "interprocedural" ([[call-graph]], [[inlining]]).
> - **Andersen vs Steensgaard, both shipped.** §12.4's inclusion-based Andersen is LLVM's `cfl-anders-aa`; the equality/[[unification]]-based Steensgaard is `cfl-steens-aa`. Full context-sensitive **DSA** lives in the external `poolalloc` module, not core ([[pointer-alias-analysis]]).
> - **Inlining often substitutes for analysis.** In practice LLVM gets much interprocedural precision simply by **inlining** and then running intraprocedural passes, rather than a separate whole-program analysis.

```dataview
TABLE facet, stage, status
WHERE book AND contains(book, "§12")
SORT file.name ASC
```
