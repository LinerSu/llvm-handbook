---
title: Dragon Book Ch.9 — Machine-Independent Optimizations → LLVM
type: book-moc
book: "Aho, Lam, Sethi, Ullman — Compilers: Principles, Techniques & Tools (Dragon Book, 2e)"
chapter: 9
tags: [moc, kind/moc, book]
status: draft
verified_on: 2026-06-28
---

# Dragon Book Ch.9 — Machine-Independent Optimizations → LLVM

> 🧭 **Book bridge** · Chapter of [[Home]] · ecosystem map [[LLVM.MOC]]
> **Source:** Dragon Book (2e) Chapter 9, pp. 583–703.

> [!abstract] What this bridge delivers
> A **reading map** into LLVM's middle end: each §9 section points to the vault note covering the same idea in LLVM. The notes describe LLVM directly (with examples); the book is the optional companion for the theory.

## 🗂 Section-by-section crosswalk

| § | Book topic | LLVM realization | Vault note |
|---|---|---|---|
| 9.1 | Principal sources of optimization (CSE, copy/const prop, DCE, code motion, IV/strength reduction) | scalar passes across the middle end | [[value-numbering]], [[instruction-combining]], [[loop-transformations]] |
| 9.2 | Introduction to data-flow analysis | worklist over the CFG | [[data-flow-analysis]] |
| 9.3 | **Foundations of data-flow analysis** (lattices, monotone framework, MOP/MFP) | the theory every LLVM analysis instantiates | [[dataflow-foundations]] |
| 9.4 | Constant propagation | **SCCP** (sparse conditional) | [[data-flow-analysis]] |
| 9.5 | **Partial-redundancy elimination** | **load PRE in the GVN pass** | [[partial-redundancy-elimination]] |
| 9.6 | Loops in flow graphs (dominators, natural loops) | DominatorTree + LoopInfo | [[dominator-tree]], [[loop-info]] |
| 9.7 | Region-based analysis | *not* LLVM's approach — it uses iterative worklist dataflow | [[data-flow-analysis]] |
| 9.8 | Symbolic analysis (induction variables, affine exprs) | **ScalarEvolution (SCEV)** | [[scalar-evolution]] |

## 📚 Suggested reading path (book ↔ vault)

1. **§9.2–9.3 → [[data-flow-analysis]] then [[dataflow-foundations]]** — the framework and the lattice theory under it.
2. **§9.1, 9.4 → [[value-numbering]], [[data-flow-analysis]]** (SCCP) — the bread-and-butter scalar optimizations.
3. **§9.5 → [[partial-redundancy-elimination]]** — removing redundancy that plain CSE can't.
4. **§9.6, 9.8 → [[loop-info]] + [[scalar-evolution]]** — loops, and the symbolic analysis that drives loop transforms.

## 📝 Reading notes — what's different in modern LLVM

> [!info] Three things to keep in mind while reading the book
> - **No region-based analysis.** §9.7's interval/region method isn't how LLVM works; LLVM uses **iterative worklist** dataflow on the CFG ([[data-flow-analysis]]).
> - **PRE is mostly load PRE.** §9.5's full PRE / lazy code motion shows up in LLVM chiefly as **load PRE inside GVN**; full value-based GVN-PRE is off by default ([[partial-redundancy-elimination]]).
> - **Symbolic analysis = SCEV.** §9.8's induction-variable/affine analysis is LLVM's `ScalarEvolution`, expressed as **add recurrences `{start,+,step}<loop>`** ([[scalar-evolution]]).

```dataview
TABLE facet, stage, status
WHERE book AND contains(book, "§9")
SORT file.name ASC
```
