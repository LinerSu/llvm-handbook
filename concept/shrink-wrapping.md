---
title: Shrink Wrapping
facet: concept
stage: codegen
ecosystem: [llvm]
concepts: [code-generation]
implements:
  - { ecosystem: llvm, src: "llvm/lib/CodeGen/ShrinkWrap.cpp" }
docs: "CodeGenerator ↗ https://llvm.org/docs/CodeGenerator.html"
book: "Muchnick, Advanced Compiler Design & Implementation §15.5"
prereqs: [code-generation-overview, dominator-tree]
related: [code-generation-overview, register-allocation]
tags: [kind/transform, status/verified]
status: verified
verified_on: 2026-06-28
---

# Shrink Wrapping

> 🧭 **Concept** · `concept · codegen · llvm` · Index [[LLVM.MOC]] · see also [[muchnick.MOC|Muchnick]]
> **Prerequisites:** [[code-generation-overview]], [[dominator-tree]]

> [!abstract] Chapter map
> The **prologue** (save callee-saved registers, set up the frame) and **epilogue** (restore, tear down) normally sit at function entry/exit. **Shrink wrapping** pushes them *inward* — to the smallest CFG region that actually needs the frame — so paths that return early without using it skip the save/restore entirely.

---

## 1. The idea

> [!example] An early-return fast path
> ```c
> void f(int n) {
>   if (n <= 0) return;          // common, cheap: needs no callee-saved regs
>   /* heavy work using many registers → needs the frame */
> }
> ```
> Putting the prologue at entry forces *every* call — including the `n<=0` fast path — to pay the save/restore. Shrink wrapping moves the prologue **after** the early-return check, so the fast path runs frame-free.

## 2. How LLVM places it

> [!info] Dominance-based placement
> LLVM's **`ShrinkWrap`** (a machine-IR pass) finds a **save point** that **dominates** every use of callee-saved registers / the frame, and a **restore point** that **post-dominates** them (see [[dominator-tree]] — post-dominators are dominators on the reverse CFG). The prologue goes at the save point, the epilogue at the restore point. If no such non-entry point exists (the frame is used everywhere), it falls back to the normal entry/exit placement.

> [!summary] The one thing to remember
> Shrink wrapping moves prologue/epilogue to the **smallest region that needs the frame** (save point = dominates all frame uses, restore point = post-dominates them), so early-return and other frame-free paths skip the save/restore cost.

> [!quote] Further reading
> - **Source:** [`CodeGen/ShrinkWrap.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/CodeGen/ShrinkWrap.cpp)
> - **Muchnick §15.5** — leaf-routine optimization and shrink wrapping.
