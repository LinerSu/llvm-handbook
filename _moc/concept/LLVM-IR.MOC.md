---
title: LLVM IR
type: concept-moc
concepts: [llvm-ir]
tags: [moc, kind/moc]
status: draft
---

# LLVM IR

> 🧭 **Concept MOC** · Chapter of [[Home]] · ecosystem view: [[LLVM.MOC]]
> **Prerequisites:** none · **Related chapters:** [[SSA-Form.MOC|SSA Form]] · [[Control-Flow.MOC|Control Flow]]

> [!abstract] What this chapter delivers
> The "narrow waist" every front end and back end plugs into: a typed, RISC-like, SSA, three-address IR. The arc *what the IR and object model are → addressing (the part people get wrong) → how to extend it*. This is the foundations chapter; the cross-facet reading path lives in [[LLVM.MOC]].

## 1. The IR & object model
What LLVM is (reusable components, three-phase architecture) and the `Module → Function → BasicBlock → Instruction` model with the core `Type` / `Value` / `Use` classes. → **[[llvm-basics|LLVM Basics]]**.

## 2. Addressing
The one instruction worth its own note — `getelementptr` computes addresses without touching memory; the classic source of confusion. → **[[getelementptr|GetElementPtr]]**.

## 3. Extending the IR
Adding instructions, types, intrinsics, parameter attributes, metadata, and remarks — how the IR grows without forking it. → **[[extending-llvm-ir|Extending LLVM IR]]**.

## 4. Why it matters
A single well-specified IR is what lets many languages (Clang, Rust, Swift) and many targets reuse one optimizer — the whole value proposition of LLVM. It is also what makes [[ssa-form|SSA]] universal across the middle end.

## 5. Limitations & future
The IR is target-independent only up to a point (datalayout, intrinsics, ABI leak through); higher-level structure that the flat IR loses is the motivation for **MLIR** dialects.

```dataview
TABLE facet, stage, status, src
WHERE contains(concepts, "llvm-ir")
SORT facet ASC
```
