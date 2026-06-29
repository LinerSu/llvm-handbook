---
title: Interprocedural SCCP (IPSCCP)
facet: concept
stage: optimization
ecosystem: [llvm]
concepts: [interprocedural, constant-propagation]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/IPO/SCCP.cpp" }
docs: "Passes — ipsccp ↗ https://llvm.org/docs/Passes.html"
book: "Muchnick, Advanced Compiler Design & Implementation §19"
prereqs: [sparse-conditional-constant-propagation, call-graph]
related: [sparse-conditional-constant-propagation, function-specialization, dead-code-elimination]
tags: [kind/transform, status/verified]
status: verified
verified_on: 2026-06-28
---

# Interprocedural SCCP (IPSCCP)

> 🧭 **Concept** · `concept · optimization · llvm` · Index [[LLVM.MOC]] · see also [[muchnick.MOC|Muchnick]]
> **Prerequisites:** [[sparse-conditional-constant-propagation]], [[call-graph]] · **Feeds:** [[function-specialization]]

> [!abstract] Chapter map
> IPSCCP runs the [[sparse-conditional-constant-propagation|SCCP]] lattice **across function boundaries**: it propagates **constant arguments** into callees and **constant return values** back to callers, while pruning unreachable blocks and functions — a whole-module, optimistic constant-propagation + dead-code pass.

---

## 1. What it adds over SCCP

> [!info] Crossing the call boundary
> Plain SCCP is per-function: a function's parameters are unknown (overdefined) on entry. **IPSCCP** examines **all call sites** of a (non-externally-visible) function: if a parameter is the **same constant at every call**, it's constant inside the callee; if a function **always returns the same constant**, that constant flows back to every caller. It also marks functions that are never called as dead.

> [!example]
> ```c
> static int scale(int x, int k) { return x * k; }
> int a() { return scale(p, 4); }
> int b() { return scale(q, 4); }   // k is always 4
> ```
> IPSCCP proves `k == 4` inside `scale`, folding `x * 4`; combined with [[inlining]] and [[dead-code-elimination|DCE]] the dead parameter is then removed.

## 2. In LLVM

The **`IPSCCP`** pass (`Transforms/IPO/SCCP.cpp`) reuses the SCCP solver interprocedurally and runs **early** in the module pipeline. It's optimistic (assume dead/constant until proven otherwise) and cooperates with **dead-argument elimination** and [[function-specialization]] — which uses IPSCCP's results to decide when cloning a function for a constant argument pays off.

> [!summary] The one thing to remember
> IPSCCP = SCCP across calls: constant **arguments in**, constant **returns out**, dead functions removed — whole-module and optimistic. It sets up inlining, dead-arg elimination, and function specialization.

> [!quote] Further reading
> - **Source:** [`Transforms/IPO/SCCP.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/IPO/SCCP.cpp)
> - **Muchnick §19** — interprocedural constant propagation.
