---
title: Home
type: home-moc
tags: [moc, kind/moc, home]
status: draft
---

# 🏠 Home — a living book on compilers

The vault is one book spanning **theory → algorithm → LLVM → real-world use**. Folders are by **facet** (the kind of knowledge); chapters and source-tree views are **MOCs**; classification/correctness rules live in **`_meta/`**.

## 📖 Reading path — read it like a book

> [!tip] New here? Start with the two lines below, then read the chapters in order.
> **The folders are just storage (by *facet*) — the order to *read* in is this list.** Follow the links, not the directory tree.

**Chapter 0 · Orientation —** **[[running-example]]**: one tiny program (`accumulate`) carried through the whole pipeline — front-end IR → SSA → optimized → inlined. Read it first; every chapter below is a zoom into one stage of it.

**Part I — The representation**
1. **LLVM IR & object model** → [[LLVM-IR.MOC]] — what the IR is; Module→Function→BasicBlock→Instruction; GEP addressing. *(no prereq)*
2. **Control flow & dominance** → [[control-flow-graph]] then [[dominator-tree]] — the CFG and the dominance every analysis stands on. *(after 1)*
3. **SSA form** → [[SSA-Form.MOC]] — single-assignment values, φ-nodes, and **mem2reg** (how SSA is built). *(after 1–2)*

**Part II — Analysis & loops**
4. **Loops** → [[Loop-Optimization.MOC]] — LoopInfo & canonical form, scalar evolution, induction variables, the transforms. *(after 3)*
5. **Data-flow analysis** → [[Dataflow-Analysis.MOC]] — lattices, the worklist, SCCP: the analysis backbone. *(after 2)*

**Part III — The classic optimizations** *(after 3–5)*
6. **Memory** → [[Memory-Optimization.MOC]] · **Redundancy** → [[Redundancy-Elimination.MOC]] · **Constant/value propagation** → [[Constant-Propagation.MOC]] · **Dead code** → [[Dead-Code-Elimination.MOC]] · **CFG cleanup** → [[Control-Flow.MOC]] · **Peephole** → [[instruction-combining]]
7. **Interprocedural** → [[Interprocedural-Analysis.MOC]] — inlining, devirtualization, IPSCCP.
8. **Alias analysis** → [[pointer-alias-analysis]] — the legality currency for memory optimizations.

**Part IV — Backend (real-world output)**
9. **Code generation** → [[Code-Generation.MOC]] — instruction selection → scheduling → register allocation → emission.

**Reference shelf** — theory: [[dataflow-foundations]], [[polyhedral-model]]; textbook crosswalks: [[muchnick.MOC|Muchnick]] · [[dragon-book-ch9.MOC|Dragon Book Ch.9]] (and Ch.6/8/10/11/12).

## Index — jump to anything
- **Ecosystems** — [[LLVM.MOC|LLVM]] (more to come: MLIR, Clang, Rust, Swift, JAX, PyTorch)
- **Chapters** — see the **📖 Reading path** above for the ordered concept-MOC curriculum.
- **Book bridges** — [[dragon-book-ch6.MOC|Dragon Book Ch.6 → LLVM]] (Intermediate-Code Generation) · [[dragon-book-ch8.MOC|Ch.8 → LLVM]] (Code Generation) · [[dragon-book-ch9.MOC|Ch.9]] (Machine-Indep. Optimizations) · [[dragon-book-ch10.MOC|Ch.10]] (Instruction-Level Parallelism) · [[dragon-book-ch11.MOC|Ch.11]] (Parallelism & Locality) · [[dragon-book-ch12.MOC|Ch.12]] (Interprocedural Analysis) · [[muchnick.MOC|Muchnick — Advanced Compiler Design]] (whole-book reading map)
- **The rulebook** — [[classification-protocol]] · [[controlled-vocabulary]] · [[callout-legend]] · [[source-hierarchy]] · [[chapter-bridge-pipeline]] · [[note-checklist]] · [[llvm-version]]

## The bookshelf (facets) — *storage, not reading order*
Where each note *lives* (one axis: the kind of knowledge). To *read*, use the path above — not these folders.
`concept/` techniques · `theory/` definitions & proofs · `algorithm/` procedures · `data-structure/` representations · `implementation/` system-specific realizations · `application/` real-world use & frontier. (See each folder's `_about` note.)

## How to extend
Add a note from `_templates/topic-note.md`, fill its frontmatter (facet · stage · ecosystem · concepts · src · prereqs · status), and it self-files into the indexes below. For a brand-new topic, follow [[classification-protocol]]; the confidence gate flags genuine novelty as `status: needs-review`.

## Needs attention

```dataview
TABLE facet, stage, ecosystem, status
FROM "concept" OR "data-structure" OR "theory" OR "algorithm" OR "implementation" OR "application"
WHERE status = "needs-review" OR status = "stub" OR status = "migrated"
SORT status ASC
```

## All notes by facet

```dataview
TABLE stage, ecosystem, status
FROM "concept" OR "data-structure" OR "theory" OR "algorithm" OR "implementation" OR "application"
SORT facet ASC, stage ASC
```
