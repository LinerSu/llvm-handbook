---
title: Scalar Replacement of Aggregates (SROA)
facet: concept
stage: optimization
ecosystem: [llvm]
concepts: [ssa, memory-optimization]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/Scalar/SROA.cpp" }
docs: "Passes — sroa ↗ https://llvm.org/docs/Passes.html"
book: "Muchnick, Advanced Compiler Design & Implementation §12.2"
prereqs: [ssa-form, three-address-code]
related: [ssa-form, inlining, mem2reg]
tags: [kind/transform, status/verified]
status: verified
verified_on: 2026-06-28
---

# Scalar Replacement of Aggregates (SROA)

> 🧭 **Concept** · `concept · optimization · llvm` · Index [[LLVM.MOC]] · see also [[muchnick.MOC|Muchnick]]
> **Prerequisites:** [[ssa-form]], [[three-address-code]] · **Enables:** [[mem2reg]] promotion

> [!abstract] Chapter map
> Front ends emit local **structs and arrays** as a single `alloca` with loads/stores to fields — and memory blocks SSA optimization. **SROA** splits that aggregate into independent scalar pieces (or pure SSA values) so [[ssa-form|mem2reg]] can promote them to registers, erasing the memory traffic. It's one of LLVM's highest-impact early passes, especially right after [[inlining]].

---

## 1. The problem

```c
struct P { int x, y; };
int f(int a) { struct P p; p.x = a; p.y = a + 1; return p.x + p.y; }
```
The front end gives `p` one stack slot and stores/loads its fields — `mem2reg` alone can't promote it because it's accessed field-by-field, not as one scalar:
```llvm
%p = alloca %struct.P
%px = getelementptr %struct.P, ptr %p, i32 0, i32 0
store i32 %a, ptr %px
; ... store y, load x, load y ...
```

## 2. What SROA does

> [!info] Split, then promote
> SROA analyzes the uses of the `alloca`. If the aggregate is only accessed through distinct, non-overlapping fields/elements, it **replaces the one aggregate slot with separate scalar slots** (scalar *replacement*), or rewrites the accesses **directly to SSA values**. `mem2reg`-style promotion then takes over. After SROA the example becomes pure SSA — no `alloca`, no memory:
> ```llvm
> %sum = add i32 %a, %a.plus1   ; p.x and p.y are now SSA values
> ```
> It also copes with the messy cases front ends produce: partial/overlapping accesses, `memcpy`/`memset` of the aggregate, and casts — splitting where it can and leaving the rest in memory.

## 3. Relationship to mem2reg

> [!note] SROA ⊃ mem2reg
> `mem2reg` promotes an `alloca` only when it's loaded/stored as a **whole scalar**. **SROA is the stronger pass**: it first *decomposes aggregates and partial accesses* into scalar pieces, then promotes them. In the modern pipeline SROA largely subsumes mem2reg for real code.

## 4. Why it matters

> [!tip] The inlining multiplier
> When a callee that passes/returns a `struct` by value is [[inlining|inlined]], the copy becomes a local aggregate `alloca` in the caller. SROA + promotion turn that into registers — which is why inlining followed by SROA unlocks so much downstream constant propagation and [[value-numbering|CSE]].

> [!summary] The one thing to remember
> SROA **breaks aggregate `alloca`s into scalars and promotes them to SSA registers**, removing struct/array memory traffic that would otherwise block every scalar optimization. It's mem2reg's more powerful sibling and a top payoff after inlining.

> [!quote] Further reading
> - **Source:** [`Transforms/Scalar/SROA.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/SROA.cpp)
> - **Muchnick §12.2** — scalar replacement of aggregates.
