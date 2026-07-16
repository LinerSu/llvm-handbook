---
title: Dominance
type: concept-moc
concepts: [dominance]
tags: [moc, kind/moc]
status: draft
---

# Dominance

> 🧭 **Concept MOC** · Chapter of [[Home]] · ecosystem view: [[LLVM.MOC]]
> **Prerequisites:** [[control-flow-graph]] · **Related chapters:** [[SSA-Form.MOC|SSA Form]] · [[Control-Flow.MOC|Control Flow]] · [[Loop-Optimization.MOC|Loop Optimization]]

> [!abstract] What this chapter delivers
> "Does every path to B go through A?" — the single most reused question in the middle-end. The arc: *what dominance is → the tree and frontier built from it → how that tree is actually constructed (and why LLVM's answer is not the textbook's) → what it unlocks*.

## 1. Definition & structure
$A$ dominates $B$ iff every entry→$B$ path passes through $A$; make $idom(B)$ the parent of $B$ and you get a tree where dominance queries become **ancestor checks**. The **dominance frontier** is where a block's dominance runs out — exactly the merges that need a φ. → **[[dominator-tree|Dominator Tree & Dominance Frontier]]** *(data-structure · analysis)*.

## 2. Algorithm — how the tree is built
Not the near-linear **Lengauer–Tarjan** the textbooks give you. LLVM ships **Semi-NCA**: it keeps LT's semidominator phase and replaces LT's bucket phase with a nearest-common-ancestor walk, accepting an $O(n^2)$ worst case in exchange for simpler code and **cheap incremental updates** — which is what matters when hundreds of passes mutate the CFG underneath the tree. → **[[dominator-tree-construction|Dominator Tree Construction (Semi-NCA)]]** *(algorithm · analysis)*.

## 3. The payoff — φ placement
SSA construction places φ at the **iterated dominance frontier** of a variable's definitions. That's the theory (Cytron et al.); what `mem2reg` actually runs is a **Sreedhar–Gao** level walk that never materializes a frontier set, and prunes by liveness as it goes. → **[[ssa-construction|SSA Construction]]** *(algorithm · ir)*, realized by **[[mem2reg]]**.

## 4. Where it's used
Everywhere downstream: [[value-numbering|GVN]] and [[early-cse|EarlyCSE]] for dominance queries and scoping, [[loop-invariant-code-motion|LICM]] for hoist legality (though it replaces plain "dominates all exits" with a stronger must-execute test), [[loop-info|LoopInfo/LCSSA]] for loop structure, and [[jump-threading]] / [[simplifycfg]] — which mutate the CFG and must therefore *maintain* the tree via `DomTreeUpdater` rather than invalidate it.

## 5. Post-dominance
$B$ post-dominates $A$ iff every path from $A$ to the exit passes through $B$ — dominance on the reverse CFG. Drives control-dependence and sinking transforms; the same Semi-NCA code computes it, templated on direction.

## 6. Limitations & future
Dominance is defined only for **reachable** blocks. Plain domtree dominance is also weaker than it looks inside a block: a call that may throw means "A dominates B" no longer implies "A's execution guarantees B's" — which is why [[loop-invariant-code-motion|LICM]] carries a separate implicit-control-flow tracker rather than trusting the tree alone.

```dataview
TABLE facet, stage, status, src
WHERE contains(concepts, "dominance")
SORT facet ASC
```
