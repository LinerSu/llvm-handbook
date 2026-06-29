---
title: Sparse Conditional Constant Propagation (SCCP)
facet: concept
stage: optimization
ecosystem: [general, llvm]
concepts: [dataflow-analysis, constant-propagation]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/Scalar/SCCP.cpp" }
docs: "Passes — sccp ↗ https://llvm.org/docs/Passes.html"
book: "Muchnick, Advanced Compiler Design & Implementation §12.6"
prereqs: [data-flow-analysis, ssa-form]
related: [data-flow-analysis, dataflow-foundations, dead-code-elimination, lazy-value-info, correlated-value-propagation]
tags: [kind/transform, status/verified]
status: verified
verified_on: 2026-06-28
---

# Sparse Conditional Constant Propagation (SCCP)

> 🧭 **Concept** · `concept · optimization · general+llvm` · Index [[LLVM.MOC]] · see also [[muchnick.MOC|Muchnick]]
> **Prerequisites:** [[data-flow-analysis]], [[ssa-form]] · **Lattice:** see [[data-flow-analysis]] · **Range cousin:** [[lazy-value-info]]

> [!abstract] Chapter map
> SCCP (Wegman–Zadeck) does two things **at once**: propagate constants through SSA values *and* track which CFG edges are **executable**. Doing them jointly finds more constants than constant-propagation-then-DCE run separately — because it can prove a branch dead and ignore the values flowing along it.

---

## 1. The idea

> [!info] Two lattices, one fixpoint
> SCCP keeps, for each SSA value, a lattice cell `undef → constant → overdefined` (see the [[data-flow-analysis|constant-propagation lattice]]), **and** for each CFG edge a flag: *executable* or not. It propagates values only along **executable** edges. A conditional branch on a value already known to be a **constant** marks **only the taken successor** executable — so the other arm's instructions are never even evaluated.

## 2. Why "conditional" beats plain const-prop

> [!example] What separate passes miss
> ```c
> int g = 1;
> if (g) x = 5; else x = read();   // else is unreachable, but plain const-prop can't prove it
> use(x);
> ```
> Ordinary constant propagation evaluates **both** arms, sees `x` is `5` on one and unknown on the other, and concludes `x` is *overdefined*. **SCCP** marks the `else` edge **non-executable** (because `g` is the constant `1`), so only `x = 5` reaches the use → it proves `x == 5` and folds it. The dead `else` is then removed.

## 3. In LLVM

LLVM's **`SCCP`** pass implements this intraprocedurally; [[ipsccp|**`IPSCCP`**]] extends it across function boundaries (propagating constant arguments and return values). Both fold the constants they prove and delete the branches/blocks they mark unreachable (overlapping with [[dead-code-elimination|DCE]]).

> [!summary] The one thing to remember
> SCCP propagates constants **and** CFG reachability together (a constant branch condition kills the other arm), so it finds constants that constant-prop + DCE run separately cannot. LLVM: **`SCCP`** (intraprocedural) and **`IPSCCP`** (interprocedural).

> [!quote] Further reading
> - **Source:** [`Transforms/Scalar/SCCP.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/SCCP.cpp) (and IPSCCP)
> - **Muchnick §12.6**; **Dragon §9.4**; Wegman & Zadeck 1991 — *Constant Propagation with Conditional Branches*.
