---
title: Constant & Value Propagation
type: concept-moc
concepts: [constant-propagation]
tags: [moc, kind/moc]
status: draft
---

# Constant & Value Propagation

> 🧭 **Concept MOC** · Chapter of [[Home]] · ecosystem view: [[LLVM.MOC]]
> **Prerequisites:** [[ssa-form]] · [[data-flow-analysis|Dataflow Analysis]] · **Related chapters:** [[Dead-Code-Elimination.MOC|Dead-Code Elimination]] · [[Interprocedural-Analysis.MOC|Interprocedural]]

> [!abstract] What this chapter delivers
> Replace values known at compile time with constants, and prune the branches they make unreachable. The arc *lattice of known values → optimistic sparse propagation (SCCP) → range/predicate-based propagation (LVI/CVP) → the interprocedural lift (IPSCCP)*.

## 1. Definition
**Constant propagation** substitutes a variable with a value proven constant on all reaching paths; **conditional** variants simultaneously discover which CFG edges are executable, so constants flow only along feasible paths.

## 2. Theory — lattices & optimism
The value lattice `⊤ (unknown) → constants → ⊥ (overdefined)`; SCCP is *optimistic* (assume `⊤`, lower only on evidence), which beats pessimistic propagation by also killing unreachable branches. → [[data-flow-analysis|Dataflow Analysis]], `lattice-theory`.

## 3. The transforms
- **[[sparse-conditional-constant-propagation|SCCP]]** — joint constant + reachability over the SSA def-use graph.
- **[[lazy-value-info|Lazy Value Info]]** — on-demand per-edge value *ranges* / predicates.
- **[[correlated-value-propagation|Correlated Value Propagation]]** — uses LVI to simplify comparisons, branches, and casts from known ranges.

## 4. Interprocedural
- **[[ipsccp|IPSCCP]]** — SCCP across the [[call-graph|call graph]]: propagates constant arguments/returns and prunes dead functions.

## 5. Where it's used
Foundational `-O1+` cleanup; especially powerful post-inlining when call-site constants become visible.

## 6. Limitations & future
Range precision is bounded by the abstract domain (constants/ranges, not relational); interprocedural reach needs visibility (LTO) to constant-fold across modules.

```dataview
TABLE facet, stage, status, src
WHERE contains(concepts, "constant-propagation")
SORT facet ASC
```
