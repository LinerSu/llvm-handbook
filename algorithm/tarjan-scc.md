---
title: Tarjan's SCC Algorithm
facet: algorithm
stage: analysis
ecosystem: [general]
concepts: [call-graph, interprocedural, control-flow]
book: "Dragon Book (Aho/Lam/Sethi/Ullman, 2e) §12.2"
docs: "doxygen — LazyCallGraph ↗ https://llvm.org/doxygen/classllvm_1_1LazyCallGraph.html"
prereqs: [call-graph]
related: [call-graph, inlining, loop-info]
tags: [kind/algorithm, status/verified, version-sensitive]
status: verified
verified_on: 2026-07-16
---

# Tarjan's SCC Algorithm

> 🧭 **Algorithm** · `algorithm · analysis · general` · Index [[LLVM.MOC]] · see also [[dragon-book-ch12.MOC|Dragon Ch.12]]
> **Powers:** [[call-graph|LazyCallGraph / CGSCC]] — and therefore [[inlining]] and every interprocedural pass
> **Prerequisites:** [[call-graph]]

> [!abstract] Chapter map
> You know what a strongly-connected component is; this is how you find them in one DFS, and — more interestingly — what happens when the graph **mutates while you're still walking it**. LLVM names Tarjan in-source and implements it faithfully. Then [[inlining|the inliner]] rewrites the call graph mid-traversal, and everything interesting in §5 follows from the fact that re-running Tarjan is not an option.

---

## 1. Why a compiler wants SCCs

> [!note] Definition
> A **strongly connected component** of a directed graph is a maximal set of nodes where every node reaches every other. Contract each SCC to a single node and you get the **condensation** — which is always a **DAG**, and therefore topologically orderable.

That last sentence is the entire reason compilers care. [[inlining|The inliner]] wants to process **callees before callers**, so each callee is already simplified when its callers are considered. "Callees first" is a topological order — but a call graph with mutual recursion **has cycles**, and cyclic graphs have no topological order. Condensing SCCs is what makes "bottom-up" well-defined: you can't order `a → b → a`, but you *can* order the single node `{a, b}` against everything else.

## 2. The algorithm

> [!info] One DFS, two numbers, one stack
> Tarjan assigns each node a **DFS number** (when first visited) and a **lowlink** (the smallest DFS number reachable from its subtree, including via one back-edge). Nodes go on a stack as they're visited and stay there until their component is complete.
>
> - On visiting a child for the first time: recurse, then `low[v] = min(low[v], low[child])`.
> - On meeting a child **already on the stack**: `low[v] = min(low[v], dfs[child])`.
> - On meeting a child in an **already-finished** component: ignore it.
> - After exhausting `v`'s edges: if `low[v] == dfs[v]`, then `v` is the **root** of an SCC — pop the stack down to `v`, and everything popped is the component.

> [!tip] The intuition
> `low[v] == dfs[v]` means "nothing in my subtree found a way back above me". If something had, my lowlink would have been dragged down below my own number. So a node whose lowlink never moved is the highest node of its cycle — the entry point of the component.

Cost is $O(V + E)$: one DFS, each edge inspected once. Components come out in **reverse topological order** of the condensation — which is exactly the bottom-up order the inliner wants, for free.

## 3. What LLVM ships — faithful, and it says so

> [!info] Named in-source
> `LazyCallGraph`'s shared SCC driver is documented as exactly what it is:
> > *"Currently this is a relatively naive implementation of **Tarjan's DFS algorithm** to form the SCCs. FIXME: We should consider newer variants such as **Nuutila**."*
>
> And the bookkeeping lives on the node, under its textbook name:
> ```cpp
> // We provide for the DFS numbering and Tarjan walk lowlink numbers to be
> // stored directly within the node.
> int DFSNumber = 0;
> int LowLink = 0;
> ```

