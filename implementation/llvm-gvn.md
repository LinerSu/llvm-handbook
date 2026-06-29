---
title: LLVM GVN (the pass)
facet: implementation
stage: optimization
ecosystem: [llvm]
concepts: [redundancy-elimination, value-numbering, partial-redundancy]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/Scalar/GVN.cpp" }
data_structures: [dominator-tree, memory-ssa]
src: "llvm/lib/Transforms/Scalar/GVN.cpp"
docs: "GVNPass class ↗ https://llvm.org/doxygen/classllvm_1_1GVNPass.html"
prereqs: [value-numbering, ssa-form]
related: [value-numbering, partial-redundancy-elimination, dominator-tree, memory-ssa]
tags: [kind/pass, status/draft, version-sensitive]
status: draft
verified_on: 2026-06-28
sources:
  - "https://llvm.org/doxygen/classllvm_1_1GVNPass.html"
  - "https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/GVN.cpp"
---

# LLVM GVN (the pass)

> 🧭 **Implementation** · `implementation · optimization · llvm` · Index [[LLVM.MOC]] · v [[llvm-version]]
> **Realizes:** [[value-numbering]] + [[partial-redundancy-elimination]] · **Prerequisites:** [[value-numbering]], [[ssa-form]] · **Consumes:** [[dominator-tree]], [[memory-ssa]]

> [!abstract] What this note adds
> The concept notes teach the *ideas* — value numbering and partial redundancy. This note documents the **single LLVM pass that realizes both of them at once**: `GVNPass` in `GVN.cpp`. Here live the engineering specifics — the class layout, where it sits in the pipeline, the load-PRE guards, the `cl::opt` knobs, and how the production pass deviates from the textbook DVNT algorithm.

---

## 1. The pass

`GVN` is LLVM's production global-value-numbering + redundancy-elimination pass. Entry point: class **`GVNPass`** in [`llvm/lib/Transforms/Scalar/GVN.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/GVN.cpp) (new-PM `run()`; legacy wrapper `GVNLegacyPass`). It is the heavyweight CSE in the middle end — the concrete realization of [[value-numbering]].

## 2. What it realizes (and why this note exists)

This is the promotion case from the blueprint: **one pass implements two concept notes.**

- [[value-numbering]] — global CSE: number expressions by `(opcode, operand value-numbers, type)` and replace re-computations with a reuse.
- [[partial-redundancy-elimination]] — **load PRE**: insert a load on the predecessor edges that lack it so the merge's load becomes fully redundant, then delete it.

Keeping the LLVM mechanics for *both* in their separate concept notes would duplicate the same pass twice; promoting them here gives one authoritative "how the real pass works" note that both concepts link to.

## 3. Where it runs

GVN is scheduled in the **function simplification pipeline at `-O2`/`-O3`** (not `-O1`). The cheap, local cousin **EarlyCSE** runs much earlier and at lower opt levels; GVN is the expensive whole-function pass that runs after the IR is already in SSA and cleaned up — i.e. after `mem2reg`/[[scalar-replacement-of-aggregates|SROA]] and [[instruction-combining|InstCombine]]. A later InstCombine/SimplifyCFG pass typically cleans up after it.

## 4. How it's built

> [!info] Core data structures
> - **`GVNPass::ValueTable`** — the value-number map: hashes expressions to numbers and exposes `lookupOrAdd` for instructions, loads, calls, and φ-nodes; a `NextValueNumber` counter mints fresh numbers.
> - **A leader table** — for each value number, the available "leader" instruction in the current scope, used to pick the replacement.
> - **[[dominator-tree|DominatorTree]]** — GVN walks in dominator order so a definition is numbered before its uses (the DVNT order from [[value-numbering]]).
> - **Memory dependence** — load PRE needs to know whether a load is available on each predecessor: classic `GVN` uses **`MemoryDependenceResults`** (MemDep); the rewrite `NewGVN` uses **[[memory-ssa|MemorySSA]]** instead.

## 5. Textbook DVNT → LLVM GVN (deviations)

