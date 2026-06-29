---
title: Dataflow Analysis
type: concept-moc
concepts: [dataflow-analysis]
tags: [moc, kind/moc]
status: draft
---

# Dataflow Analysis

> 🧭 **Concept MOC** · Chapter of [[Home]] · ecosystem view: [[LLVM.MOC]]
> **Prerequisites:** [[control-flow-graph]] · **Related chapters:** [[Constant-Propagation.MOC|Constant & Value Propagation]] · [[SSA-Form.MOC|SSA Form]]

> [!abstract] What this chapter delivers
> The program-analysis backbone: compute, at every program point, a sound over-approximation of reachable states by iterating to a fixpoint. The arc *lattice/fixpoint theory → the monotone framework & worklist → LLVM/MLIR realizations → the analyses built on it → precision limits*.

## 1. Theory — lattices & fixpoints
A finite-height lattice + monotone transfer functions guarantees a fixpoint (Kleene/Kildall). → **[[dataflow-foundations|Dataflow Foundations]]** *(theory · analysis)*; the `lattice-theory` underpinnings.

## 2. The framework
The monotone dataflow framework, the worklist algorithm, **MFP vs. MOP** precision (equal iff transfer functions are distributive), and dataflow-as-abstract-interpretation. → **[[data-flow-analysis|Data-Flow Analysis]]** *(concept · analysis)*.

## 3. In LLVM / MLIR
Hand-rolled iterations in LLVM (`SparsePropagation`, SCCP), versus MLIR's reusable generic **`DataFlowSolver`** (`mlir/Analysis/DataFlow/`) — *not* in core LLVM.

## 4. Analyses built on it
- **[[sparse-conditional-constant-propagation|SCCP]]** — joint constant + reachability lattice.
- **[[lazy-value-info|Lazy Value Info]]** — on-demand per-edge value ranges/predicates.
- **[[correlated-value-propagation|Correlated Value Propagation]]** — simplifies from LVI ranges.
- Feeds [[value-numbering|value numbering]] and [[pointer-alias-analysis|alias analysis]].

## 5. Limitations & future
Precision is bounded by the abstract domain (constants/ranges, not relational); non-distributive analyses lose MOP precision. Relational domains (intervals → octagons → polyhedra) live in [[polyhedral-model|the polyhedral model]].

```dataview
TABLE facet, stage, status, src
WHERE contains(concepts, "dataflow-analysis")
SORT facet ASC
```
