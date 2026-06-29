---
title: SSA Form
type: concept-moc
concepts: [ssa]
tags: [moc, kind/moc]
status: draft
---

# SSA Form

> 🧭 **Concept MOC** · Chapter of [[Home]] · ecosystem view: [[LLVM.MOC]]
> **Prerequisites:** [[llvm-basics]] · [[dominator-tree]] · **Related chapters:** [[Memory-Optimization.MOC|Memory Optimization]] · [[Redundancy-Elimination.MOC|Redundancy Elimination]]

> [!abstract] What this chapter delivers
> The single-assignment backbone the whole optimizer assumes. The arc *what SSA is (one def per value, φ at merges) → the structure that places φ (dominance frontiers) → how it's constructed and lifted to memory → why every later pass needs it*.

## 1. Definition & structure
Every value is assigned **exactly once**; control-flow merges reconcile definitions with **φ nodes**; def-use / use-def chains come for free. → **[[ssa-form|SSA Form]]** *(data-structure · ir)*.

## 2. Theory — where φ goes
Minimal SSA places φ at **iterated dominance frontiers** (Cytron et al. 1991), computed from the [[dominator-tree|dominator tree]] over the [[control-flow-graph|CFG]].

## 3. Construction
LLVM scalars are SSA *by construction*; the real work is promoting memory to registers. → **[[mem2reg|mem2reg]]** (alloca → SSA + φ) and its prerequisite **[[scalar-replacement-of-aggregates|SROA]]** (split aggregates first).

## 4. Lifting to memory
Memory has no SSA names natively; **[[memory-ssa|Memory SSA]]** gives loads/stores the same def-use chains, enabling memory-aware optimization.

## 5. Where it's used
Foundational — [[Redundancy-Elimination.MOC|GVN/value-numbering]], [[Constant-Propagation.MOC|SCCP]], and [[loop-info|loop]] passes all assume SSA. It is why LLVM "never converts scalars to SSA": they already are.

## 6. Limitations & future
φ placement and renaming cost; aggregates and escaping addresses block promotion (SROA/mem2reg criteria); destruction (out-of-SSA) happens late in the backend.

```dataview
TABLE facet, stage, status, src
WHERE contains(concepts, "ssa")
SORT facet ASC
```
