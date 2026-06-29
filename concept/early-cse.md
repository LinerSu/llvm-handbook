---
title: Early CSE (EarlyCSE)
facet: concept
stage: optimization
ecosystem: [general, llvm]
concepts: [redundancy-elimination, value-numbering]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/Scalar/EarlyCSE.cpp" }
data_structures: [dominator-tree, memory-ssa]
src: "llvm/lib/Transforms/Scalar/EarlyCSE.cpp"
docs: "Passes — early-cse ↗ https://llvm.org/docs/Passes.html"
prereqs: [value-numbering, dominator-tree]
related: [value-numbering, llvm-gvn, memory-ssa]
tags: [kind/transform, status/verified]
status: verified
verified_on: 2026-06-28
sources:
  - "https://llvm.org/doxygen/EarlyCSE_8cpp.html"
  - "https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/EarlyCSE.cpp"
---

# Early CSE (EarlyCSE)

> 🧭 **Concept** · `concept · optimization · general+llvm` · Index [[LLVM.MOC]]
> **Prerequisites:** [[value-numbering]], [[dominator-tree]] · **Heavyweight cousin:** [[llvm-gvn]] · **Uses:** [[memory-ssa]]

> [!abstract] Chapter map
> **EarlyCSE** is the **cheap, local** redundancy eliminator: a single dominator-tree walk with a **scoped hash table** that removes trivially redundant instructions (and, with [[memory-ssa|MemorySSA]], redundant loads and dead stores). It runs early and at low opt levels to clean up before the expensive passes — the fast counterpart to the whole-function [[llvm-gvn|GVN]].

> [!info]+ Where it sits between LVN and GVN
> | | [[value-numbering|Local VN]] | **EarlyCSE** | [[llvm-gvn|GVN]] |
> |---|---|---|---|
> | Scope | one block | dominator subtree (scoped) | whole function |
> | Cost | cheap | cheap | expensive |
> | Memory ops | no | yes (via MemorySSA) | yes (MemDep, load PRE) |
> | When | — | early, `-O1+` | `-O2+` |

---

## 1. What it does

> [!note] Scoped-hash CSE
> EarlyCSE performs a **dominator-tree DFS**, keeping a **scoped hash table** of available expressions: enter a block → push a scope; leave → pop. An instruction whose key `(opcode, operands, type)` is already available is replaced by the existing value. It also folds simple constants and drops trivially dead instructions in the same pass.

## 2. Memory CSE

> [!info] The MemorySSA variant
> The `EarlyCSEMemSSA` variant uses [[memory-ssa|MemorySSA]] to also eliminate **redundant loads** (same address, no intervening clobber) and **simple dead stores** — cheap memory cleanups that don't need GVN's full load-PRE machinery.

## 3. Worked example

> [!example]+ Trivial redundancy gone in one walk
> ```llvm
> %a = add i32 %x, %y
> %b = add i32 %x, %y     ; same key -> replaced by %a
> %p = load i32, ptr %q
> %r = load i32, ptr %q   ; no clobber between -> replaced by %p
> ```

## 4. In LLVM

> [!info] Where it lives
> [`Transforms/Scalar/EarlyCSE.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/EarlyCSE.cpp). Runs multiple times in the pipeline (very early, and again after inlining), at `-O1+`. Think of it as the broom that sweeps obvious redundancy so [[instruction-combining|InstCombine]] and [[llvm-gvn|GVN]] spend their budget on the hard cases.

> [!summary] The one thing to remember
> EarlyCSE = cheap CSE via a **scoped hash table over the dominator tree** (+ MemorySSA for redundant loads / dead stores). Fast and local; it pre-cleans for the expensive [[llvm-gvn|GVN]].

> [!quote] Sources & confidence
> - **Source:** [`Transforms/Scalar/EarlyCSE.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/EarlyCSE.cpp) — tier-1.
> - [LLVM Passes — `early-cse`](https://llvm.org/docs/Passes.html).
