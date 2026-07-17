---
title: Graph-Coloring Register Allocation
facet: algorithm
stage: codegen
ecosystem: [general]
concepts: [register-allocation]
book: "Dragon Book (Aho/Lam/Sethi/Ullman, 2e) §8.8"
docs: "CodeGenerator — register allocation ↗ https://llvm.org/docs/CodeGenerator.html"
prereqs: [control-flow-graph]
related: [register-allocation, data-flow-analysis, ssa-form]
tags: [kind/algorithm, status/verified]
status: verified
verified_on: 2026-07-16
---

# Graph-Coloring Register Allocation

> 🧭 **Algorithm** · `algorithm · codegen · general` · Index [[LLVM.MOC]] · see also [[dragon-book-ch8.MOC|Dragon Ch.8]]
> **Powers:** the *textbook* half of [[register-allocation]] — which is exactly the half LLVM **doesn't** ship

> [!abstract] Chapter map
> The classical answer to "which values live in which registers": build an interference graph, color it with $k$ colors, spill what won't fit. This note is the algorithm itself — Chaitin's build/simplify/select loop and Briggs's optimistic fix. [[register-allocation]] already documents what LLVM ships **instead**; the contrast only lands once you've seen the original, which is what this note is for.

---

## 1. The reduction

> [!note] Definition
> Two values **interfere** if their live ranges overlap — they cannot share a register. Build the **interference graph**: one node per value, one edge per interfering pair. Assigning $k$ physical registers is then exactly **$k$-coloring** the graph: adjacent nodes get different colors.

> [!warning] The bad news, and why the heuristic exists
> Chaitin proved graph coloring register allocation is **NP-complete**, by showing that *every* graph is the interference graph of some program — so a polynomial allocator would polynomially color arbitrary graphs. There is no efficient exact algorithm to find. Everything below is heuristic, and that's forced, not lazy.

## 2. Chaitin's algorithm

> [!info] Kempe's rule — the one idea
> A node with **fewer than $k$ neighbors** can *always* be colored, no matter what happens elsewhere: color everything else first, and at most $k-1$ colors are taken, so one remains. So such a node is **not the problem** — remove it and solve the smaller graph.

That gives the loop:

1. **Build** the interference graph from live ranges.
2. **Coalesce** — if a `mov a, b` connects two *non*-interfering nodes, merge them; the copy disappears. (Merging raises degree, so aggressive coalescing can make the graph harder to color — hence *conservative* coalescing, which merges only when provably safe.)
3. **Simplify** — repeatedly push any node with degree $< k$ onto a stack and remove it from the graph.
4. **Spill** — if every remaining node has degree $\ge k$, pick one by a cost heuristic (spill cost ÷ degree, roughly "cheap to spill and relieves a lot of pressure"), mark it spilled, remove it, and go back to 3.
5. **Select** — pop the stack, giving each node a color not used by its (already-colored) neighbors.

> [!tip] Briggs's optimistic coloring — the important refinement
> Chaitin spills a node the moment its degree hits $k$. But degree $\ge k$ only means it *might* not be colorable — its neighbors may share colors. **Briggs**: push it on the stack anyway and find out at select time. Often it colors fine. Only if select genuinely runs out of colors does it become an *actual* spill. This one change — defer the decision until you have the information — measurably reduces spilling, and it is the single most quoted improvement to Chaitin.

> [!example] Why $k$ matters more than the graph
> The same interference graph is trivially colorable on a 32-register RISC and hopeless on x86's handful of general-purpose registers. Register allocation difficulty is a property of the **pair** (graph, $k$), which is why the algorithm's shape barely changes between targets but its outcome changes completely.

## 3. The other classic — linear scan

> [!info] Trade optimality for speed
> Poletto & Sarkar's **linear scan** abandons the graph entirely: flatten the code, treat each live range as an *interval*, sweep left to right keeping an active list, and when more than $k$ intervals are live, evict the one ending furthest away. No graph is built, so it's near-linear. Far worse code, far faster compile — which is why it's the classic choice for JITs and `-O0`.

That framing — *the interference graph is expensive, and maybe you don't need it* — is the thread LLVM pulls on.

## 4. What LLVM does instead

> [!warning] LLVM ships neither Chaitin nor plain linear scan
> Its default allocator, **Greedy**, never builds an interference graph. It works on `LiveIntervals`, checks interference against per-register live-interval unions, and treats allocation as a **priority queue with eviction and live-range splitting** — the key move being that a range that won't fit can be *split* rather than spilled wholesale. LLVM chose this over Chaitin-style coloring because the interference graph is expensive and **spill/split placement matters more than optimal coloring**.
>
> That story — including the allocator table, the eviction/splitting refinement loop, and PBQP as the graph-based opt-in — is already told in **[[register-allocation]] §2**, and isn't repeated here.

> [!note] A theory footnote worth knowing
> Chaitin's NP-completeness result is about *arbitrary* programs. If the program is in **SSA form**, its interference graph is **chordal**, and chordal graphs are optimally colorable in polynomial time. So SSA-based allocation can, in principle, escape the hardness result — the difficulty migrates into φ-elimination and spilling instead of coloring. This is why "allocate before or after leaving SSA?" is a live design question rather than a settled one.

> [!summary] The one thing to remember
> Chaitin gives you a clean reduction (allocation *is* coloring), a hard theorem (it's NP-complete), and a good heuristic (Kempe's rule + optimistic coloring). LLVM keeps the *problem statement* and throws away the *reduction* — because the graph is expensive to build and, once you can split live ranges, coloring was never the expensive decision. **Where you spill is worth more than how well you color.**

> [!quote] Sources & confidence
> - Chaitin et al., *Register Allocation via Coloring*, Computer Languages 1981; Chaitin, *Register Allocation and Spilling via Graph Coloring*, SIGPLAN 1982 — the algorithm of §2 and the NP-completeness reduction.
> - Briggs, Cooper & Torczon, *Improvements to Graph Coloring Register Allocation*, TOPLAS 1994 — optimistic coloring and conservative coalescing.
> - Poletto & Sarkar, *Linear Scan Register Allocation*, TOPLAS 1999 — §3.
> - Hack & Goos, *Optimal Register Allocation for SSA-form Programs in Polynomial Time*, IPL 2006; Bouchez, Darte, Rastello, *On the Complexity of Register Coalescing*, CGO 2007; Pereira & Palsberg, *Register Allocation via Coloring of Chordal Graphs*, APLAS 2005 — the chordality footnote.
> - **Also in:** Muchnick *Advanced Compiler Design & Impl.* §16 — register allocation.
> - **LLVM's side of the contrast** is documented and verified in [[register-allocation]]; this note deliberately does not duplicate or re-verify it.
