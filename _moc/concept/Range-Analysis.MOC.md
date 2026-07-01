---
title: Value-Range & Constraint Reasoning
type: concept-moc
concepts: [range-analysis]
tags: [moc, kind/moc, status/draft]
status: draft
---

# Value-Range & Constraint Reasoning

> 🧭 **Concept MOC** · Chapter of [[Home]] · ecosystem view: [[LLVM.MOC]]
> **Prerequisites:** [[llvm-basics]], [[dominator-tree]] · **Related chapters:** [[Dataflow-Analysis.MOC|Dataflow Analysis]] · [[Constant-Propagation.MOC|Constant Propagation]]

> [!abstract] What this chapter delivers
> The LLVM passes that reason about **what values can hold** at a program point — from per-value **ranges** to **relational constraints** between values — and use that to fold comparisons, propagate facts, and delete dead branches. The arc: *per-value ranges → predicate propagation → relational (multi-variable) constraints*.

## 1. Per-value ranges — LazyValueInfo
Lazily computes a **constant range** for a value at a location, on demand, from dominating conditions → **[[lazy-value-info|LazyValueInfo (LVI)]]** *(concept · analysis)*.

## 2. Using ranges to transform — Correlated Value Propagation
The client that turns LVI facts into rewrites (fold comparisons, narrow ops, remove redundant checks) → **[[correlated-value-propagation|Correlated Value Propagation (CVP)]]** *(concept · optimization)*.

## 3. Relational constraints — ConstraintElimination
Steps up from per-value ranges to **relations between values** (`a·x − b·y ≤ c`): keeps signed/unsigned inequality systems and decides implication by **Fourier–Motzkin**, folding comparisons a range analysis can't — the pass behind redundant bounds-check removal → **[[constraint-elimination|LLVM ConstraintElimination]]** *(implementation · optimization)*.

## 4. Where it connects
These are the applied face of [[data-flow-analysis|dataflow analysis]] (lattices, fixpoint) specialized to value ranges/relations; they feed and overlap [[sparse-conditional-constant-propagation|SCCP]] and [[jump-threading|jump threading]]. The relational step (§3) is a lightweight cousin of classic relational **abstract domains** (Zones/Octagon/Polyhedra) — which maintain a *closed* domain rather than re-deriving per query.

## 5. Limitations & future
Per-value ranges miss correlations between variables; the relational pass re-runs Fourier–Motzkin per query (no maintained closure) and caps at 64-bit coefficients / mostly two-variable constraints — the frontier is stronger maintained relational domains for loop-carried facts.

```dataview
TABLE facet, stage, status, src WHERE contains(concepts, "range-analysis") SORT facet ASC
```
