---
title: Interprocedural Optimization
type: concept-moc
concepts: [interprocedural]
tags: [moc, kind/moc]
status: draft
---

# Interprocedural Optimization

> 🧭 **Concept MOC** · Chapter of [[Home]] · ecosystem view: [[LLVM.MOC]]
> **Prerequisites:** [[llvm-basics]] · [[call-graph|Call Graph]] · **Related chapters:** [[Constant-Propagation.MOC|Constant Propagation]] · [[Dead-Code-Elimination.MOC|Dead-Code Elimination]]

> [!abstract] What this chapter delivers
> Optimization that crosses function boundaries. The arc *the call graph as the substrate → inlining (the enabler) → specializing and devirtualizing calls → propagating facts and pruning across calls → tail calls*.

## 1. Substrate
The [[call-graph|Call Graph]] is what interprocedural passes traverse (bottom-up over SCCs in the CGSCC pipeline). The scalable way to cross function boundaries without re-analyzing per calling context is **summaries** → **[[interprocedural-summaries|Summary-Based (Compositional) Analysis]]** *(concept · analysis)* — the compositional technique behind LTO and whole-program tooling.

## 2. The enabler — inlining
Replacing a call with the callee body; the single most important IPO because it exposes intraprocedural opportunities everywhere else. → **[[inlining|Inlining]]**.

## 3. Specializing calls
- **[[devirtualization|Devirtualization]]** — turn indirect/virtual calls into direct ones (enables inlining).
- **[[function-specialization|Function Specialization]]** — clone a function specialized to constant arguments.

## 4. Propagating & pruning across calls
- **[[ipsccp|IPSCCP]]** — interprocedural constant + reachability propagation.
- **[[interprocedural-dead-code-elimination|Interprocedural DCE]]** — drop dead functions, args, and returns.

## 5. Call-shape transforms
- **[[tail-call-optimization|Tail-Call Optimization]]** — reuse the caller's frame for a call in tail position.

## 6. Where it's used / limits
The CGSCC pipeline at `-O2+` and LTO. Effectiveness scales with **visibility**: separate compilation hides callees, so the biggest IPO wins come under LTO/whole-program.

```dataview
TABLE facet, stage, status, src
WHERE contains(concepts, "interprocedural")
SORT facet ASC
```
