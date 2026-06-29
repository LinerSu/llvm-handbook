---
title: Loop Unswitching
facet: concept
stage: optimization
ecosystem: [llvm]
concepts: [loop-optimization]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/Scalar/SimpleLoopUnswitch.cpp" }
docs: "Passes — simple-loop-unswitch ↗ https://llvm.org/docs/Passes.html"
book: "Muchnick, Advanced Compiler Design & Implementation §14"
prereqs: [loop-info, loop-transformations]
related: [loop-transformations]
tags: [kind/transform, status/verified]
status: verified
verified_on: 2026-06-28
---

# Loop Unswitching

> 🧭 **Concept** · `concept · optimization · llvm` · Index [[LLVM.MOC]] · see also [[muchnick.MOC|Muchnick]]
> **Prerequisites:** [[loop-info]], [[loop-transformations]] · Chapter: [[Loop-Optimization.MOC]]

> [!abstract] Chapter map
> A branch inside a loop whose condition is **loop-invariant** is re-tested every iteration for no reason. **Unswitching** hoists that branch *out* of the loop by **cloning the loop** — one copy for the condition true, one for false — so the test runs once. The cost is code duplication.

---

## 1. The transform

```c
for (i = 0; i < n; i++) {
  if (inv)  A(i);          // `inv` doesn't change in the loop
  else      B(i);
}
```
becomes
```c
if (inv) { for (i=0;i<n;i++) A(i); }
else     { for (i=0;i<n;i++) B(i); }
```
The invariant branch is evaluated **once** instead of `n` times, and each cloned loop body is now branch-free and independently optimizable (vectorizable, etc.).

## 2. In LLVM

> [!info] `SimpleLoopUnswitch`
> LLVM's **`SimpleLoopUnswitch`** (which replaced the legacy `LoopUnswitch`) handles two forms:
> - **Trivial** — the invariant condition makes the loop exit (or skip) immediately; cheap, no cloning of the body.
> - **Non-trivial** — full duplication of the loop for each value of the condition; gated by a **cost model** because each unswitched condition can *double* code size.
>
> It needs the loop in [[loop-info#3. Loop closed SSA (LCSSA) --- a canonical form|LCSSA]] / simplified form and updates the dominator tree and loop info as it clones.

> [!summary] The one thing to remember
> Unswitching **pulls a loop-invariant branch out of the loop by cloning the loop per branch outcome**, so the test runs once and each clone is branch-free — paid for in code size, so LLVM's `SimpleLoopUnswitch` is cost-model-gated (trivial vs. non-trivial).

> [!quote] Further reading
> - **Source:** [`Transforms/Scalar/SimpleLoopUnswitch.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/SimpleLoopUnswitch.cpp)
> - **Muchnick §14** — loop optimizations.
