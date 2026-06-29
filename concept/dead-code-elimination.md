---
title: Dead-Code Elimination (DCE / ADCE / BDCE)
facet: concept
stage: optimization
ecosystem: [general, llvm]
concepts: [dead-code]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/Scalar/ADCE.cpp" }
  - { ecosystem: llvm, src: "llvm/lib/Transforms/Scalar/BDCE.cpp / DCE.cpp" }
docs: "Passes — adce/bdce/dce ↗ https://llvm.org/docs/Passes.html"
book: "Muchnick, Advanced Compiler Design & Implementation §18"
prereqs: [ssa-form, data-flow-analysis]
related: [data-flow-analysis, control-flow-graph]
tags: [kind/transform, status/verified]
status: verified
verified_on: 2026-06-28
---

# Dead-Code Elimination (DCE / ADCE / BDCE)

> 🧭 **Concept** · `concept · optimization · general+llvm` · Index [[LLVM.MOC]] · see also [[muchnick.MOC|Muchnick]]
> **Prerequisites:** [[ssa-form]], [[data-flow-analysis]] · **Cleans up after:** most other passes

> [!abstract] Chapter map
> Remove computations whose results are never used (and the control flow that only feeds them). LLVM ships three strengths: **DCE** (trivial), **ADCE** (aggressive — control-dependence-based, can delete dead branches/loops), and **BDCE** (bit-tracking — removes work whose result *bits* are all unused).

---

## 1. Trivial DCE

An instruction with **no uses** and **no side effects** is dead — delete it, and iterate (deleting one can make its operands dead). [[ssa-form|SSA]] makes this immediate: every value carries its use list, so "no uses" is a direct check.
```llvm
%t = add i32 %a, %b   ; %t never used, no side effects  → deleted
```

## 2. ADCE — aggressive (optimistic)

> [!info] Assume dead until proven live
> Trivial DCE is *pessimistic* (keeps anything reachable). **ADCE** flips it: mark everything dead, then mark **live** only what has side effects (stores, calls, returns) and, transitively, whatever feeds a live instruction — using **control dependence** so it can also delete a **branch (or whole loop)** that only controls dead code. Anything still unmarked is removed.

## 3. BDCE — bit-tracking

> [!info] Demanded bits
> **BDCE** uses **demanded-bits** analysis: if *no* use needs *any* bit of an instruction's result, the instruction is dead even though it technically has a use (e.g. a computation whose high bits are immediately masked off). It removes such instructions and simplifies operands whose upper bits don't matter.

> [!summary] The one thing to remember
> Dead code = results (or bits, or branches) that can't affect output. LLVM: **DCE** (no-use, no-side-effect), **ADCE** (optimistic + control-dependence, kills dead branches/loops), **BDCE** (demanded-bits). SSA use lists make the liveness check cheap; DCE runs constantly to clean up after other passes. Module-scope cleanup: [[interprocedural-dead-code-elimination]].

> [!quote] Further reading
> - **Source:** [`Transforms/Scalar/ADCE.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/ADCE.cpp) · [`BDCE.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/BDCE.cpp) · [`DCE.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/DCE.cpp)
> - **Muchnick §18** — dead-code elimination; **Dragon §9.1**.
