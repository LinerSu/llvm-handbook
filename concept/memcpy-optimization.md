---
title: MemCpy Optimization (MemCpyOpt)
facet: concept
stage: optimization
ecosystem: [general, llvm]
concepts: [memory-optimization]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/Scalar/MemCpyOptimizer.cpp" }
data_structures: [memory-ssa]
src: "llvm/lib/Transforms/Scalar/MemCpyOptimizer.cpp"
docs: "MemCpyOptimizer doxygen ↗ https://llvm.org/doxygen/MemCpyOptimizer_8h_source.html"
prereqs: [memory-ssa]
related: [memory-ssa, dead-store-elimination, pointer-alias-analysis]
tags: [kind/transform, status/verified]
status: verified
verified_on: 2026-06-28
sources:
  - "https://llvm.org/doxygen/MemCpyOptimizer_8h_source.html"
  - "https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/MemCpyOptimizer.cpp"
---

# MemCpy Optimization (MemCpyOpt)

> 🧭 **Concept** · `concept · optimization · general+llvm` · Index [[LLVM.MOC]]
> **Prerequisites:** [[memory-ssa]] · **Memory-cleanup pair:** [[dead-store-elimination]] · **Uses:** [[pointer-alias-analysis]]

> [!abstract] Chapter map
> **MemCpyOpt** optimizes bulk memory intrinsics — `llvm.memcpy` / `llvm.memmove` / `llvm.memset` — by removing, shortening, or fusing them. Its signature trick is **call-slot optimization**: when a value is produced into a temporary and immediately copied elsewhere, write it to the destination directly and delete the copy.

> [!info]+ Patterns MemCpyOpt rewrites
> | Pattern | Rewrite |
> |---|---|
> | `tmp = produce(); memcpy(dst, tmp)` | **call-slot opt**: produce straight into `dst`, drop the copy |
> | `memcpy(b, a); memcpy(c, b)` | **copy-of-copy**: `memcpy(c, a)` when `b` is otherwise dead |
> | sequence of stores of the same byte | fuse into a single **`memset`** |
> | `memcpy` from a `memset`-filled buffer | turn the `memcpy` into a `memset` |

---

## 1. What it does

> [!note] Make bulk copies cheaper or disappear
> Front ends and earlier passes leave behind redundant `memcpy`/`memset` traffic (struct returns, pass-by-value, initialization). MemCpyOpt recognizes the patterns above and either eliminates the intermediate buffer (call-slot optimization), collapses chained copies, or rewrites store sequences into a single intrinsic. It reasons about clobbering via [[memory-ssa|MemorySSA]] + [[pointer-alias-analysis|alias analysis]].

## 2. Worked example

> [!example]+ Call-slot optimization
> ```llvm
> ; before: build into a temp, then copy to the real destination
> %tmp = alloca %S
> call void @make(ptr %tmp)
> call void @llvm.memcpy(ptr %dst, ptr %tmp, i64 sizeof_S, i1 false)
> ; after: have @make write %dst directly; the alloca + memcpy go away
> call void @make(ptr %dst)
> ```

## 3. In LLVM

> [!info] Where it lives
> [`Transforms/Scalar/MemCpyOptimizer.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/MemCpyOptimizer.cpp). It is **MemorySSA-based** and runs in the `-O2`/`-O3` scalar pipeline, complementing [[dead-store-elimination|DSE]] (which removes the dead writes MemCpyOpt's rewrites can expose). Legality hinges on alias/size facts: the source must be unmodified between the producing op and the copy.

> [!summary] The one thing to remember
> MemCpyOpt rewrites bulk `memcpy`/`memmove`/`memset`: **call-slot optimization** (produce into the destination), copy-of-copy elimination, and store→`memset` fusion — all gated by [[memory-ssa|MemorySSA]] + alias analysis.

> [!quote] Sources & confidence
> - **Source:** [`Transforms/Scalar/MemCpyOptimizer.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/MemCpyOptimizer.cpp) — tier-1.
> - [MemCpyOptimizer header (doxygen)](https://llvm.org/doxygen/MemCpyOptimizer_8h_source.html).
