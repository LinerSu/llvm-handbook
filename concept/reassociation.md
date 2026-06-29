---
title: Reassociation
facet: concept
stage: optimization
ecosystem: [llvm]
concepts: [canonicalization]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/Scalar/Reassociate.cpp" }
docs: "Passes — reassociate ↗ https://llvm.org/docs/Passes.html"
book: "Muchnick, Advanced Compiler Design & Implementation §12.3"
prereqs: [three-address-code]
related: [value-numbering, instruction-combining, loop-transformations]
tags: [kind/transform, status/verified]
status: verified
verified_on: 2026-06-28
---

# Reassociation

> 🧭 **Concept** · `concept · optimization · llvm` · Index [[LLVM.MOC]] · see also [[muchnick.MOC|Muchnick]]
> **Prerequisites:** [[three-address-code]] · **Enables:** [[value-numbering]], LICM in [[loop-transformations]]

> [!abstract] Chapter map
> Associative/commutative operators (`+`, `*`, `&`, `|`, `^`) can be grouped many ways. **Reassociation** rewrites such expressions into a **canonical order** so equivalent computations become syntactically identical — which is what lets [[value-numbering|CSE/GVN]], constant folding, and LICM actually fire. It's an *enabling* canonicalization, not a win by itself.

---

## 1. What it does

LLVM's **`Reassociate`** pass assigns each operand a **rank** (by definition order / loop depth) and reorders commutative-associative chains into a consistent shape, also pushing constants together.

> [!example] Two payoffs
> **Expose common subexpressions:** these compute the same value but look different —
> ```text
> t1 = (a + b) + c
> t2 = (b + c) + a     ; same value, different grouping
> ```
> reassociation canonicalizes both to e.g. `a + b + c`, so [[value-numbering|GVN]] can prove `t1 == t2` and delete one.
>
> **Gather constants for folding:**
> ```text
> x = a + 2 + b + 3     →     x = a + b + 5
> ```

## 2. Why it helps loops

> [!tip] Reassociation feeds LICM
> By regrouping a chain so the **loop-invariant operands sit together**, reassociation lets LICM hoist that sub-expression out of the loop. e.g. `(inv1 + i) + inv2` → `(inv1 + inv2) + i`, and `inv1 + inv2` hoists. Without reassociation the invariant part is "trapped" mid-chain.

> [!summary] The one thing to remember
> Reassociation **canonicalizes commutative/associative expression trees** (rank-ordered operands, constants grouped) so that CSE/GVN, constant folding, and LICM can recognize and exploit equivalences. It's a setup pass — its value is what it *enables*.

> [!quote] Further reading
> - **Source:** [`Transforms/Scalar/Reassociate.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/Reassociate.cpp)
> - **Muchnick §12.3** — algebraic simplifications and reassociation.
