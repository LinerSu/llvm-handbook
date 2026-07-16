---
title: Mark-and-Sweep Reachability
facet: algorithm
stage: optimization
ecosystem: [general]
concepts: [dead-code, interprocedural]
book: "Dragon Book (Aho/Lam/Sethi/Ullman, 2e) §7.6.1"
docs: "doxygen — GlobalDCE ↗ https://llvm.org/doxygen/GlobalDCE_8h_source.html"
prereqs: [call-graph]
related: [interprocedural-dead-code-elimination, dead-code-elimination, devirtualization]
tags: [kind/algorithm, status/verified, version-sensitive]
status: verified
verified_on: 2026-07-16

---

# Mark-and-Sweep Reachability

> 🧭 **Algorithm** · `algorithm · optimization · general` · Index [[LLVM.MOC]] · chapter: [[Dead-Code-Elimination.MOC|Dead-Code Elimination]]
> **Powers:** `GlobalDCE` (→ [[interprocedural-dead-code-elimination]]), and the same shape underlies tracing garbage collection

> [!abstract] Chapter map
> The simplest algorithm in this folder: pick roots, mark everything reachable, delete the rest. `GlobalDCE` implements it almost exactly as written — which makes it the **counter-example** to the rest of the `algorithm/` layer. Here the algorithm survives contact with reality intact, and **all** the engineering has migrated into defining the graph: what counts as a root, and what counts as an edge. §4 is where it gets interesting.

---

## 1. The algorithm

> [!note] Definition
> Given a graph and a **root set**, **mark** every node reachable from the roots, then **sweep**: delete every unmarked node. Cost is $O(V + E)$ — each node is marked once, each edge traversed once.

> [!info] The mark phase is three lines of real work
> Seed a worklist with the roots. Pop a node, mark it, push its successors. The *entire* termination argument is the mark test:
> ```cpp
> if (!AliveGlobals.insert(&GV).second)
>   return;   // already marked — stop
> ```
> `insert().second` is false if the element was already present, so re-reaching a marked node costs one hash probe and stops. That's what makes a cyclic graph terminate.

This is textbook tracing GC, minus the moving/compaction half. `GlobalDCE`'s own header describes it in exactly those terms: *"It uses an aggressive algorithm, searching out globals that are known to be alive. After it finds all of the globals which are needed, it deletes whatever is left over."*

> [!note] It requires no analyses at all
> Not the dominator tree, not the call graph, not alias analysis — nothing. `GlobalDCE` builds its own dependency graph straight from LLVM's use-lists. This is the only pass in the audit with an empty analysis dependency set, and it's a direct consequence of the algorithm being this simple.

## 2. Building the graph — from the wrong end

> [!tip] Use-lists invert the traversal for free
> The obvious way to build "A references B" is to walk each global's initializer forward. LLVM does the opposite: it walks each global's **users** and records the edge from there. Because LLVM IR maintains **use-lists** — every `Value` knows its users — the reverse walk is free, and the forward walk would cost a traversal. Same edge set, assembled from the opposite end.
>
> `ConstantExpr` subtrees are **memoized** in a cache, since one big constant expression can be shared by many globals: *"Avoid walking the whole tree of a big ConstantExprs multiple times."* The recursion also **stops as soon as it meets a `GlobalValue`** — that's what keeps the graph at global granularity instead of instruction granularity.

## 3. The sweep is staged, and it has to be

> [!warning] You cannot mark-then-delete in one pass
> The dead set is **internally cyclic** — dead function `f` references dead global `g` which references `f`. Erase `f` while `g` still points at it and you've corrupted the module. So the sweep runs in stages: first **cut every edge** (drop dead initializers, blank dead function bodies, null out dead aliases' aliasees and ifuncs' resolvers), and only then **erase the objects**:
> > *"Now that all interferences have been dropped, delete the actual objects themselves."*
>
> Textbook mark-sweep over an abstract graph never has to say this, because deleting an abstract node has no dangling-pointer problem. Real object graphs do.

## 4. The delta — the algorithm is fine; *"reachable"* is the hard part

