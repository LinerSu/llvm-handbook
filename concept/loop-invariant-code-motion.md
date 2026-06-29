---
title: Loop-Invariant Code Motion (LICM)
facet: concept
stage: optimization
ecosystem: [general, llvm]
concepts: [loop-optimization, redundancy-elimination]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/Scalar/LICM.cpp" }
data_structures: [loop-info, dominator-tree, memory-ssa]
src: "llvm/lib/Transforms/Scalar/LICM.cpp"
docs: "Passes — licm ↗ https://llvm.org/docs/Passes.html"
prereqs: [loop-info, ssa-form]
related: [loop-transformations, scalar-evolution, pointer-alias-analysis, memory-ssa]
tags: [kind/transform, status/verified]
status: verified
verified_on: 2026-06-28
sources:
  - "https://llvm.org/doxygen/LICM_8cpp.html"
  - "https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/LICM.cpp"
---

# Loop-Invariant Code Motion (LICM)

> 🧭 **Concept** · `concept · optimization · general+llvm` · Index [[LLVM.MOC]]
> **Prerequisites:** [[loop-info]], [[ssa-form]] · **Family:** [[loop-transformations]] · **Uses:** [[memory-ssa]], [[pointer-alias-analysis]]

> [!abstract] Chapter map
> A computation is **loop-invariant** if it yields the same value on every iteration. **LICM** moves such code out of the loop: **hoist** it into the **preheader** (run once before the loop) or **sink** it into the **exit blocks** (run once after), provided doing so is *safe* and *preserves semantics*.

> [!info]+ Classic LICM → LLVM
> | Classic | LLVM realization |
> |---|---|
> | Find invariants: operands defined outside the loop or themselves invariant | same fixed-point marking over the loop body |
> | Hoist to a single pre-loop block | hoist to the **preheader** (requires [[loop-info|LoopSimplify]] form) |
> | — | also **sink** invariant/dead-after-loop code to dedicated **exit** blocks |
> | Safety: must dominate all exits *or* be safe to speculate | same; plus alias checks for memory via [[memory-ssa]] |
> | Move loads/stores out (scalar promotion) | **promotion** of must-aliased loads/stores to a register around the loop |

---

## 1. The idea

> [!note] Invariant + safe = movable
> Code is hoistable when (a) it is **loop-invariant** (operands come from outside the loop or from already-hoisted instructions) and (b) moving it is **safe**: either it is **guaranteed to execute** (dominates all loop exits) or it has **no side effects and cannot fault** (safe to speculate). Sinking is the dual — move computations whose only uses are after the loop into the exit blocks.

## 2. Safety conditions (why LICM is careful)

> [!warning] What blocks a hoist
> - A faulting op (e.g. a `load` or `sdiv`) may be hoisted only if it is **guaranteed to execute** in the loop, or proven safe to speculate — otherwise hoisting could fault on an iteration count of zero.
> - A `load` may be hoisted only if **no aliasing store** in the loop can clobber it ([[pointer-alias-analysis|alias analysis]] + [[memory-ssa]]).
> - **Scalar promotion** of a memory location to a register requires the access to be **must-alias** and executed unconditionally, so the load-before / store-after rewrite is sound.

## 3. Algorithm

> [!example]- LICM sketch (click to expand)
> ```text
> require LoopSimplify form: a unique preheader + dedicated exit blocks
> mark invariants: fixpoint — an instr is invariant if all operands are
>                  defined outside the loop or are themselves invariant
> hoist: walk the loop in dominator order; for each invariant instr that is
>        safe-to-execute, move it to the preheader
> sink:  for invariant instrs whose uses are all outside the loop, move to exits
> promote: for must-aliased, unconditionally-accessed memory, introduce a
>          register temically (load in preheader, store in exits)
> ```

## 4. Worked example

> [!example]+ Hoisting an invariant multiply
> **Before:**
> ```llvm
> ; for (i=0; i<n; i++)  a[i] = x * y;   — x*y is invariant
> loop:
>   %i = phi i32 [0, %ph], [%i.next, %loop]
>   %m = mul i32 %x, %y          ; recomputed every iteration
>   ... store %m ...
> ```
> **After LICM:**
> ```llvm
> ph:                            ; preheader
>   %m = mul i32 %x, %y          ; hoisted: computed once
> loop:
>   %i = phi i32 [0, %ph], [%i.next, %loop]
>   ... store %m ...
> ```

## 5. In LLVM

> [!info] Where it lives
> [`Transforms/Scalar/LICM.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/LICM.cpp). It consumes [[loop-info|LoopInfo]], the [[dominator-tree]], alias analysis, and **[[memory-ssa|MemorySSA]]** (the modern mechanism for the memory legality checks, replacing the old AST-based version). It requires **LoopSimplify** form (a unique preheader and dedicated exits) — usually ensured by running loop canonicalization first; see [[loop-info]].

## 6. Limitations

> [!warning] Tradeoffs
> - Hoisting increases **register pressure** in the preheader; LLVM balances this against the redundancy removed.
> - Memory hoisting/promotion is only as precise as [[pointer-alias-analysis|alias analysis]] — a conservative may-alias blocks the move.
> - Pairs with the rest of [[loop-transformations]] (unroll, rotate, unswitch) which reshape the loop so more code becomes invariant.

> [!summary] The one thing to remember
> LICM hoists loop-invariant code to the **preheader** and sinks it to **exit blocks**, gated by safety (guaranteed-to-execute or speculation-safe) and, for memory, by [[memory-ssa|MemorySSA]] + alias analysis. It needs LoopSimplify form.

> [!quote] Sources & confidence
> - **Source:** [`Transforms/Scalar/LICM.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/LICM.cpp) — tier-1.
> - [LLVM Passes — `licm`](https://llvm.org/docs/Passes.html).
> - **Also in:** Muchnick *Advanced Compiler Design & Impl.* §13.2 — loop-invariant code motion.
