---
title: Inlining
facet: concept
stage: optimization
ecosystem: [llvm]
concepts: [inlining, interprocedural]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/IPO/Inliner.cpp; llvm/lib/Analysis/InlineCost.cpp" }
docs: "doxygen — Inliner ↗ https://llvm.org/doxygen/Inliner_8h_source.html"
book: "Dragon Book (Aho/Lam/Sethi/Ullman, 2e) §12.2"
prereqs: [call-graph]
related: [call-graph, value-numbering]
tags: [kind/transform, status/verified]
status: verified
verified_on: 2026-06-28
---

# Inlining

> 🧭 **Concept** · `concept · optimization · llvm` · Index [[LLVM.MOC]] · see also [[dragon-book-ch12.MOC|Dragon Ch.12]]
> **Prerequisites:** [[call-graph]] · **Why interprocedural matters:** it's the flagship IPO

> [!abstract] Chapter map
> Inlining replaces a call with a copy of the callee's body. Its real value isn't just removing call overhead — it's **exposing the callee's code to the caller's context**, which unlocks constant propagation, [[value-numbering|CSE]], and dead-code elimination across what used to be a call boundary. In LLVM it's a **bottom-up CGSCC pass** governed by a cost model.

---

## 1. What and why

> [!example] The real win is the follow-on optimization
> ```c
> int square(int x) { return x * x; }
> int f()          { return square(3); }
> ```
> Inlining `square` into `f` gives `return 3 * 3;` — and *then* constant folding makes it `return 9;`. The call overhead is gone, but the bigger payoff is that the callee's body is now optimized **in the caller's context**.

## 2. In LLVM — a bottom-up CGSCC pass

> [!info] How the Inliner runs
> The Inliner is a **CGSCC pass**: it walks the [[call-graph]]'s SCCs **bottom-up** (post-order), so each callee has already been simplified before its callers are considered. After inlining a call, the callee's own call sites are added to a worklist and reconsidered, interleaved with the per-function simplification pipeline — a process of gradual refinement over the call graph.

## 3. The decision: legality, then cost

> [!info] Two steps
> 1. **Legality + mandatory.** Some calls can't be inlined (varargs mismatches, incompatible attributes); some are forced by `alwaysinline` or forbidden by `noinline`.
> 2. **Profitability** (only if legal and non-mandatory) — the **`InlineCost`** heuristic. It estimates the cost of the inlined body against a **threshold** (raised at `-O3`/for hot calls, lowered for size with `-Os`/`-Oz`), with **bonuses** for simplifications the inline would enable (e.g. a constant argument that folds away branches) and for **single-call-site / `internal`** callees (inlining then deletes the original).

## 4. Limitations

Inlining trades **code size and compile time** for speed, so the threshold matters; over-inlining bloats I-cache and slows builds. It can't inline through an **unresolved indirect/virtual call** without [devirtualization] first, and recursive SCCs are inlined only to a bounded depth.

> [!summary] The one thing to remember
> Inlining = paste the callee into the caller, mainly to **expose it to the caller's context** for further optimization. LLVM does it **bottom-up over call-graph SCCs**, deciding per call site by **legality → mandatory → `InlineCost` vs threshold**.

> [!quote] Further reading
> - **Also in:** Muchnick *Advanced Compiler Design & Impl.* §15 — procedure integration / in-line expansion.
> - **Source:** [`Transforms/IPO/Inliner.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/IPO/Inliner.cpp) · cost in [`Analysis/InlineCost.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Analysis/InlineCost.cpp)
> - **Dragon Book §12.2** — why interprocedural analysis (inlining as the motivating transform).
> - [LLVM `Inliner`](https://llvm.org/doxygen/Inliner_8h_source.html); `InlineCost.cpp`; the CGSCC pass manager ([[call-graph]]).
