---
title: mem2reg (Promote Memory to Register)
facet: concept
stage: optimization
ecosystem: [general, llvm]
concepts: [ssa, memory-optimization]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/Utils/PromoteMemoryToRegister.cpp" }
data_structures: [dominator-tree, ssa-form]
src: "llvm/lib/Transforms/Utils/PromoteMemoryToRegister.cpp"
docs: "Kaleidoscope Ch.7 — mem2reg ↗ https://llvm.org/docs/tutorial/MyFirstLanguageFrontend/LangImpl07.html"
prereqs: [ssa-form, dominator-tree]
related: [scalar-replacement-of-aggregates, value-numbering, llvm-gvn]
tags: [kind/transform, status/verified]
status: verified
verified_on: 2026-06-28
sources:
  - "https://llvm.org/doxygen/PromoteMemoryToRegister_8cpp.html"
  - "https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Utils/PromoteMemoryToRegister.cpp"
---

# mem2reg (Promote Memory to Register)

> 🧭 **Concept** · `concept · optimization · general+llvm` · Index [[LLVM.MOC]]
> **Prerequisites:** [[ssa-form]], [[dominator-tree]] · **Sibling:** [[scalar-replacement-of-aggregates]] · **Enables:** [[value-numbering]], [[llvm-gvn]]

> [!abstract] Chapter map
> Front ends emit every local variable as a stack slot (`alloca` + `load`/`store`). **mem2reg** is the pass that turns those promotable stack slots into **SSA virtual registers + φ-nodes** — i.e. it *constructs* [[ssa-form|SSA]]. It is the classic Cytron et al. algorithm: place φ at iterated dominance frontiers, then rename.

> [!info]+ Classic SSA construction → LLVM mem2reg
> | Classic (Cytron et al. 1991) | LLVM realization |
> |---|---|
> | Variables in memory / no SSA | `alloca` stack slots from the front end |
> | φ at **iterated dominance frontiers** | same — computed from the [[dominator-tree]] |
> | Rename pass walking the dominator tree | `PromoteMemoryToRegister` renaming stack |
> | "Minimal" SSA | mem2reg's φ placement (pruned by live-in blocks) |
> | — | Fast paths: single-store and single-block allocas skip φ entirely |

---

## 1. Definition

> [!note] What it does
> **mem2reg** promotes an `alloca` whose **address is never taken** — used only by direct `load`/`store` — into SSA values, inserting **φ-nodes** at control-flow merges so each use reads the right definition. Memory traffic disappears; the value lives in a register.

## 2. When is an alloca promotable?

> [!info] Promotion criteria
> An `alloca` is promotable iff:
> - every `load`/`store` uses the alloca's **allocated type** directly (no bitcast/type-pun) — usually a scalar, though whole-aggregate allocas qualify too; aggregates are normally split first by [[scalar-replacement-of-aggregates|SROA]];
> - it is used **only** by `load`/`store` (its address does **not** escape — no pointer arithmetic, no passing to calls);
> - the loads/stores are **non-volatile**.

## 3. Algorithm

> [!example]- mem2reg in three moves (click to expand)
> ```text
> 1. Collect info per alloca: defining blocks (stores) and using blocks (loads).
> 2. Place φ: at the iterated dominance frontier of the defining blocks,
>    pruned to blocks where the value is live-in.
> 3. Rename: DFS the dominator tree carrying a "current value" stack per alloca;
>    replace each load with the reaching value; each store updates the stack;
>    fill φ operands from predecessors.
>
> Fast paths:
>   - single store  -> dominated loads take the stored value directly
>   - single block  -> linear scan, no φ needed
> ```

## 4. Worked example

> [!example]+ Stack slot → SSA + φ
> **Before (front-end output):**
> ```llvm
> entry:
>   %x = alloca i32
>   br i1 %c, label %then, label %else
> then:
>   store i32 1, ptr %x
>   br label %done
> else:
>   store i32 2, ptr %x
>   br label %done
> done:
>   %v = load i32, ptr %x      ; which store reaches here?
> ```
> **After mem2reg:**
> ```llvm
> done:
>   %v = phi i32 [ 1, %then ], [ 2, %else ]   ; φ at the merge; alloca gone
> ```

## 5. In LLVM

> [!info] Where it lives
> The engine is `PromoteMemoryToRegister` in [`Transforms/Utils/PromoteMemoryToRegister.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Utils/PromoteMemoryToRegister.cpp), exposed as the `mem2reg` pass (`Transforms/Utils/Mem2Reg.cpp`) and also driven **inside [[scalar-replacement-of-aggregates|SROA]]** after it splits aggregates into scalar slots. It runs early at `-O1+`; almost every later SSA-based optimization assumes it has happened.

## 6. Why it matters

mem2reg is the gateway to the optimizer: once locals are SSA values, [[value-numbering|GVN]], [[instruction-combining|InstCombine]], [[sparse-conditional-constant-propagation|SCCP]], and the loop passes can all reason about def-use chains directly instead of chasing memory.

> [!summary] The one thing to remember
> mem2reg = **SSA construction**: promote address-not-taken scalar `alloca`s to registers, placing φ at iterated dominance frontiers (Cytron), with single-store/single-block fast paths. SROA splits aggregates first, then hands the scalar slots to mem2reg.

> [!quote] Sources & confidence
> - **Source:** [`Transforms/Utils/PromoteMemoryToRegister.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Utils/PromoteMemoryToRegister.cpp) — tier-1.
> - [Kaleidoscope Ch.7 — *Mutable Variables / mem2reg*](https://llvm.org/docs/tutorial/MyFirstLanguageFrontend/LangImpl07.html).
> - Cytron, Ferrante, Rosen, Wegman, Zadeck, *Efficiently Computing SSA* (1991) — the φ-placement algorithm.
