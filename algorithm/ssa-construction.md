---
title: SSA Construction (φ-placement & renaming)
facet: algorithm
stage: ir
ecosystem: [general]
concepts: [ssa, dominance]
book: "Dragon Book (Aho/Lam/Sethi/Ullman, 2e) §6.2.4"
docs: "doxygen — PromoteMemToReg ↗ https://llvm.org/doxygen/PromoteMemToReg_8h.html"
prereqs: [dominator-tree, ssa-form]
related: [mem2reg, dominator-tree-construction, ssa-form]
tags: [kind/algorithm, status/verified, version-sensitive]
status: verified
verified_on: 2026-07-16
---

# SSA Construction (φ-placement & renaming)

> 🧭 **Algorithm** · `algorithm · ir · general` · Index [[LLVM.MOC]] · see also [[dragon-book-ch6.MOC|Dragon Ch.6]]
> **Powers:** [[mem2reg]] — and therefore essentially the whole middle-end, since almost every pass assumes [[ssa-form|SSA]]
> **Prerequisites:** [[dominator-tree]]

> [!abstract] Chapter map
> Two questions: **where do φ nodes go**, and **which definition does each use refer to**. The famous answer is Cytron et al. — φs at the *iterated dominance frontier*, then a dominator-tree renaming walk. LLVM's `mem2reg` follows that skeleton and then departs from it at **every single step**: a different frontier algorithm, a different SSA flavour, a different traversal, and a different stack. §5 is where the textbook stops describing the code.

---

## 1. The problem

> [!note] Definition
> Given a CFG where a variable is assigned in several blocks, place **φ nodes** so that every use has exactly one reaching definition, then rewrite each use to name that definition. A φ in block $B$ with predecessors $P_1 \ldots P_k$ selects the value that flowed in along the edge actually taken.

> [!info] Three flavours, and the vocabulary matters
> | Flavour | φ placed when | Cost |
> |---|---|---|
> | **Maximal** | a φ for every variable in every block | correct, absurdly wasteful |
> | **Minimal** | at the iterated dominance frontier of the defs (Cytron) | no φ is *structurally* redundant, but some are **dead** |
> | **Pruned** | minimal, minus φs for values not **live** at that block | fewest φs; needs liveness |
>
> "Minimal" is a term of art and does **not** mean "fewest". It means minimal *with respect to the frontier criterion alone*. A minimal-SSA φ can still be dead — nothing uses it — and a later DCE pass is expected to sweep it. Pruned SSA never builds it in the first place.

## 2. Cytron et al. — the iterated dominance frontier

> [!note] The placement rule
> For a variable defined in blocks $D$, place φs at $DF^+(D)$ — the **iterated** [[dominator-tree|dominance frontier]]. Iterated because each φ you place is *itself a new definition*, with its own frontier, so you re-apply $DF$ until the set stops growing.

The intuition is exactly the frontier's definition: $DF(A)$ is where $A$'s dominance runs out — the first blocks reachable from $A$ that $A$ does not strictly dominate. Those are precisely the merges where a definition in $A$ can collide with a different one. Fixpoint over that, and you have every merge that needs a φ.

Then **rename**: walk the dominator tree depth-first, keeping a **stack per variable** of the currently-reaching definition. Entering a block, push its definitions; rewrite uses to the stack top; fill in successors' φ operands; on the way out, pop what you pushed.

This is the algorithm in every textbook, and it is a fair description of `mem2reg`'s *shape*. It is not a description of `mem2reg`'s *code*.

## 3. What LLVM ships — the frontier

> [!warning] `mem2reg` does not use `DominanceFrontier`, and does not implement Cytron's frontier
> `DominanceFrontier` exists in-tree as an analysis. `mem2reg` never includes it. It calls `ForwardIDFCalculator`, whose header cites a **different paper**:
> > *"Sreedhar and Gao. **A linear time algorithm for placing phi-nodes.** POPL '95."*
> > *"It has been modified to not explicitly use the DJ graph data structure and to directly compute pruned SSA using per-variable liveness information."*
>
> So the correct pairing is: **Cytron for the skeleton** (def blocks → IDF → rename), **Sreedhar–Gao for the frontier itself**. Citing Cytron for LLVM's φ-placement algorithm is a common and specific mistake.

> [!info] The DJ-graph trick, without the DJ graph
> Sreedhar–Gao's insight is that you never need to *materialize* frontier sets. Its DJ graph has **D-edges** (dominator-tree edges) and **J-edges** (CFG edges that jump out of a subtree) — and the J-edge test is a comparison of **dominator-tree levels**.
>
> LLVM recovers both on the fly. Push every def block into a priority queue keyed on `(domtree level, DFSNumIn)`. It's a **max-heap**, so the **deepest node pops first**. Pop `Root`, walk `Root`'s entire dominator *subtree*, and inspect each node's CFG successors: a successor joins the IDF exactly when
>
> ```cpp
> if (SuccLevel > RootLevel)  continue;   // still inside Root's dominance — not a frontier
> ```
>
> i.e. `Succ.level <= Root.level` **is** the J-edge test, done arithmetically. Newly found IDF blocks that aren't already def blocks get pushed back onto the queue — that's the *iterated* part. No DJ graph is built, no frontier set is stored.

> [!tip] Why deepest-first is the load-bearing choice
> The level test is only sound because of the pop order. Processing the deepest node first guarantees that by the time you ask "is `Succ.level <= Root.level`?", every contribution from deeper subtrees has already settled. Reorder the queue and the arithmetic stops meaning what it needs to mean.
>
> The `DFSNumIn` half of the key does **no algorithmic work at all** — it breaks ties between nodes at the same level so φ insertion order, and therefore `.ll` output, is deterministic. The source says so outright.

