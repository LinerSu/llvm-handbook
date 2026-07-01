---
title: LLVM
type: ecosystem-moc
ecosystem: llvm
tags: [moc, kind/moc]
status: draft
---

# LLVM — ecosystem map & reading path

> 🧭 **Ecosystem MOC** · Chapter of [[Home]] · folders are by *facet*; this note is the LLVM view.

A dependency-ordered reading path plus a jump-to-any-topic index for the LLVM-the-tool notes. Folders stay facet-based (`concept/ data-structure/ …`); this note reconstructs the source-tree / pipeline view. Each note opens with a 🧭 breadcrumb and a *classic-theory → LLVM* table.

## 📚 Recommended reading order

**Foundations (read first):** **[[control-flow-graph|Control-Flow Graph]]** → **[[dominator-tree|Dominator Tree]]** — the graph and dominance structure everything else builds on.

1. **[[llvm-basics|LLVM Basics]]** — what LLVM is, the three-phase architecture, the IR object model (Module → Function → BasicBlock → Instruction), `.ll` format, core classes. _Prereq: none._
   - ↳ deep dive: **[[getelementptr|GetElementPtr]]** (read alongside / after basics)
2. **[[ssa-form|SSA Form]]** — single-assignment values, def-use / use-def chains, φ nodes. _Prereq: [[llvm-basics]]._
   - ↳ memory side: **[[memory-ssa|Memory SSA]]**
3. **[[extending-llvm-ir|Extending LLVM IR]]** — instructions, types, intrinsics, parameter attributes, metadata, remarks. _Prereq: [[llvm-basics]]._
4. **[[loop-info|LoopInfo & Canonical Forms]]** → **[[loop-transformations|Loop Transformations]]** — loop terminology, LoopSimplify/LCSSA/rotation, then unroll/LICM/fission/fusion/vectorization. _Prereq: [[llvm-basics]], [[ssa-form]]._
5. **[[pointer-alias-analysis|Pointer / Alias Analysis]]** — may/must/no alias, the AliasAnalysis interface, DSA. _Prereq: [[llvm-basics]]._
6. **[[instruction-combining|Instruction Combining]]** — the peephole / canonicalization worklist (no CFG changes). _Prereq: [[llvm-basics]], [[ssa-form]]._
7. **[[value-numbering|Value Numbering]]** — redundancy elimination via LVN and GVN. _Prereq: [[ssa-form]]._
8. **[[data-flow-analysis|Data-Flow Analysis]]** — program-analysis foundation: lattices, MFP/MOP, worklist; SCCP & MLIR's `DataFlowSolver`. _Prereq: [[control-flow-graph]]._
9. **[[code-generation-overview|Code Generation (Backend)]]** — instruction selection → scheduling → register allocation → MC emission. _Prereq: [[llvm-basics]], [[ssa-form]]._

> Tip: after [[value-numbering]], revisit the transform half of [[loop-transformations]] (LICM, unroll, fusion) — they build on [[loop-info|LoopInfo]] + LCSSA + [[pointer-alias-analysis|alias analysis]].

## 🔁 Dependency map

```text
control-flow-graph ─> dominator-tree ──┐ (foundations)
                                       v
llvm-basics ─┬─> ssa-form ─┬─> instruction-combining
             │             ├─> value-numbering (GVN)
             │             ├─> memory-ssa
             │             └─> loop-info ─> loop-transformations (LICM, unroll, fusion)
             ├─> extending-llvm-ir
             ├─> getelementptr (addressing deep-dive)
             ├─> data-flow-analysis (SCCP, ranges → MLIR DataFlowSolver)
             ├─> pointer-alias-analysis ──> (feeds memory-aware transforms)
             └─> code-generation-overview (ISel → regalloc → MC)
```

## 🗂 Auto-index (all LLVM-layer notes)

```dataview
TABLE facet, stage, status, src
FROM "concept" OR "data-structure" OR "implementation"
WHERE contains(ecosystem, "llvm")
SORT stage ASC, facet ASC
```

## 🔗 Source-tree crosswalk

Each note's `src:` points at the real path. `IR/` ↔ `llvm/lib/IR`, `Analysis/` ↔ `llvm/lib/Analysis`, `Transforms/{InstCombine,Scalar}` ↔ the matching passes. **Pass-level deep dives** (the `implementation/` facet) document one concrete pass each: [[llvm-gvn]] (realizes [[value-numbering]] + [[partial-redundancy-elimination]]). Concept chapters: [[Loop-Optimization.MOC]]. **Front end (Clang AST/CFG, before IR):** [[Source-Level-Analysis.MOC|Front-End & Source-Level Analysis]] — the [[clang-static-analyzer|Static Analyzer]] & [[clang-dataflow-framework|dataflow framework]] over the [[clang-cfg|Clang CFG]]. Book bridges: [[dragon-book-ch6.MOC|Dragon Book Ch.6]] · [[dragon-book-ch8.MOC|Ch.8]] · [[dragon-book-ch9.MOC|Ch.9]] · [[dragon-book-ch10.MOC|Ch.10]] · [[dragon-book-ch11.MOC|Ch.11]] · [[dragon-book-ch12.MOC|Ch.12]] · [[muchnick.MOC|Muchnick]] (theory → LLVM).