> [!info]+ Where the real pass differs from the classic algorithm
> | Classic value numbering (DVNT) | What `GVNPass` actually does |
> |---|---|
> | Pure CSE: delete fully-redundant exprs | CSE **plus load PRE** (partial → full) in one pass |
> | Operates on scalars | Reasons about **memory** (loads) via MemDep + alias analysis |
> | "Available expressions" data-flow | Replaced by SSA + dominator-scoped value table |
> | Hoist freely to remove redundancy | **Guarded**: never insert a load on a path that didn't fault before; **won't grow code**; critical edges block load PRE unless safely split |
> | One canonical algorithm | Two implementations coexist: `GVN` (default) and `NewGVN` (opt-in rewrite) |

## 6. Run it yourself

> [!example]+ See GVN remove a redundant load
> ```bash
> # value numbering + load PRE on a single function
> opt -passes='gvn' -S input.ll -o -
>
> # try the experimental rewrite instead
> opt -passes='newgvn' -S input.ll -o -
> ```
> Add `-debug-only=gvn` (on an assertions build) to watch numbering and PRE decisions.

## 7. Flags & knobs

> [!note] Selected `cl::opt` switches (defaults in parentheses)
> - `-enable-pre` (**true**) — scalar PRE inside GVN.
> - `-enable-load-pre` / `GVNEnableLoadPRE` (**true**) — load PRE.
> - `-enable-load-in-loop-pre` (**true**) — allow load PRE for loop-carried loads.
> - `-enable-split-backedge-in-load-pre` (**false**) — permit splitting a backedge for load PRE.
> - `-enable-newgvn` (**false**) — swap in the `NewGVN` rewrite.

## 8. Siblings & variants

> [!info] The GVN family
> - **`NewGVN`** (`NewGVN.cpp`) — a from-scratch rewrite (congruence classes + [[memory-ssa|MemorySSA]]); intended to eventually replace `GVN` but **still off by default** (correctness/feature gaps; subject of recurring revival work).
> - **`GVNHoist`** (`GVNHoist.cpp`) — hoists identical computations to a common dominator; **disabled by default** after a string of bugs.
> - **`GVNSink`** (`GVNSink.cpp`) — the dual: sinks identical computations to a common post-dominator.

## 9. Limitations & version notes

> [!warning] Guards and gaps
> - Load PRE will **not** speculate a load onto a path that could fault, and will **not** increase code size — so it often declines on critical edges.
> - GVN does **not** do full lazy-code-motion-style scalar PRE; its scalar PRE is limited. Aggressive value-based PRE is part of what `NewGVN` aims at, not stock `GVN`.

> [!note] Version-sensitive
> Which value numberer is default (`GVN`), whether `NewGVN`/`GVNHoist` are opt-in, and the exact pipeline slot can shift between releases — this note is tagged `version-sensitive`; the tracked release lives in [[llvm-version]].

> [!summary] The one thing to remember
> `GVNPass` is the one LLVM pass that does **both** global value numbering (CSE) **and** load PRE — dominator-ordered value table for the first, MemDep-guarded load insertion for the second. `NewGVN` is the MemorySSA-based rewrite waiting in the wings (off by default).

> [!quote] Sources & confidence
> - **Source:** [`Transforms/Scalar/GVN.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/GVN.cpp) · [`NewGVN.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/NewGVN.cpp) — tier-1.
> - [`llvm::GVNPass` doxygen](https://llvm.org/doxygen/classllvm_1_1GVNPass.html) · [`ValueTable`](https://llvm.org/doxygen/classllvm_1_1GVNPass_1_1ValueTable.html).
> - [Reviving NewGVN — LLVM blog (2024)](https://blog.llvm.org/posts/2024-09-01-reviving-newgvn/).
> - **Status `draft`:** class layout, flags, and NewGVN/GVNHoist defaults verified against doxygen + LLVM blog; the precise `-O2` pipeline slot is stated from model knowledge and is the main thing to re-confirm against the source on review.
