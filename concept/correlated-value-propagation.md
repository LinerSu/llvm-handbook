---
title: Correlated Value Propagation (CVP)
facet: concept
stage: optimization
ecosystem: [general, llvm]
concepts: [range-analysis, constant-propagation, dataflow-analysis]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/Scalar/CorrelatedValuePropagation.cpp" }
data_structures: [dominator-tree]
src: "llvm/lib/Transforms/Scalar/CorrelatedValuePropagation.cpp"
docs: "CorrelatedValuePropagation doxygen ↗ https://llvm.org/doxygen/CorrelatedValuePropagation_8cpp.html"
prereqs: [lazy-value-info]
related: [lazy-value-info, sparse-conditional-constant-propagation, instruction-combining]
tags: [kind/transform, status/verified]
status: verified
verified_on: 2026-06-28
sources:
  - "https://llvm.org/doxygen/CorrelatedValuePropagation_8cpp.html"
  - "https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/CorrelatedValuePropagation.cpp"
---

# Correlated Value Propagation (CVP)

> 🧭 **Concept** · `concept · optimization · general+llvm` · Index [[LLVM.MOC]]
> **Prerequisites:** [[lazy-value-info]] · **Sibling consumer:** [[jump-threading]] · **Contrast:** [[sparse-conditional-constant-propagation]]

> [!abstract] Chapter map
> **CVP** is the transform that *uses* [[lazy-value-info|LVI]]'s ranges. Wherever a value's range — *correlated* with the path taken to reach it — pins down a result, CVP rewrites the IR: fold a comparison to a constant, narrow a wide operation, drop a redundant cast, or attach `nsw`/`nuw`/`range` facts.

> [!info]+ What LVI knows → what CVP does
> | LVI fact at a point | CVP rewrite |
> |---|---|
> | `icmp` is always true/false on this path | replace with `i1 true`/`false` |
> | value range fits a narrower width | **narrow** the arithmetic (e.g. i64 → i32) |
> | shift/div operand range is safe | remove guards; mark exact / no-wrap |
> | add/sub cannot overflow on this range | set **`nsw`/`nuw`** |
> | known non-null / non-zero | delete null checks; simplify `udiv`/`urem` |

---

## 1. What it does

> [!note] Range-driven simplification
> CVP walks the function and, for each candidate instruction, queries [[lazy-value-info|LVI]] for the operand ranges *at that program point*. Because LVI's ranges are **edge-sensitive**, CVP catches simplifications that a flow-insensitive pass cannot — the "correlation" is between a value and the branch outcomes that led to it. It uses LVI plus the [[dominator-tree|DominatorTree]].

## 2. Worked example

> [!example]+ Folding a correlated comparison
> ```llvm
> ;  if (x > 10) {  ...  use (x > 5) ...  }
> entry:
>   %c1 = icmp sgt i32 %x, 10
>   br i1 %c1, label %then, label %end
> then:
>   %c2 = icmp sgt i32 %x, 5     ; on this edge LVI knows x ∈ [11, INT_MAX]
>   br i1 %c2, label %a, label %b
> ```
> LVI reports `%x ∈ [11, INT_MAX]` on the `%then` edge, so `%c2` is always true; CVP replaces it with `true`, and later [[simplifycfg|SimplifyCFG]] deletes the dead `%b` path.

## 3. In LLVM

> [!info] Where it lives
> [`Transforms/Scalar/CorrelatedValuePropagation.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/CorrelatedValuePropagation.cpp), scheduled in the `-O2`/`-O3` scalar pipeline, typically near [[jump-threading|JumpThreading]] (the other LVI consumer). CVP **preserves** LVI; the analysis is released once both have run.

## 4. CVP vs SCCP vs the analysis

> [!tip] Division of labor
> - [[lazy-value-info|LVI]] = the **analysis** (ranges on demand).
> - **CVP** = the **transform** that rewrites IR from those ranges.
> - [[sparse-conditional-constant-propagation|SCCP]] = a *different*, eager whole-function pass that propagates **constants** (and lattice-reachability), not edge-correlated ranges. CVP complements it on the range/correlation cases SCCP misses.

> [!summary] The one thing to remember
> CVP is the IR-rewriting consumer of [[lazy-value-info|LVI]]: it turns edge-correlated value ranges into concrete simplifications — folded comparisons, narrowed ops, dropped casts, `nsw`/`nuw`/`range` facts — alongside JumpThreading.

> [!quote] Sources & confidence
> - **Source:** [`Transforms/Scalar/CorrelatedValuePropagation.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/CorrelatedValuePropagation.cpp) — tier-1.
> - [CorrelatedValuePropagation doxygen](https://llvm.org/doxygen/CorrelatedValuePropagation_8cpp.html).
> - Analysis it consumes: [[lazy-value-info]].
