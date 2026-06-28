---
title: Muchnick — Advanced Compiler Design & Implementation → LLVM
type: book-moc
book: "Steven Muchnick — Advanced Compiler Design and Implementation (1997)"
tags: [moc, kind/moc, book]
status: draft
verified_on: 2026-06-28
---

# Muchnick — *Advanced Compiler Design and Implementation* → LLVM

> 🧭 **Book bridge** · Chapter of [[Home]] · ecosystem map [[LLVM.MOC]]
> **Source:** Muchnick, *Advanced Compiler Design and Implementation* (1997), 887 pp.

> [!abstract] What this bridge delivers
> A **reading map** for Muchnick — the implementation-focused classic. Because its chapters 7–20 *are* LLVM's middle + back end, most map onto notes you already have; it's the **second, often-canonical source** (especially for SSA construction, PRE, value numbering, register allocation, and code scheduling). The vault notes describe LLVM directly; Muchnick is the deeper reference in the footer.

## 🗂 Chapter-by-chapter crosswalk (LLVM-relevant chapters)

| Ch | Muchnick topic | Vault note(s) |
|---|---|---|
| 7 | Control-flow analysis (dominators, intervals, natural loops) | [[control-flow-graph]], [[dominator-tree]], [[loop-info]] |
| 8 | Data-flow analysis (iterative; control-tree/interval) | [[data-flow-analysis]], [[dataflow-foundations]] |
| 9 | Dependence analysis & dependence graphs | [[dependence-analysis]] |
| 10 | Alias analysis | [[pointer-alias-analysis]] |
| 12 | Early optimizations (value numbering, SCCP, copy/const prop) | [[value-numbering]], [[data-flow-analysis]], [[instruction-combining]] |
| 13 | Redundancy elimination (**PRE**, CSE, LICM, hoisting) | [[partial-redundancy-elimination]], [[value-numbering]], [[loop-transformations]] |
| 14 | Loop optimizations (induction vars, **strength reduction**) | [[induction-variables-and-strength-reduction]], [[scalar-evolution]], [[loop-transformations]] |
| 15 | Procedure optimizations (integration / in-lining, tail calls) | [[inlining]] |
| 16 | Register allocation (graph coloring) | [[register-allocation]] |
| 17 | Code scheduling (list scheduling, software pipelining) | [[instruction-scheduling]] |
| 18 | Control-flow & low-level optimizations (DCE, branch opts) | [[instruction-combining]], [[control-flow-graph]] |
| 19 | Interprocedural analysis & optimization | [[call-graph]], [[inlining]], [[pointer-alias-analysis]] |
| 20 | Optimization for the memory hierarchy (tiling, scalar replacement) | [[polyhedral-model]], [[loop-transformations]] |

## 📚 Where Muchnick is the *better* read

> [!info] Reach for Muchnick over the Dragon Book on
> - **SSA & value numbering** ([[ssa-form]], [[value-numbering]]) — concrete construction.
> - **Partial-redundancy elimination** ([[partial-redundancy-elimination]]) — the canonical algorithmic treatment.
> - **Induction variables & strength reduction** ([[induction-variables-and-strength-reduction]]) — §14 is the reference.
> - **Register allocation by graph coloring** ([[register-allocation]]) and **code scheduling** ([[instruction-scheduling]]).

## 📝 Reading note

> [!info] One LLVM divergence to keep in mind
> Muchnick §8 develops **control-tree / interval-based** data-flow analysis at length. **LLVM does not use it** — it relies on **iterative worklist** dataflow ([[data-flow-analysis]]). Read the interval material as background, not as LLVM's method.

> [!quote] Excluded (not LLVM-core)
> Chapters 1–6 (ICAN notation, symbol tables, IR, run-time support, automatic code-generator generation) and 11/21 (intro, case studies) are frontend/infra/pedagogical and out of scope for this LLVM vault.