> [!note] Pruned, always — not minimal
> `ComputeLiveInBlocks` runs for **every** alloca on the slow path, and its result is always handed to the IDF calculator, which drops any block where the φ would be dead. So `mem2reg` emits **pruned SSA unconditionally**. It does not build Cytron's minimal SSA and let DCE clean up — it declines to build the dead φs at all. The liveness itself is a **backwards worklist over predecessors** seeded from the using-blocks.

## 4. What LLVM ships — the renamer

Cytron renames by recursing over **dominator-tree children** with a **per-variable stack**. LLVM does neither.

> [!info] A CFG walk with an undo journal
> - **It walks the CFG, not the dominator tree.** `RenamePass` pushes *CFG successors* onto an explicit worklist and runs iteratively — no recursion. A `BitVector Visited`, indexed by block number, keeps each block's *body* processed once. But the φ-filling step sits **before** that early-return, so φ operands are still added on *every* incoming edge.
>
>   Why that's correct is the whole point of the IDF: if a block has no φ for a variable, then by construction the reaching definition is identical on every path into it — so whichever predecessor the DFS happens to arrive from carries the right value.
>
> - **The stack is an undo journal over a flat array.** Instead of one stack per variable, there's a flat `IncomingVals` vector indexed by alloca number, plus a journal of `(index, old_value)` pairs. Pushing a block records the journal's length; popping rewinds to it. Same stack discipline, but reading the current definition of any alloca is an O(1) indexed load rather than a stack-top lookup — and `set()` is a no-op when the value is unchanged, so the journal only grows on real changes.

> [!example]- The fast paths that skip all of the above (click to expand)
> Before any of this runs, three special cases bail out early — and they're a good reminder that the general algorithm is often not the one executing:
>
> | Case | What it does instead |
> |---|---|
> | **Dead alloca** (no uses) | erase it |
> | **Single store** | no frontier at all — just ask `DT.dominates(store, load)` per load |
> | **Used in one block only** | sort the accesses, then **binary search** for the nearest preceding store |
>
> The single-block path is the neat one: within one block the nearest preceding store *is* the reaching definition, so dominance reasoning collapses into `lower_bound` on a sorted array. Both non-trivial paths are **speculative** — they bail back to the full IDF path if their assumption breaks (a load not dominated by the store; a load before any store).

## 5. The delta

> [!summary] The one thing to remember
> `mem2reg` keeps Cytron's *skeleton* — collect def blocks, place φs at the iterated dominance frontier, rename — and replaces the content of every step:
>
> | Step | Textbook | LLVM |
> |---|---|---|
> | Frontier | Cytron's $DF$, materialized for all blocks, reusable | **Sreedhar–Gao** level walk, computed lazily per-alloca, never materialized |
> | Flavour | minimal (dead φs cleaned up later) | **pruned** (dead φs never built) |
> | Rename walk | recursion over dominator-tree children | **iterative worklist over CFG successors** |
> | Rename state | one stack per variable | **flat array + undo journal** |
>
> The through-line: a textbook optimizes for provability, a compiler optimizes for the query it actually issues. Cytron's DF is a *reusable analysis*; LLVM only ever wants the IDF of one alloca's def blocks, so it computes that and nothing else.

> [!quote] Sources & confidence
> - **Source (tier 1, verified at the version in [[llvm-version]]):** [`llvm/lib/Transforms/Utils/PromoteMemoryToRegister.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Utils/PromoteMemoryToRegister.cpp) (fast paths, `ForwardIDFCalculator` use, `ComputeLiveInBlocks`, `RenamePass`, `VectorWithUndo`) · [`llvm/include/llvm/Support/GenericIteratedDominanceFrontier.h`](https://github.com/llvm/llvm-project/blob/main/llvm/include/llvm/Support/GenericIteratedDominanceFrontier.h) (the Sreedhar–Gao citation, the priority queue, the level test) · [`llvm/include/llvm/Analysis/IteratedDominanceFrontier.h`](https://github.com/llvm/llvm-project/blob/main/llvm/include/llvm/Analysis/IteratedDominanceFrontier.h) (the `BasicBlock` specialization).
> - Sreedhar & Gao, *A Linear Time Algorithm for Placing φ-Nodes*, POPL '95 — cited **by name in LLVM's header** as the algorithm implemented.
> - Cytron, Ferrante, Rosen, Wegman, Zadeck, *Efficiently Computing Static Single Assignment Form and the Control Dependence Graph*, TOPLAS 1991 — the skeleton, minimal SSA, and the DF/renaming formulation of §2.
> - Choi, Cytron & Ferrante, *Automatic Construction of Sparse Data Flow Evaluation Graphs*, POPL '91 — pruned SSA.
> - **Note on a moved file:** IDF has been **header-only since 2019**; `llvm/lib/Analysis/IteratedDominanceFrontier.cpp` no longer exists. Any source that points you there is stale.
>
> > [!danger] Unverified — one claim deliberately not repeated
> > Sreedhar–Gao's title, and LLVM's header, both say **linear time**. Reading `calculate`, each node enters the subtree worklist at most once and is queued at most once, but the priority queue contributes log factors and the subtree walk restarts per popped root. This note therefore says **"near-linear in practice"** and does not assert the linear-time bound as verified. Checking it against the POPL '95 paper's actual cost model is open work.
