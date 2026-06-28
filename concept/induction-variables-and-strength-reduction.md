---
title: Induction Variables & Strength Reduction
facet: concept
stage: optimization
ecosystem: [general, llvm]
concepts: [loop-optimization, induction-variables, strength-reduction]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/Scalar/IndVarSimplify.cpp" }
  - { ecosystem: llvm, src: "llvm/lib/Transforms/Scalar/LoopStrengthReduce.cpp" }
docs: "doxygen — IndVarSimplify ↗ https://llvm.org/doxygen/IndVarSimplify_8cpp.html"
book: "Muchnick, Advanced Compiler Design & Implementation §14"
prereqs: [scalar-evolution, loop-info]
related: [scalar-evolution, loop-transformations]
tags: [kind/transform, status/verified]
status: verified
verified_on: 2026-06-28
---

# Induction Variables & Strength Reduction

> 🧭 **Concept** · `concept · optimization · general+llvm` · Index [[LLVM.MOC]] · see also [[muchnick.MOC|Muchnick]]
> **Prerequisites:** [[scalar-evolution]], [[loop-info]] · **Builds on:** the SCEV add-recurrence

> [!abstract] Chapter map
> An **induction variable** changes by a fixed amount each iteration. **Strength reduction** replaces an *expensive* value derived from an IV (a multiply, an address `base + i·w`) with a *cheap* one maintained incrementally (an add). LLVM does this in two cooperating passes: **IndVarSimplify** (canonicalize IVs via [[scalar-evolution|SCEV]]) and **LoopStrengthReduce (LSR)**.

> [!info] The two ideas
> - **Induction variable (IV)** — a value whose SCEV is an add-recurrence `{start,+,step}<loop>` (basic IV `i`; *derived* IV like `i·4` or `a + i·4`).
> - **Strength reduction** — maintain a derived IV by **adding its step** each iteration instead of recomputing it: `t = a + i·4` becomes `t += 4`.
> - **Linear-function test replacement (LFTR)** — rewrite the loop's exit test to use the new IV so the original one becomes dead.

---

## 1. Worked example

```c
for (i = 0; i < n; i++)
  sum += a[i];          // address of a[i] is  a + i*4   (i32 elements)
```
The address `a + i*4` is the SCEV `{a,+,4}<loop>`. Strength reduction keeps a running pointer instead of multiplying every iteration:
```c
p = a;
for (i = 0; i < n; i++) { sum += *p; p += 4; }   // multiply → add
```

## 2. In LLVM — IndVarSimplify then LSR

> [!info] A two-pass division of labor
> - **`IndVarSimplify`** uses SCEV to **canonicalize** induction variables: unify them to one canonical IV, **expose the trip count**, **widen** narrow IVs to the native width, and **rewrite exit values** to closed forms. It *prepares* loops — e.g. turning `for (i=0;i<n;i+=2) … p[i]` into a unit-stride `for (i=0;i!=n;++i) … p[i*2]`.
> - **`LoopStrengthReduce` (LSR)** then **strength-reduces** the SCEV expressions — replacing the `i*2`/`base + i·w` computations with minimal-cost IVs and **targeting the machine's addressing modes** (so `a[i]` becomes a single incremented pointer/scaled-index).

> [!warning] Why they're paired
> IndVarSimplify's canonicalization can *introduce* a multiply (the `p[i*2]` above) and is a **pessimization on its own** — it relies on **LSR running afterward** to clean it up. Treat them as one IV-optimization stage, not two independent passes.

## 3. Why it matters

Loop bodies are where programs spend their time; turning per-iteration multiplies and address computations into single adds is one of the highest-leverage classical optimizations. It also feeds the back end: LSR shapes IVs to fit addressing modes ([[code-generation-overview]]), reducing instruction count in the hot loop.

> [!summary] The one thing to remember
> Recognize induction variables (SCEV add-recurrences), then **trade expensive per-iteration work for cheap increments**. LLVM splits it: **IndVarSimplify** canonicalizes IVs (and exposes trip counts), **LSR** strength-reduces them into addressing-mode-friendly increments — and the two are designed to run together.

> [!quote] Further reading
> - **Source:** [`Transforms/Scalar/IndVarSimplify.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/IndVarSimplify.cpp) · [`Transforms/Scalar/LoopStrengthReduce.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/LoopStrengthReduce.cpp)
> - **Muchnick, *Advanced Compiler Design & Implementation* §14** — induction-variable optimizations, strength reduction, linear-function test replacement.
> - **Dragon Book §9.1** — strength reduction among the principal sources of optimization.
