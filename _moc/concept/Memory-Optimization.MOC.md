---
title: Memory Optimization
type: concept-moc
concepts: [memory-optimization]
tags: [moc, kind/moc]
status: draft
---

# Memory Optimization

> 🧭 **Concept MOC** · Chapter of [[Home]] · ecosystem view: [[LLVM.MOC]]
> **Prerequisites:** [[ssa-form]] · [[pointer-alias-analysis]] · **Related chapters:** [[SSA-Form.MOC|SSA Form]] · [[Dead-Code-Elimination.MOC|Dead-Code Elimination]]

> [!abstract] What this chapter delivers
> Get values out of memory and remove pointless memory traffic. The arc *split aggregates → promote stack slots to registers → eliminate dead/forwarded loads and stores*. The legality currency throughout is **alias analysis** + [[memory-ssa|Memory SSA]].

## 1. Split aggregates
Break structs/arrays into independent scalar slots so each can be promoted. → **[[scalar-replacement-of-aggregates|SROA]]** (runs before mem2reg).

## 2. Promote to registers
Turn promotable `alloca`s (address never escapes) into SSA values + φ — the single biggest source of downstream optimization. → **[[mem2reg|mem2reg]]**.

## 3. Remove redundant traffic
- **[[dead-store-elimination|Dead-Store Elimination]]** — drop stores killed by a later store with no intervening read.
- **[[memcpy-optimization|MemCpy Optimization]]** — forward, merge, and eliminate `memcpy`/`memset`/`memmove` and call-by-value copies.

## 4. Where it's used
Foundational `-O1+` cleanup; SROA + mem2reg are what make front-end "everything is a stack slot" code fast, and they expose work for [[Redundancy-Elimination.MOC|GVN]] and [[Constant-Propagation.MOC|SCCP]].

## 5. Limitations & future
Promotion is blocked by escaping addresses and aggregates SROA can't split; store/copy elimination precision is bounded by [[pointer-alias-analysis|alias analysis]] and [[memory-ssa|Memory SSA]] resolution.

```dataview
TABLE facet, stage, status, src
WHERE contains(concepts, "memory-optimization")
SORT facet ASC
```
