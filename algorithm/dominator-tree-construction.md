---
title: Dominator Tree Construction (Semi-NCA)
facet: algorithm
stage: analysis
ecosystem: [general]
concepts: [dominance, control-flow]
book: "Dragon Book (Aho/Lam/Sethi/Ullman, 2e) §9.6.1"
docs: "doxygen — DominatorTreeBase ↗ https://llvm.org/doxygen/classllvm_1_1DominatorTreeBase.html"
prereqs: [control-flow-graph]
related: [dominator-tree, ssa-construction, ssa-form]
tags: [kind/algorithm, status/verified, version-sensitive]
status: verified
verified_on: 2026-07-16
---

# Dominator Tree Construction (Semi-NCA)

> 🧭 **Algorithm** · `algorithm · analysis · general` · Index [[LLVM.MOC]] · see also [[dragon-book-ch9.MOC|Dragon Ch.9]]
> **Powers:** [[dominator-tree]] — and through it [[ssa-construction]], [[mem2reg]], [[loop-info]], every dominance query in the middle-end

> [!abstract] Chapter map
> You know *what* a dominator tree is ([[dominator-tree]]); this note is *how you build one*. Three methods, in the order the field found them: the dataflow fixpoint (obvious, slow), **Lengauer–Tarjan** (the classic near-linear answer), and **Semi-NCA** — which is what LLVM actually ships despite being **asymptotically worse**. That last sentence is the interesting part, and §5 explains why a real compiler makes that trade.

---

## 1. The problem

> [!note] Definition
> Given a CFG with entry $r$, compute $idom(B)$ for every block $B$ reachable from $r$ — the unique strict dominator of $B$ closest to it. The parent-pointer array $idom[\cdot]$ *is* the [[dominator-tree|dominator tree]].

Everything downstream wants the tree, not the dominance *sets*: [[mem2reg]] wants dominance frontiers, [[loop-invariant-code-motion|LICM]] wants "does this dominate every exit", [[early-cse]] wants to walk it. So an algorithm that produces $idom$ directly beats one that produces sets you must post-process.

## 2. Method 0 — the dataflow fixpoint

> [!info] The obvious way
> Dominance is a [[data-flow-analysis|forward dataflow problem]] over the lattice of block-sets, meet = intersection:
> $$Dom(r) = \{r\} \qquad Dom(B) = \{B\} \cup \bigcap_{p \in pred(B)} Dom(p)$$
> Initialize every non-entry block to "all blocks", iterate in [[data-flow-analysis|RPO]] to a fixpoint. Then recover $idom(B)$ as the unique member of $Dom(B) \setminus \{B\}$ with the largest $Dom$ set.

It's correct, it's ten lines with bitvectors, and it's what most courses teach first. Two things sink it in a real compiler: the sets cost $O(n)$ space *per block* ($O(n^2)$ total), and you pay a fixpoint iteration to compute something the next two methods get in essentially one DFS plus one pass. It survives as a teaching device and as the basis of Cooper–Harvey–Kennedy's "simple, fast" variant, which iterates on $idom$ pointers directly instead of sets.

## 3. Lengauer–Tarjan — the semidominator idea

The 1979 breakthrough was finding a computable *approximation* of $idom$ that you can then correct.

> [!note] Definition — semidominator
> DFS the CFG from $r$, numbering each node. The **semidominator** $sdom(w)$ is the minimum-numbered vertex $v$ from which there is a path $v = v_0 \to v_1 \to \cdots \to v_k = w$ where every *intermediate* $v_i$ has a DFS number **greater than** $w$'s.

> [!tip] The intuition
> $sdom(w)$ is the highest place in the DFS tree you can start and still "sneak down" to $w$ through nodes DFS visited *after* $w$ — i.e. through a detour that the DFS tree itself doesn't show. It is a **candidate** for $idom(w)$, and crucially a **bound**: $idom(w)$ is always an ancestor of (or equal to) $sdom(w)$, and $sdom(w)$ is always a proper ancestor of $w$. So the true answer lies on the DFS-tree path between the root and $sdom(w)$ — a much smaller search than "any block".

LT then runs two phases:

1. **Semidominators**, walking DFS numbers **downward**, using an `eval`/`link` structure with **path compression** over a "virtual forest" to compute each $sdom$ in near-constant amortized time.
2. **Immediate dominators**, via *buckets*: each $w$ is parked in $sdom(w)$'s bucket, and when the DFS retreats past that node the parked entries are resolved, sometimes only as a **deferred** relative answer (`idom(w) = idom(u)`) that a final pass must fix up.

Complexity: $O(m \log n)$ with simple path compression, $O(m \, \alpha(m,n))$ with balanced linking. This is the "near-linear dominators" result the textbooks cite.

## 4. Semi-NCA — what LLVM ships

> [!warning] LLVM does **not** run Lengauer–Tarjan
> `llvm/include/llvm/Support/GenericDomTreeConstruction.h` implements **Semi-NCA (SNCA)**, from Georgiadis's dissertation. Its own header comment states the trade outright:
> > *"Semi-NCA algorithm runs in **O(n^2) worst-case time** but usually slightly faster than Simple Lengauer-Tarjan in practice. O(n^2) worst cases happen when the computation of nearest common ancestors requires O(n) average time, which is very unlikely in real world."*

SNCA **keeps LT's phase 1 verbatim** and **throws away LT's phase 2**. Instead of buckets and deferred fix-ups, it computes each immediate dominator as a nearest common ancestor. LLVM's `runSemiNCA` says so in the code itself:

```cpp
// Step #2: Explicitly define the immediate dominator of each vertex.
//          IDom[i] = NCA(SDom[i], SpanningTreeParent(i)).
```