> [!info] Roots are a **linkage** question, not a syntactic one
> Not "is it named `main`" or "is it exported". The test is `!GV.isDiscardableIfUnused()` on globals that have a body. That's asking: *could another translation unit reference this?* A `linkonce_odr` function is discardable; an `external` one isn't. The root set is decided by the **linker's** model, and getting it wrong doesn't produce slow code — it produces undefined symbols at link time.

> [!warning] Comdats make liveness all-or-nothing
> Marking any member of a comdat group marks **every** member:
> ```cpp
> if (Comdat *C = GV.getComdat())
>   for (auto &&CM : make_range(ComdatMembers.equal_range(C)))
>     MarkLive(*CM.second, Updates);   // recursion depth is only two
> ```
> A comdat group is the linker's **atomic unit** — split it and you get undefined symbols. So liveness isn't per-object, it's per-partition. (The recursion terminates at depth two: the nested calls find themselves already in the mark set and return.) This is a *correctness* constraint, not an optimization.

> [!tip] Virtual Function Elimination — deliberately deleting real edges
> Here's the sharpest twist. A vtable references **every** virtual function in the class. So plain reachability keeps every virtual function alive forever, and is therefore *sound but useless* for C++.
>
> VFE's answer is to **suppress an edge that genuinely exists**:
> ```cpp
> if (VFESafeVTables.count(GVU) && isa<Function>(&GV)) {
>   // If this is a dep from a vtable to a virtual function, and we have
>   // complete information about all virtual call sites which could call
>   // though this vtable, then skip it, because the call site information will
>   // be more precise.
>   continue;
> }
> ```
> and replace it with **precise call-site → function edges** recovered from `llvm.type.checked.load` intrinsics, whose constant offsets identify the exact slot. The soundness gate is whole-program visibility: a vtable is VFE-safe only when its `VCallVisibility` proves LLVM can see *every* virtual call site. Any call with a **non-constant offset** revokes safety for every matching vtable — bail out and keep them all alive.
>
> This is the general lesson in miniature: the *algorithm* is textbook, but making it useful required a whole-program soundness argument about which edges are real.

> [!note] Dead ≠ use-empty
> A dead virtual function is still *pointed at* by its vtable slot, so it isn't use-empty and can't simply be erased. GlobalDCE **nulls the slot** rather than declining to delete. Textbook reachability has no analogue — there, unreachable means deletable, full stop.

> [!summary] The one thing to remember
> Mark-and-sweep is the one algorithm in this folder that ships essentially unmodified — and that's precisely why it's instructive. All the difficulty moved into the **graph definition**: roots are a linkage property, comdats force liveness to be a set-partition, and C++ vtables require deliberately deleting true edges and rebuilding precise ones. When the algorithm is trivial, the modelling is where the work is.

> [!quote] Sources & confidence
> - **Source (tier 1):** Quoted text was verified against the **tag** in [[llvm-version]]. The links below track `main` for navigation — this vault deliberately does not hardcode release numbers in content notes — so `main` may since have drifted from what is quoted here; re-verify against the tag, not `main`. [`llvm/lib/Transforms/IPO/GlobalDCE.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/IPO/GlobalDCE.cpp) (`MarkLive`, the worklist, the root set, the staged sweep, comdats, `AddVirtualFunctionDependencies`, `ScanVTables`) · [`llvm/include/llvm/Transforms/IPO/GlobalDCE.h`](https://github.com/llvm/llvm-project/blob/main/llvm/include/llvm/Transforms/IPO/GlobalDCE.h) (`AliveGlobals`, `GVDependencies`, `VFESafeVTables`). Code and comments quoted above are verbatim.
> - **Note on a stale in-tree comment:** `GlobalDCE.cpp`'s `run()` describes building the dependency graph *forward* by walking initializers; the implementation builds it *backward* from use-lists (§2). The edge set is equivalent — the comment describes the wrong end. Verified against the code at the pinned version, not against git history.
> - Dragon Book §7.6.1 — mark-and-sweep garbage collection, the same algorithm in its original setting.
