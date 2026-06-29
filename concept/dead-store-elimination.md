---
title: Dead Store Elimination (DSE)
facet: concept
stage: optimization
ecosystem: [general, llvm]
concepts: [dead-code, memory-optimization]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/Scalar/DeadStoreElimination.cpp" }
data_structures: [memory-ssa]
src: "llvm/lib/Transforms/Scalar/DeadStoreElimination.cpp"
docs: "DeadStoreElimination doxygen ↗ https://llvm.org/doxygen/DeadStoreElimination_8cpp.html"
prereqs: [memory-ssa]
related: [memory-ssa, dead-code-elimination, pointer-alias-analysis, memcpy-optimization]
tags: [kind/transform, status/verified]
status: verified
verified_on: 2026-06-28
sources:
  - "https://llvm.org/doxygen/DeadStoreElimination_8cpp.html"
  - "https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/DeadStoreElimination.cpp"
---

# Dead Store Elimination (DSE)

> 🧭 **Concept** · `concept · optimization · general+llvm` · Index [[LLVM.MOC]]
> **Prerequisites:** [[memory-ssa]] · **Memory-DCE pair:** [[dead-code-elimination]] · **Uses:** [[pointer-alias-analysis]]

> [!abstract] Chapter map
> **DSE** removes **stores whose value is never read** before being overwritten (or before the memory dies). It is [[dead-code-elimination|DCE]] for memory: where DCE deletes SSA values with no uses, DSE deletes writes with no observers, reasoning about memory through [[memory-ssa|MemorySSA]].

> [!info]+ Classic DSE → LLVM
> | Classic | LLVM realization |
> |---|---|
> | A store is dead if overwritten before any read | walk **[[memory-ssa|MemorySSA]]** def chains to find the killing store |
> | Liveness of memory locations | MemorySSA + [[pointer-alias-analysis|alias analysis]] (must-alias to kill) |
> | Whole-store kill | also **partial** overwrites when sizes/offsets are known |
> | — | removes stores dead at function end / to dying `alloca`s |

---

## 1. What it does

> [!note] Kill overwritten writes
> A store `S1` to location `L` is dead if there is a later store `S2` that **must-overwrites** the same bytes of `L` with **no intervening read** of those bytes. DSE finds `S2` by walking MemorySSA backward from later defs, checks aliasing/size, and erases `S1`. It also drops stores that are dead because the memory does not outlive the function (e.g. a store to an `alloca` never read).

## 2. Worked example

> [!example]+ The first store is dead
> ```llvm
> store i32 1, ptr %p     ; dead: overwritten below, never read in between
> store i32 2, ptr %p
> %v = load i32, ptr %p   ; reads 2
> ```
> DSE deletes `store i32 1, ptr %p`.

## 3. In LLVM

> [!info] Where it lives
> [`Transforms/Scalar/DeadStoreElimination.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/DeadStoreElimination.cpp). The modern implementation is **MemorySSA-based** (replacing the old MemDep version), which lets it kill stores across basic blocks, handle partial overwrites, and shorten `memset`/`memcpy` ranges. Precision is bounded by [[pointer-alias-analysis|alias analysis]]: a may-alias read keeps the store.

> [!summary] The one thing to remember
> DSE = DCE for memory: delete a store that is **must-overwritten with no intervening read**, found by walking [[memory-ssa|MemorySSA]] and gated by [[pointer-alias-analysis|alias analysis]].

> [!quote] Sources & confidence
> - **Source:** [`Transforms/Scalar/DeadStoreElimination.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/DeadStoreElimination.cpp) — tier-1.
> - [DeadStoreElimination doxygen](https://llvm.org/doxygen/DeadStoreElimination_8cpp.html) · [MemorySSA docs](https://llvm.org/docs/MemorySSA.html).