All three textbook pieces are present in `buildGenericSCCs`: an explicit **DFS stack** (pairing each node with its in-progress edge iterator, since Tarjan is recursive on paper), a **pending stack** (Tarjan's `S`), and the root test `if (N->LowLink != N->DFSNumber) continue;`.

> [!example] The one quiet deviation — a sentinel instead of a bit
> Tarjan needs an `onStack` predicate to distinguish "child is on the stack" (a real back-edge, drag the lowlink down) from "child is in a finished component" (ignore it). Textbooks carry a boolean per node. LLVM carries none — it overloads the two integers with three states:
>
> | `DFSNumber` | Meaning |
> |---|---|
> | `0` | not yet visited |
> | `> 0` | visited, still on the stack |
> | `-1` | already assigned to a finished component |
>
> so the "ignore it" guard is just `if (ChildN.DFSNumber == -1) continue;`, and assigning `-1` is what *removes* a node from the stack. Same algorithm, one less field per node — which matters when the node count is "every function in the module".

## 4. Two graphs in a trench coat — SCC vs RefSCC

> [!warning] LLVM does not have one call graph; it has two nested ones
> - An **SCC** is a strongly-connected component of **call edges** — the classic call-graph SCC, and the unit CGSCC passes run on.
> - A **RefSCC** is a strongly-connected component of **reference edges** — a strict superset, since *"all call edges are inherently reference edges, and so the reference graph forms a superset of the formal call graph"*. Each RefSCC contains a **DAG of SCCs**.

Why carry both? Because **a ref edge is a call edge that hasn't happened yet.** The graph deliberately models *"direct call edges that might be formed through static optimizations. Specifically, it considers taking the address of a function to be an edge in the call graph because this might be forwarded to become a direct call."*

Suppose you only tracked calls. A function pass turns `store @f, %p` … `%fn = load %p` … `call %fn` into `call @f`. A **brand-new call edge** appears out of nowhere, in a graph whose bottom-up order you are halfway through consuming — and that order is now wrong. Tracking the *reference* up front makes that same event a **promotion inside a region you already knew was connected**, not a new edge. LLVM enforces this with an assertion:

> *"No function transformations should introduce \*new\* call edges! Any new calls should be modeled as promoted existing ref edges!"*

So the division of labour is: **RefSCC is the mutation scope** (the boundary no local optimization can reach past), **SCC is the optimization scope** (finer, so more precise and more parallel). Same Tarjan, two edge subsets, nested — `buildGenericSCCs` is templated on the edge iterators precisely so it can be run twice.

## 5. The delta — Tarjan has no incremental form

> [!tip] The constraint that drives everything
> Tarjan is **batch**: mutate the graph, re-run, $O(V+E)$, get fresh numbers. LLVM cannot do that. The header states the invariant it must preserve:
> > *"no optimizations will delete, remove, or add an edge such that functions already visited in a bottom-up order of the SCC DAG are no longer valid to have visited."*
>
> Re-running Tarjan would renumber every node and destroy the in-progress traversal that the inliner is *currently iterating*. So LLVM ships **incremental repair operations** instead — and they are not Tarjan at all.

> [!info] Edge insertion — a different algorithm entirely
> No DFS, no lowlinks. Postorder means callees precede callers, so:
> 1. **O(1) early out.** If the target already sits *earlier* in the postorder than the source, the edge flows the way everything already flows and cannot close a cycle. Done. This is the common case.
> 2. Otherwise, two bounded searches — what reaches the source, what the target reaches — both **clamped to the window `[SourceIdx, TargetIdx]`**. Nothing outside is touched, so cost tracks the disorder introduced, not the graph size.
> 3. Reorder with two `std::stable_partition`s. Stability is load-bearing: it preserves postorder among the members that didn't move.
> 4. If the target turns out to reach back to the source, the surviving window **is** the new cycle. Merge it.

> [!example] Edge removal — Tarjan, but with a shortcut it isn't allowed to have
> Demoting a call edge to a ref edge inside one SCC may shatter the cycle, so here LLVM *does* return to a DFS — scoped to the old SCC's nodes only. And then it exploits an invariant no general graph library has:
> > *"This also enables us to take a very significant short-cut in the standard Tarjan walk to re-form SCCs below: whenever we build an edge that reaches the target node, we know that the target node eventually connects back to all other nodes in our walk."*
>
> Because the component **was an SCC a moment ago**, reaching the target is *proof of membership* — no lowlink propagation needed. On touching it, LLVM dumps the entire DFS and pending stacks straight into the old SCC and restarts. Textbook Tarjan would have to walk the return path edge by edge to propagate the lowlink. This is a domain fact, not a graph fact, and it's exactly why you can't lift this code into a generic library.

> [!note] The name is half-earned
> `LazyCallGraph` is lazy about **node population** — no function body is scanned until the walk first reaches it. It is **not** lazy about RefSCC formation: `buildRefSCCs()` does one batch DFS and forms *every* RefSCC eagerly, and the iterators assert the walk is already complete. A comment in the CGSCC pass manager still claims RefSCCs are *"lazily constructed"* — that comment is false as of the version in [[llvm-version]], since `buildRefSCCs()` runs on the preceding line. Read `Lazy` as "lazy population, eager components".

> [!summary] The one thing to remember
> Building the graph is textbook Tarjan. **Maintaining** it isn't Tarjan at all — because the inliner mutates the call graph while consuming the very postorder Tarjan produced, LLVM replaces "re-run the batch algorithm" with bounded, in-place repair: an O(1) order test, a windowed reorder for insertions, and a scoped re-walk for removals. The textbook gives you the algorithm; shipping code needs the algorithm *plus an incremental form the paper never defined*.

> [!quote] Sources & confidence
> - **Source (tier 1, verified at the version in [[llvm-version]]):** [`llvm/include/llvm/Analysis/LazyCallGraph.h`](https://github.com/llvm/llvm-project/blob/main/llvm/include/llvm/Analysis/LazyCallGraph.h) (the Tarjan/Nuutila comment, `DFSNumber`/`LowLink`, the SCC vs RefSCC definitions, the bottom-up invariant) · [`llvm/lib/Analysis/LazyCallGraph.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Analysis/LazyCallGraph.cpp) (`buildGenericSCCs`, the `-1` sentinel, `updatePostorderSequenceForEdgeInsertion`, the removal short-cut) · [`llvm/lib/Analysis/CGSCCPassManager.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Analysis/CGSCCPassManager.cpp) (the new-call-edge assertion; also the stale laziness comment noted in §5). Quotes above are verbatim from these files.
> - Tarjan, *Depth-First Search and Linear Graph Algorithms*, SIAM J. Computing 1972 — the algorithm of §2; named in LLVM's header.
> - Nuutila & Soisalon-Soininen, *On Finding the Strongly Connected Components in a Directed Graph*, 1994 — named in LLVM's `FIXME` as the variant not yet adopted.
>
> > [!danger] Unverified — an attribution this vault is making, not LLVM
> > The edge-insertion repair in §5 is *structurally* the **Pearce–Kelly** dynamic topological sort (2006): affected region bounded by the two endpoints' ordinals, two-way bounded search, in-place reorder. **LLVM never names Pearce, Kelly, or "dynamic topological sort" anywhere** — unlike Tarjan and Nuutila, which it does name. Treat this as a shape-match observed by this vault, not a citation, and don't put it in LLVM's mouth. Confirming it against the 2006 paper's exact variant is open work.
