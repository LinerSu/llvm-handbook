---
title: Jump Threading
facet: concept
stage: optimization
ecosystem: [llvm]
concepts: [control-flow]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/Scalar/JumpThreading.cpp" }
docs: "Passes — jump-threading ↗ https://llvm.org/docs/Passes.html"
book: "Muchnick, Advanced Compiler Design & Implementation §18"
prereqs: [control-flow-graph, sparse-conditional-constant-propagation]
related: [simplifycfg, sparse-conditional-constant-propagation, lazy-value-info, correlated-value-propagation]
tags: [kind/transform, status/verified]
status: verified
verified_on: 2026-06-28
---

# Jump Threading

> 🧭 **Concept** · `concept · optimization · llvm` · Index [[LLVM.MOC]] · see also [[muchnick.MOC|Muchnick]]
> **Prerequisites:** [[control-flow-graph]] · **Sibling cleanup:** [[simplifycfg]]

> [!abstract] Chapter map
> When the value that controls a branch is **already determined on a particular incoming path**, jump threading **redirects that path straight to the branch's chosen successor** — bypassing the test entirely. It's the CFG optimization that turns "correlated" branches into straight-line flow.

---

## 1. The idea

> [!example] A correlated branch
> ```text
> B1:  ... ; arrives here only when  x == 0
> B2:  c = (x == 0)
>      br c, label %T, label %F      ; on the edge B1→B2, c is known true
> ```
> The edge **B1 → B2** can be **threaded** directly to `%T`, skipping the redundant test. If `B2` has other predecessors where `x` isn't known, jump threading **duplicates** `B2` onto the threaded edge so the other predecessors are unaffected.

A common form: a `phi` feeds a branch, and one incoming value makes the condition constant — that predecessor's edge is threaded past the branch.

## 2. In LLVM

> [!info] `JumpThreading` + LazyValueInfo
> LLVM's **`JumpThreading`** pass uses **`LazyValueInfo`** (LVI — per-edge value ranges/constants) to discover when a predecessor implies a branch's outcome, then rewrites the CFG (cloning the block as needed). It eliminates correlated conditionals, propagates constants across blocks that [[simplifycfg|SimplifyCFG]] alone can't, and exposes more straight-line code for later passes. The cost it watches is **code duplication**, so it's bounded by a size threshold.

> [!summary] The one thing to remember
> Jump threading **routes an incoming edge past a branch whose result that edge already determines** (duplicating the block if needed), using LazyValueInfo to prove the outcome. It removes correlated branches and propagates facts across the CFG.

> [!quote] Further reading
> - **Source:** [`Transforms/Scalar/JumpThreading.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/JumpThreading.cpp)
> - **Muchnick §18** — control-flow optimizations.
