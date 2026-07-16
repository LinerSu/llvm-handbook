---
title: algorithm/ — about this layer
type: meta
tags: [meta, facet-about]
---

# algorithm/ — procedures (tool-agnostic)

Concrete algorithms and recipes, independent of language or tool. A note belongs here when its subject is a **procedure**. See [[classification-protocol]].

But "is it a procedure?" is not a sufficient test — it would admit quicksort. This layer exists for a specific purpose, and that purpose sets a sharper bar.

## What this layer is for

**You know the concept but have forgotten how it's achieved** — and that gap is blocking you from reading what LLVM actually does. A note here is the *refresher*, and its payoff is the note it unblocks: shipping code implements real algorithms, and the fastest way to understand a production compiler is to know what it started from, then see where it departed.

That departure — **the textbook says X, the shipped code does Y, here's why** — is the most valuable content in this vault. It only lands if X is written down somewhere. That somewhere is here.

## The bar (both parts required)

1. **An existing note already leans on it.** The demand signal: the note fills a gap a reader actually hits, rather than padding the folder. If nothing in the vault invokes the algorithm, it doesn't belong here yet.
2. **LLVM ships a concrete implementation to point at.** This keeps the layer LLVM-motivated (invariant #4 in `CLAUDE.md`) even though the body is tool-agnostic. The note must name where.

Quicksort fails (1) — nothing here leans on it. Topological sort fails (1) too: its entire compiler content is "any topological order is a legal schedule", which is one line, and it already sits in [[instruction-scheduling]] where it belongs. **DFS, BFS, union-find as such, hash maps** are prerequisites a compilers reader already has; re-teaching them is not this layer's job. [[unification]] earns its place because the *same* union-find drives two unrelated things ([[type-checking]] and [[pointer-alias-analysis]]) — an insight a data-structures course can't give you.

## The shape of a note here

Refresher first, LLVM second:

1. **The problem** — what is being computed, precisely.
2. **The algorithm** — tool-agnostic, with a worked trace. This is the part you came back for.
3. **What LLVM ships** — and, if it differs, *why*. Quote the source; the in-tree comments usually explain the trade themselves.
4. **The delta** — one summary table. If there is no delta, say so plainly; that's a finding too (see [[mark-and-sweep-reachability]], where the algorithm survives intact and all the engineering has moved into defining the graph).

[[unification]] is the reference shape; [[dominator-tree-construction]] is the reference *delta*.

## Wiring

A note here is reached from its consumer via the typed **`algorithm:`** frontmatter field — [[mem2reg]] carries `algorithm: [ssa-construction]`, [[call-graph]] carries `algorithm: [tarjan-scc]`. Populate that field on the consuming note whenever you add one here. The link is the whole point; an orphaned algorithm note is a failed one.

## Current residents

| Note | LLVM anchor | The delta |
|---|---|---|
| [[unification]] | Steensgaard/DSA + type inference | none — same union-find, two unrelated uses |
| [[dominator-tree-construction]] | `GenericDomTreeConstruction.h` | ships **Semi-NCA**, *not* near-linear Lengauer–Tarjan — an $O(n^2)$ worst case bought for incremental updates |
| [[ssa-construction]] | `mem2reg` + `ForwardIDFCalculator` | frontier is **Sreedhar–Gao**, not Cytron; **pruned**, not minimal; CFG walk, not domtree recursion |
| [[tarjan-scc]] | `LazyCallGraph` / CGSCC | faithful Tarjan to *build*; incremental repair to *maintain*, because the inliner mutates mid-walk |
| [[switch-lowering]] | `LowerSwitch`, `SwitchLoweringUtils` | one sorted array becomes a BST, an exact $O(n^2)$ DP, and a jump table — the objective differs, the structure doesn't |
| [[graph-coloring]] | `RegAllocGreedy` (by contrast) | LLVM ships **neither** Chaitin nor linear scan — splitting beats coloring |
| [[mark-and-sweep-reachability]] | `GlobalDCE` | algorithm intact; all difficulty moved into roots, comdats, and vtable edges |
| [[dependence-testing]] | `DependenceAnalysis` | Banerjee's equations **simplified** because SCEV normalized the loops; no Omega test; monotonicity assumed but unchecked |

## Candidates not yet written

- **SSA reconstruction** (`SSAUpdater`) → leaned on by [[loop-transformations|LCSSA]] and several loop passes. Distinct from [[ssa-construction]]: it *repairs* SSA rather than building it.
- **Abstract interpretation as a cost model** → `InlineCost` is a bounded abstract interpretation of the callee, specialized per call site, with threshold-directed early exit. Currently described only inside [[inlining]].

Something that clears **both** parts of the bar and isn't listed: add it. Something that clears only one: leave it in the note that uses it.
