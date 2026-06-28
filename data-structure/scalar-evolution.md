---
title: Scalar Evolution (SCEV)
facet: data-structure
stage: analysis
ecosystem: [llvm]
concepts: [scalar-evolution, loop-optimization]
src: llvm/lib/Analysis/ScalarEvolution.cpp
docs: "doxygen — ScalarEvolution ↗ https://llvm.org/doxygen/classllvm_1_1ScalarEvolution.html"
book: "Dragon Book (Aho/Lam/Sethi/Ullman, 2e) §9.8"
prereqs: [loop-info]
related: [loop-transformations, loop-info]
tags: [kind/data-structure, status/verified]
status: verified
verified_on: 2026-06-28
---

# Scalar Evolution (SCEV)

> 🧭 **Data structure** · `data-structure · analysis · llvm` · Index [[LLVM.MOC]] · see also [[dragon-book-ch9.MOC|Dragon Ch.9]]
> **Prerequisites:** [[loop-info]] · **Drives:** [[loop-transformations]]

> [!abstract] Chapter map
> SCEV is LLVM's **symbolic analysis** of how scalar values change across loop iterations. It rewrites induction variables and the expressions built on them into closed-form symbolic recurrences, so loop passes can reason about trip counts, strides, and dependences algebraically instead of by simulation.

> [!info] The core representation: add recurrences
> SCEV expresses a loop-varying value as a **chain of recurrences**, written `{start,+,step}<loop>` (an *add recurrence*, AddRec). `{0,+,1}<L>` is "starts at 0, adds 1 each iteration of L" — the canonical induction variable. Building blocks: constants, `SCEVUnknown` (opaque values), `+`/`*`, `min`/`max`, and nested AddRecs (for nested loops).

---

## 1. A worked example

```c
for (int i = 0; i < n; i++)
  a[i] = a[i] + 1;
```
SCEV analyzes the IR and concludes:
- `i` is the add recurrence **`{0,+,1}<loop>`**;
- the address `&a[i]` is **`{a, +, 4}<loop>`** (affine: base `a`, stride 4 bytes for `i32`);
- the **backedge-taken count** is `n - 1` (so the trip count is `n`), letting LLVM know exactly how many times the loop runs.

Because the address is an *affine* AddRec, LLVM knows successive iterations touch `a`, `a+4`, `a+8`, … — contiguous, non-overlapping — which is what makes the loop safe to vectorize.

## 2. What it powers in LLVM

> [!info] Consumers of `ScalarEvolution`
> - **IndVarSimplify** — canonicalize induction variables, widen them, replace exit values with closed forms.
> - **Loop Strength Reduction (LSR)** — rewrite expensive `i*stride` into cheaper pointer increments using the AddRec.
> - **Loop vectorizer / unroller** — need the trip count and proof that memory strides don't overlap.
> - **Dependence analysis** and **`scev-aa`** — compare two affine SCEVs to decide whether `a[i]` and `a[i+1]` can alias.

It builds on [[loop-info|LoopInfo]] (it reasons relative to a specific loop) and is far more precise in [[loop-info#3. Loop closed SSA (LCSSA) --- a canonical form|LCSSA]] form, where each loop-variant value splits into an in-loop value and an exit value.

## 3. Limits

SCEV is strongest on **affine** (linear) recurrences over integers; non-linear evolution, data-dependent bounds, and wrapping/overflow force conservative `SCEVUnknown` results or guard conditions. Overflow reasoning relies on `nsw`/`nuw` flags carried from the front end.

> [!summary] The one thing to remember
> SCEV turns "how does this value change each iteration?" into algebra: induction variables become **add recurrences `{start,+,step}<loop>`**, which give LLVM exact trip counts and strides — the prerequisite for strength reduction, vectorization, and loop dependence analysis.

> [!quote] Further reading
> - **Dragon Book §9.8** — symbolic analysis (induction variables, affine expressions of loop variables).
> - [LLVM `ScalarEvolution`](https://llvm.org/doxygen/classllvm_1_1ScalarEvolution.html); Bachmann, Wang, Zima — *Chains of Recurrences*.
