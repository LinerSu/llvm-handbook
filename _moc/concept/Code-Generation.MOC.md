---
title: Code Generation (Backend)
type: concept-moc
concepts: [code-generation]
tags: [moc, kind/moc]
status: draft
---

# Code Generation (Backend)

> 🧭 **Concept MOC** · Chapter of [[Home]] · ecosystem view: [[LLVM.MOC]]
> **Prerequisites:** [[llvm-basics]] · [[ssa-form]] · **Related chapters:** [[Loop-Optimization.MOC|Loop Optimization]]

> [!abstract] What this chapter delivers
> How target-independent IR becomes machine code: the backend pipeline *instruction selection → scheduling → register allocation → prologue/epilogue & MC emission*, and the concept notes for each stage.

## 1. Overview — the backend pipeline
The end-to-end path and where each stage sits. → **[[code-generation-overview|Code Generation Overview]]**.

## 2. Instruction selection
Map IR (or SelectionDAG / GMIR) to target instructions. → **[[instruction-selection|Instruction Selection]]** (SelectionDAG vs. GlobalISel; defaults are [[llvm-version|version-sensitive]]).

## 3. Scheduling
Order instructions to expose ILP and hide latency. → **[[instruction-scheduling|Instruction Scheduling]]**.

## 4. Register allocation
Assign virtual to physical registers, spilling under pressure. → **[[register-allocation|Register Allocation]]** (Greedy at `-O1+`, Fast at `-O0`).

## 5. Frame & emission
- **[[shrink-wrapping|Shrink Wrapping]]** — sink prologue/epilogue so the frame is set up only on paths that need it.

## 6. Where it's used / limits
Every compiled target; quality is dominated by ISel pattern coverage and regalloc heuristics. Target-specific behavior is the main version- and target-sensitivity in the vault.

```dataview
TABLE facet, stage, status, src
WHERE contains(concepts, "code-generation")
SORT facet ASC
```
