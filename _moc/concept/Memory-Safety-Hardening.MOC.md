---
title: Memory Safety & C/C++ Hardening
type: concept-moc
concepts: [memory-safety]
tags: [moc, kind/moc, status/draft]
status: draft
---

# Memory Safety & C/C++ Hardening

> 🧭 **Concept MOC** · Chapter of [[Home]] · ecosystem view: [[LLVM.MOC]]
> **Prerequisites:** [[llvm-basics]] · [[clang-ast|Clang AST]] · **Related chapters:** [[Source-Level-Analysis.MOC|Front-End & Source-Level Analysis]] · [[Interprocedural-Analysis.MOC|Interprocedural]]

> [!abstract] What this chapter delivers
> The Clang/LLVM features and analyses that **eliminate entire classes of memory-safety vulnerabilities** in C/C++ — by adding compiler-checkable *local rules* + *annotations* + *runtime support*, rather than rewriting the code. The arc: *spatial (bounds) → temporal & type → control-flow integrity → scaling the hardening → the source-level analyzers that find what's left*.

## 1. The strategy
You cannot rewrite the ocean of existing C/C++, so you **harden it**: restrict the language to a checkable subset, express invariants as annotations (assume/guarantee, like types), and fall back to runtime checks where static proof is undecidable. Each mechanism below targets one *class* of bug.

## 2. Spatial (bounds) safety
- **[[fbounds-safety|-fbounds-safety]]** — a C language extension: bounds annotations (`__counted_by`…) as [[clang-ast|AST]] type attributes + inserted runtime traps *(implementation · frontend)*.
- **[[safe-buffers|C++ Safe Buffers]]** — `-Wunsafe-buffer-usage` gadget analysis + hardened libc++ (`std::span`) *(implementation · analysis)*.
- backed by **[[constraint-elimination|ConstraintElimination]]** — the middle-end pass that removes the redundant inserted checks (Fourier–Motzkin over dominating conditions) *(implementation · optimization)*.

## 3. Temporal & type safety
- **[[lifetime-safety|Clang LifetimeSafety]]** — Rust-NLL-style loan/origin dataflow over the [[clang-cfg|Clang CFG]] for use-after-free / dangling *(implementation · analysis)*.
- **[[typed-allocators|Type-Aware Allocation]]** — `operator new`/`delete` receive the allocated type, enabling type-isolating allocators (mitigates UAF / type confusion) *(implementation · frontend)*.

## 4. Control-flow integrity
- **[[pointer-authentication|Pointer Authentication (ptrauth / arm64e)]]** — hardware-backed signing of control pointers to blunt ROP/JOP; Clang `__ptrauth` → `llvm.ptrauth.*` → AArch64 PAC *(implementation · codegen)*.

## 5. Scaling the hardening
- **[[interprocedural-summaries|Summary-Based (Compositional) Analysis]]** — the technique (per-procedure summaries composed over the [[call-graph]]) *(concept · analysis)*.
- **[[scalable-static-analysis|Scalable Static Analysis Framework (SSAF)]]** — "ThinLTO for static analysis": whole-program summary pipeline driving automated raw-pointer→`std::span` migration *(implementation · analysis, WIP)*.

## 6. The source-level analyzers
The bug-finders that catch what the above don't eliminate → the whole [[Source-Level-Analysis.MOC|Front-End & Source-Level Analysis]] chapter: **[[clang-static-analyzer|Clang Static Analyzer]]** (path-sensitive symbolic execution) and the **[[clang-dataflow-framework|Clang Dataflow Framework]]** (flow-sensitive).

## 7. Limitations & frontier
Most of these ship **experimental / incrementally** (`-fbounds-safety`, SSAF); enforcement is cheap-local + runtime because whole-program static proof doesn't scale ([[interprocedural-summaries]] is the scaling answer). The frontier is lowering **adoption cost** via automatic annotation inference / source rewriting (SSAF, clang-reforge).

```dataview
TABLE facet, stage, status, src
WHERE contains(concepts, "memory-safety")
SORT stage ASC, facet ASC
```
