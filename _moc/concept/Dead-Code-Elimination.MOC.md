---
title: Dead-Code Elimination
type: concept-moc
concepts: [dead-code]
tags: [moc, kind/moc]
status: draft
---

# Dead-Code Elimination

> 🧭 **Concept MOC** · Chapter of [[Home]] · ecosystem view: [[LLVM.MOC]]
> **Prerequisites:** [[ssa-form]] · **Related chapters:** [[Redundancy-Elimination.MOC|Redundancy Elimination]] · [[Constant-Propagation.MOC|Constant Propagation]]

> [!abstract] What this chapter delivers
> Remove computation whose result is never observed. The arc *what "dead" means (no observable effect) → liveness vs. reachability → scalar dead code, dead stores, and the interprocedural case → the LLVM passes*.

## 1. Definition
Code is **dead** if removing it cannot change observable program behavior — either its result is unused (dead value) or its memory write is overwritten/unread before any read (dead store).

## 2. Theory
Liveness is a backward dataflow problem; aggressive DCE instead assumes everything dead until proven live (optimistic), which removes whole dead cycles a conservative pass keeps. → [[data-flow-analysis|Dataflow Analysis]].

## 3. The transforms
- **[[dead-code-elimination|Dead-Code Elimination]]** — DCE/ADCE: remove instructions with no live uses (ADCE works optimistically over the SSA graph).
- **[[dead-store-elimination|Dead-Store Elimination]]** — remove stores killed by a later store with no intervening read (uses [[memory-ssa|Memory SSA]] + alias analysis).
- **[[interprocedural-dead-code-elimination|Interprocedural DCE]]** — drop unreachable functions/globals and dead arguments/returns across the [[call-graph|call graph]].

## 4. In LLVM
`dce`/`adce`, `dse`, and `globaldce`/`deadargelim`; runs throughout the pipeline to clean up after other passes expose dead code.

## 5. Where it's used
Cleanup after inlining, SCCP, and SROA — most dead code is *created* by other optimizations, so DCE runs repeatedly.

## 6. Limitations & future
Dead-store precision is bounded by alias analysis; interprocedural cases need whole-program (LTO) visibility to be effective.

```dataview
TABLE facet, stage, status, src
WHERE contains(concepts, "dead-code")
SORT facet ASC
```
