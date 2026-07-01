---
title: Front-End & Source-Level Analysis
type: concept-moc
concepts: [source-level-analysis]
tags: [moc, kind/moc]
status: draft
---

# Front-End & Source-Level Analysis

> 🧭 **Concept MOC** · Chapter of [[Home]] · ecosystem view: [[LLVM.MOC]]
> **Prerequisites:** [[llvm-basics]] · **Related chapters:** [[Control-Flow.MOC|Control Flow]] · [[Dataflow-Analysis.MOC|Dataflow Analysis]]

> [!abstract] What this chapter delivers
> Analysis that runs on the **Clang AST/CFG** — *before* lowering to LLVM IR — and why a whole class of tools lives there. The arc *the two data structures (AST, source CFG) → the spine tradeoff (source vs IR) → the tools built on it (Static Analyzer, dataflow framework)*.

## 1. The spine — which level to analyze on
The organizing idea of the chapter: the **same** program can be analyzed on the source AST/CFG or on LLVM IR, and that choice trades **diagnostic fidelity for analytic power**. → **[[source-level-analysis|Source-Level vs IR-Level Program Analysis]]** *(concept · analysis)*.

## 2. The data structures
- **[[clang-ast|Clang AST]]** — the typed, sugar-preserving parse tree; retains source locations, `typedef`s, macros, templates *(data-structure · frontend)*.
- **[[clang-cfg|Clang CFG]]** — the source-level control-flow graph built from the AST, modelling C/C++ semantics (short-circuit, destructors) that the [[control-flow-graph|LLVM IR CFG]] has lowered away *(data-structure · frontend)*.
- *how the AST is built* → **[[clang-frontend-pipeline|Front-End Pipeline]]** — Lex → Parse → Sema → AST, with parsing interleaved with semantic analysis (`ActOn…`) *(implementation)*.
- *how you consume the AST* → **[[ast-traversal|AST Traversal]]** — `RecursiveASTVisitor`, AST matchers, `StmtVisitor` (the AST-side counterpart of IR's [[visitor-pattern|InstVisitor]]) *(concept)*.

## 3. The tools built on it
- **[[clang-static-analyzer|Clang Static Analyzer]]** — path-sensitive symbolic execution over the Clang CFG *(implementation)*.
- **[[lifetime-safety|Clang LifetimeSafety]]** — intra-procedural loan/origin dataflow over the Clang CFG for *temporal* safety (use-after-free, dangling captures) *(implementation)*.
- **[[clang-dataflow-framework|Clang Dataflow Framework]]** — the flow-sensitive, reusable analysis framework in `clang/include/clang/Analysis/FlowSensitive/` *(concept)*.
  - worked example: **[[dataflow-worked-example|A Minimal clang::dataflow Analysis]]** — the lattice API (`LatticeEffect`, `VarMapLattice`, `DataflowAnalysis`) mapped to the AI lattice + transfer + fixpoint, and where it stays non-relational *(application)*.
  - relational extension: **[[dataflow-relational-octagon|Wiring an Octagon into clang::dataflow]]** — which seam can hold a DBM: why `Environment::ValueModel` (per storage location) can't, and the user `LatticeT` can *(application)*.

## 4. Where it connects
Type/annotation *checking* happens here too → [[type-checking]]; the IR-side counterpart of these analyses is [[data-flow-analysis]] and [[pointer-alias-analysis|alias analysis]], which trade source fidelity for SSA and whole-program reach.

## 5. Limitations & future
Source-level analysis is typically **intra-TU** and lacks [[ssa-form|SSA]] def-use chains, so value tracking is hand-rolled; the frontier is the [[clang-dataflow-framework|flow-sensitive framework]] maturing into a general home for checks written per-analysis today.

```dataview
TABLE facet, stage, status, src
WHERE contains(concepts, "source-level-analysis") OR contains(concepts, "clang-ast") OR contains(concepts, "clang-cfg")
SORT facet ASC
```
