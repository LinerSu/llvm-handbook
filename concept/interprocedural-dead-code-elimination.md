---
title: Interprocedural Dead-Code Elimination (DAE & GlobalDCE)
facet: concept
stage: optimization
ecosystem: [llvm]
concepts: [interprocedural, dead-code]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/IPO/DeadArgumentElimination.cpp" }
  - { ecosystem: llvm, src: "llvm/lib/Transforms/IPO/GlobalDCE.cpp" }
docs: "Passes — deadargelim/globaldce ↗ https://llvm.org/docs/Passes.html"
book: "Muchnick, Advanced Compiler Design & Implementation §19"
prereqs: [call-graph, dead-code-elimination]
related: [dead-code-elimination, call-graph, ipsccp]
tags: [kind/transform, status/verified]
status: verified
verified_on: 2026-06-28
---

# Interprocedural Dead-Code Elimination (DAE & GlobalDCE)

> 🧭 **Concept** · `concept · optimization · llvm` · Index [[LLVM.MOC]] · see also [[muchnick.MOC|Muchnick]]
> **Prerequisites:** [[call-graph]] · **Module-level cousin of:** [[dead-code-elimination]]

> [!abstract] Chapter map
> [[dead-code-elimination|DCE]] removes dead code *within* a function; these two passes do it **across the module**: **DeadArgumentElimination** drops unused parameters and return values (rewriting every call site), and **GlobalDCE** removes functions and globals that nothing reachable references.

---

## 1. Dead-argument elimination

> [!info] `DeadArgumentElimination`
> For an **internal** function (not externally visible, so all callers are known), if a **parameter is never used** in the body, DAE removes it and updates **all call sites**; likewise it can drop an **unused return value**. This shrinks signatures and exposes more constants to callers (it pairs with [[ipsccp|IPSCCP]] and [[inlining]]).
> ```c
> static int f(int x, int unused) { return x + 1; }   // unused never read
> // → static int f(int x) { return x + 1; }   (call sites rewritten)
> ```

## 2. Global dead-code elimination

> [!info] `GlobalDCE`
> **GlobalDCE** computes reachability over the whole module from its **roots** — exported/external symbols and the `llvm.used` list — and deletes any **function or global variable** that nothing reachable references. It's how unused library functions and dead vtables disappear after inlining and internalization.

> [!summary] The one thing to remember
> Module-scope dead removal: **DAE** strips unused parameters/returns from internal functions (and rewrites callers); **GlobalDCE** deletes functions/globals unreachable from the module roots. Together they're the interprocedural complement to intraprocedural [[dead-code-elimination|DCE]].

> [!quote] Further reading
> - **Source:** [`Transforms/IPO/DeadArgumentElimination.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/IPO/DeadArgumentElimination.cpp) · [`IPO/GlobalDCE.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/IPO/GlobalDCE.cpp)
> - **Muchnick §19** — interprocedural optimization.
