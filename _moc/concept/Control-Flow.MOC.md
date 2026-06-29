---
title: Control Flow
type: concept-moc
concepts: [control-flow]
tags: [moc, kind/moc]
status: draft
---

# Control Flow

> 🧭 **Concept MOC** · Chapter of [[Home]] · ecosystem view: [[LLVM.MOC]]
> **Prerequisites:** [[llvm-basics]] · **Related chapters:** [[SSA-Form.MOC|SSA Form]] · [[Dataflow-Analysis.MOC|Dataflow Analysis]] · [[Loop-Optimization.MOC|Loop Optimization]]

> [!abstract] What this chapter delivers
> The graph everything else runs on, and the transforms that reshape it. The arc *the CFG (blocks + terminator edges) → how source control flow becomes branches → simplifying and rewriting the graph → flattening branches for the backend*.

## 1. The structure
A `Function` **is** a CFG: nodes are basic blocks, edges come from each block's single **terminator**; dominance, loops, and φ-placement are all defined *over* it. → **[[control-flow-graph|Control-Flow Graph]]** *(data-structure · ir)*.

## 2. Building it
How source `if`/`while`/`switch`/short-circuit logic is lowered to branches and blocks. → **[[control-flow-translation|Control-Flow Translation]]**.

## 3. Cleaning it up
**[[simplifycfg|SimplifyCFG]]** — merge blocks, fold branches, remove unreachable code, form `switch`es; the CFG canonicalizer run throughout the pipeline.

## 4. Rewriting it for value flow
- **[[jump-threading|Jump Threading]]** — when a branch's outcome is known on an incoming path, route that path directly to the target, duplicating blocks as needed.

## 5. Flattening for the backend
- **[[if-conversion|If-Conversion]]** — replace short branches with predicated/`select` instructions to avoid misprediction (a codegen-stage transform).

## 6. Limitations & future
Block duplication (threading) trades code size for speed; **irreducible** control flow has no natural loop and limits structured reasoning; predication only pays off when branches are unpredictable.

```dataview
TABLE facet, stage, status, src
WHERE contains(concepts, "control-flow")
SORT facet ASC
```
