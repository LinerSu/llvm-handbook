---
title: Home
type: home-moc
tags: [moc, kind/moc, home]
status: draft
---

# 🏠 Home — a living book on compilers

The vault is one book spanning **theory → algorithm → LLVM → real-world use**. Folders are by **facet** (the kind of knowledge); chapters and source-tree views are **MOCs**; classification/correctness rules live in **`_meta/`**.

## Start here
- **Ecosystems** — [[LLVM.MOC|LLVM]] (more to come: MLIR, Clang, Rust, Swift, JAX, PyTorch)
- **Chapters (concept MOCs)** — Foundations: [[LLVM-IR.MOC|LLVM IR]] · [[SSA-Form.MOC|SSA Form]] · [[Control-Flow.MOC|Control Flow]] · [[Dataflow-Analysis.MOC|Dataflow Analysis]]. Optimization: [[Loop-Optimization.MOC|Loop Optimization]] · [[Redundancy-Elimination.MOC|Redundancy Elimination]] · [[Dead-Code-Elimination.MOC|Dead-Code Elimination]] · [[Constant-Propagation.MOC|Constant & Value Propagation]] · [[Memory-Optimization.MOC|Memory Optimization]] · [[Interprocedural-Analysis.MOC|Interprocedural Optimization]] · [[Code-Generation.MOC|Code Generation]]
- **Book bridges** — [[dragon-book-ch6.MOC|Dragon Book Ch.6 → LLVM]] (Intermediate-Code Generation) · [[dragon-book-ch8.MOC|Ch.8 → LLVM]] (Code Generation) · [[dragon-book-ch9.MOC|Ch.9]] (Machine-Indep. Optimizations) · [[dragon-book-ch10.MOC|Ch.10]] (Instruction-Level Parallelism) · [[dragon-book-ch11.MOC|Ch.11]] (Parallelism & Locality) · [[dragon-book-ch12.MOC|Ch.12]] (Interprocedural Analysis) · [[muchnick.MOC|Muchnick — Advanced Compiler Design]] (whole-book reading map)
- **The rulebook** — [[classification-protocol]] · [[controlled-vocabulary]] · [[callout-legend]] · [[source-hierarchy]] · [[chapter-bridge-pipeline]] · [[note-checklist]] · [[llvm-version]]

## The bookshelf (facets)
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