> [!info] How the NCA step works
> `IDom` is pre-seeded with each node's **DFS spanning-tree parent**. Phase 2 then sweeps DFS numbers **upward** — so by the time it reaches $w$, every ancestor of $w$'s parent already holds its *final* idom. It walks up that finished chain until it drops to or below $sdom(w)$'s DFS number:
>
> ```cpp
> NodePtr WIDomCandidate = WInfo.IDom;
> while (true) {
>   auto &WIDomCandidateInfo = getNodeInfo(WIDomCandidate);
>   if (WIDomCandidateInfo.DFSNum <= SDomNum)
>     break;
>   WIDomCandidate = WIDomCandidateInfo.IDom;
> }
> WInfo.IDom = WIDomCandidate;
> ```
>
> That `while (true)` is the whole difference. It is unbounded — a single node can walk $O(n)$ links — which is precisely where the $O(n^2)$ comes from. No buckets, no deferred fix-up pass, no final correction sweep: when the loop breaks, the answer is final.

> [!example]- The two phases side by side (click to expand)
> **Phase 1 — semidominators, DFS numbers descending.** Note `Semi` starts at the spanning-tree parent and is lowered by each incoming edge, and that `eval` is where path compression lives:
> ```cpp
> for (unsigned i = NextDFSNum - 1; i >= 2; --i) {
>   auto &WInfo = *NumToInfo[i];
>   WInfo.Semi = WInfo.Parent;
>   for (unsigned N : WInfo.ReverseChildren) {
>     unsigned SemiU = NumToInfo[eval(N, i + 1, EvalStack, NumToInfo)]->Semi;
>     if (SemiU < WInfo.Semi) WInfo.Semi = SemiU;
>   }
> }
> ```
> **Phase 2 — idoms, DFS numbers ascending** (the NCA walk quoted above). The `for` runs `i = 2` upward, which is what makes "the chain above me is already final" true.
>
> `eval` itself is LT's, unchanged: it stacks the ancestors, then re-points every `Parent` straight at the virtual-tree root while carrying the minimum-`Semi` `Label` down — textbook path compression.

> [!note] Per-node state
> One `InfoRec` per block: `DFSNum`, `Semi`, `Label`, `Parent`, `IDom`, `ReverseChildren`. Flat arrays (`NumToNode`, `NumToInfo`) indexed by DFS number, not maps — the DFS numbering *is* the index, which is half the reason this is fast in practice despite the quadratic bound.

## 5. Why ship the asymptotically worse algorithm?

> [!tip] The delta — and the real reason
> Two reasons, and the second is the one that matters.
>
> **Constant factors.** The $O(n^2)$ needs a pathological CFG where NCA chains are long; real control flow is shallow, so the walk almost always breaks after a step or two. Meanwhile SNCA drops LT's buckets and fix-up pass entirely, so it does strictly less bookkeeping per node. Asymptotically worse, empirically faster — the header says as much.
>
> **Incrementality.** This is the decisive one. LLVM does not build a dominator tree once; it builds one and then *hundreds of passes mutate the CFG underneath it*. [[simplifycfg|SimplifyCFG]] deletes blocks, [[jump-threading|JumpThreading]] redirects edges, [[inlining|the inliner]] splices whole function bodies in. Recomputing from scratch after each edit would dwarf any phase-1 asymptotics. SNCA's phase 2 is a **local walk over a chain of final answers**, which makes it far easier to re-run on a *sub*tree than LT's global bucket phase — the tree is patched, not rebuilt. `InsertEdge` / `DeleteEdge` / `ApplyUpdates` implement that patching with a **Depth Based Search**, citing Georgiadis et al., *An Experimental Study of Dynamic Dominators* (2016).

> [!info] Where you see this from the outside
> `DomTreeUpdater` is the API through which passes announce CFG edits; it batches them and lets the tree (and `PostDominatorTree`) absorb updates lazily. A pass that declares `PreservedAnalyses` including the dominator tree is promising it used that channel — which is why "does this pass preserve the DomTree?" is a real review question in LLVM, not a formality.

> [!summary] The one thing to remember
> LT's phase 1 (semidominators + path compression) is *kept*; LT's phase 2 (buckets + deferred fix-up) is *replaced* by "walk up the already-final idom chain until you reach $sdom$". That swap trades a worst-case guarantee nobody hits for code that is simpler, faster in practice, and — the actual point — **incrementally updatable**.

> [!quote] Sources & confidence
> - **Source (tier 1, verified at the version in [[llvm-version]]):** [`llvm/include/llvm/Support/GenericDomTreeConstruction.h`](https://github.com/llvm/llvm-project/blob/main/llvm/include/llvm/Support/GenericDomTreeConstruction.h) — file-header comment (algorithm choice + complexity), `runSemiNCA` (both phases), `eval` (path compression), `InsertEdge`/`DeleteEdge`/`ApplyUpdates` (incremental). Code quoted above is verbatim from this file.
> - Georgiadis, *Linear-Time Algorithms for Dominators and Related Problems*, Princeton dissertation, Nov 2005, pp. 21–23 — the Semi-NCA algorithm, cited by name in LLVM's header.
> - Georgiadis et al., *An Experimental Study of Dynamic Dominators*, 2016, pp. 5–7, 9–10 — the Depth Based Search incremental algorithm, cited by name in LLVM's header.
> - Lengauer & Tarjan, *A Fast Algorithm for Finding Dominators in a Flowgraph*, TOPLAS 1979 — phases 1 and 2 as described in §3.
> - Cooper, Harvey & Kennedy, *A Simple, Fast Dominance Algorithm*, 2001 — the iterate-on-idom-pointers variant mentioned in §2.
> - **Also in:** Muchnick *Advanced Compiler Design & Impl.* §7 — control-flow analysis.
