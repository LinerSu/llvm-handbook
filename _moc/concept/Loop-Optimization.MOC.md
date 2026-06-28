---
title: Loop Optimization
type: concept-moc
concepts: [loop-optimization]
tags: [moc, kind/moc]
status: draft
---

# Loop Optimization

> 🧭 **Concept MOC** · Chapter of [[Home]] · ecosystem view: [[LLVM.MOC]]
> **Prerequisites:** [[ssa-form]] · **Related chapters:** [[data-flow-analysis|Dataflow Analysis]]

> [!abstract] What this chapter delivers
> Loops as the arc *what a loop is → the structures that find it → the transforms → where it pays off → limits*. The detail lives in two atomic notes that this MOC threads together.

## 1. Definition & data structure
What a loop *is* in LLVM (a CFG + dominator-tree property, not syntax), its anatomy, and the canonical forms passes assume. → **[[loop-info|LoopInfo & Canonical Forms]]** *(data-structure · analysis)*

## 2. Theory / legality
Every transform is a **dependence-analysis legality test** + a rewrite (the golden rule). Memory legality is answered by [[memory-ssa|Memory SSA]] and [[pointer-alias-analysis|alias analysis]].

## 3. The transforms
Unrolling, peeling/splitting, LICM (+ rotation), vectorization, fission, fusion. → **[[loop-transformations|Loop Transformations]]** *(concept · optimization)*

## 4. Where it's used
Performance (locality, fewer branches), enabling vectorization and parallelism, and bounded model checking (full unrolling). → `application/` *(to be added)*

## 5. Limitations & future
Legality is bounded by dependence/alias precision; relational reasoning about indices (polyhedral) lives in **Polly** / the polyhedral model rather than core loop passes. → `theory/domains/polyhedra`, `implementation/polly` *(to be added)*

```dataview
TABLE facet, stage, status, src
WHERE contains(concepts, "loop-optimization")
SORT facet ASC
```
