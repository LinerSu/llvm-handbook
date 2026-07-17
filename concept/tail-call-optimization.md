---
title: Tail-Call & Tail-Recursion Optimization
facet: concept
stage: optimization
ecosystem: [llvm]
concepts: [tail-call, interprocedural]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/Scalar/TailRecursionElimination.cpp" }
docs: "LangRef — call/musttail ↗ https://llvm.org/docs/LangRef.html#call-instruction"
book: "Muchnick, Advanced Compiler Design & Implementation §15.1"
prereqs: [three-address-code]
related: [inlining, loop-transformations]
tags: [kind/transform, status/unverified]
status: unverified
verified_on: ""
---

# Tail-Call & Tail-Recursion Optimization

> 🧭 **Concept** · `concept · optimization · llvm` · Index [[LLVM.MOC]] · see also [[muchnick.MOC|Muchnick]]
> **Prerequisites:** [[three-address-code]] · **Cousin of:** [[inlining]]

> [!abstract] Chapter map
> A **tail call** is the last action a function takes — so its caller's stack frame is no longer needed and can be **reused**, turning unbounded call chains into constant stack space. LLVM handles the recursive case in the middle end (turn it into a **loop**) and the general case in the back end (**reuse the frame**, gated by the `tail`/`musttail` markers).

---

## 1. Tail recursion → loop

> [!info] `TailCallElim`
> When a function calls **itself** in tail position, LLVM's **`TailRecursionElimination`** pass rewrites the recursion as a **loop** in the same function — no new frames, no stack-overflow risk, and the loop is then open to [[loop-transformations|loop optimizations]].

> [!example] Accumulator factorial
> ```c
> int fact(int n, int acc) { return n <= 1 ? acc : fact(n-1, n*acc); }  // tail-recursive
> ```
> becomes, in effect:
> ```c
> int fact(int n, int acc) { while (n > 1) { acc = n*acc; n = n-1; } return acc; }
> ```

## 2. General tail calls → frame reuse

> [!info] `tail` / `musttail`
> For a non-recursive tail call, the back end can perform a **sibling-call optimization**: jump to the callee reusing the caller's frame instead of pushing a new one. LLVM IR marks the opportunity on the `call`:
> - **`tail`** — a hint that TCO is allowed (the optimizer/codegen may take it).
> - **`musttail`** — a *guarantee*: the call **must** be tail-call-optimized (required by guaranteed-TCO languages and by perfect forwarding); the verifier enforces the calling-convention/signature constraints.

## 3. Why it matters

Beyond avoiding stack overflow for deep recursion, TCO makes recursive and continuation-passing styles as cheap as loops — important for functional front ends (Swift, Rust async lowering, ML-style code) targeting LLVM.

> [!summary] The one thing to remember
> Tail position ⇒ the caller's frame is dead ⇒ reuse it. LLVM turns **tail self-recursion into a loop** (`TailCallElim`) and reuses the frame for **general tail calls** in codegen, with `tail` (allowed) and `musttail` (guaranteed) on the IR `call`.

> [!quote] Further reading
> - **Source:** [`Transforms/Scalar/TailRecursionElimination.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/TailRecursionElimination.cpp)
> - **Muchnick §15.1** — tail-call optimization and tail-recursion elimination; [LangRef — `musttail`](https://llvm.org/docs/LangRef.html#call-instruction).
