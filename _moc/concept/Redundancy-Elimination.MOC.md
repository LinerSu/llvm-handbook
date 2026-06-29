---
title: Redundancy Elimination
type: concept-moc
concepts: [redundancy-elimination, value-numbering]
tags: [moc, kind/moc]
status: draft
---

# Redundancy Elimination

> 🧭 **Concept MOC** · Chapter of [[Home]] · ecosystem view: [[LLVM.MOC]]
> **Prerequisites:** [[ssa-form]] · **Related chapters:** [[data-flow-analysis|Dataflow Analysis]] · [[Dead-Code-Elimination.MOC|Dead-Code Elimination]]

> [!abstract] What this chapter delivers
> Don't compute the same value twice. The arc *what "the same value" means → how we prove sameness (value numbering) → eliminating fully vs. partially redundant computations → the LLVM passes that realize it → limits*.

## 1. Definition
A computation is **redundant** if its result is already available on every path reaching it (fully redundant) or on some paths (partially redundant). Eliminating it replaces the recomputation with the earlier value.

## 2. Theory — proving "same value"
Two expressions are equivalent if they have the same **value number**. → **[[value-numbering|Value Numbering]]** (LVN within a block, GVN across the CFG using SSA + dominance).

## 3. The transforms
- **[[early-cse|Early CSE]]** — cheap, dominator-tree-scoped common-subexpression elimination run early to clean up.
- **[[partial-redundancy-elimination|Partial Redundancy Elimination]]** — code motion that turns partially-redundant into fully-redundant, then removes it (subsumes CSE + loop-invariant motion).

## 4. In LLVM
GVN is the workhorse pass that fuses value numbering with load/redundancy elimination and load-PRE. → **[[llvm-gvn|llvm: GVN]]** *(implementation · optimization)*. Related memory cleanups: [[memcpy-optimization|MemCpyOpt]].

## 5. Where it's used
Every `-O1+` pipeline; biggest wins on redundant loads/address computations exposed after inlining and SROA.

## 6. Limitations & future
Precision is bounded by alias analysis (for loads) and by SSA structure; full GVN-PRE is expensive and off by default (see [[llvm-version]]).

```dataview
TABLE facet, stage, status, src
WHERE contains(concepts, "redundancy-elimination") OR contains(concepts, "value-numbering")
SORT facet ASC
```
