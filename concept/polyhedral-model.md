---
title: The Polyhedral Model (Polly)
facet: concept
stage: optimization
ecosystem: [llvm, polly]
concepts: [polyhedral, loop-optimization]
implements:
  - { ecosystem: polly, src: "polly/ (LLVM subproject)" }
docs: "Polly ↗ https://polly.llvm.org/"
book: "Dragon Book (Aho/Lam/Sethi/Ullman, 2e) §11"
prereqs: [loop-info, scalar-evolution]
related: [dependence-analysis, loop-transformations]
tags: [kind/concept, status/verified]
status: verified
verified_on: 2026-06-28
---

# The Polyhedral Model (Polly)

> 🧭 **Concept** · `concept · optimization · llvm+polly` · Index [[LLVM.MOC]] · see also [[dragon-book-ch11.MOC|Dragon Ch.11]]
> **Prerequisites:** [[loop-info]], [[scalar-evolution]] · **Legality from:** [[dependence-analysis]]

> [!abstract] Chapter map
> When a loop nest has **affine** bounds and array indexes, its iterations form an integer **polyhedron** (a *polytope* of index points). Representing loops this way turns transformations — tiling, interchange, fusion, skewing — into **affine changes of the iteration schedule**, chosen to improve **locality and parallelism**. In LLVM this is **Polly**.

> [!info] The model
> - **Iteration space** — the set of executed index vectors `(i, j, …)`, bounded by affine inequalities (a polytope).
> - **Affine array index** — each access is an affine function of the loop indices, e.g. `A[2i + j]`.
> - **Schedule** — an affine map assigning each iteration a logical time; a *transformation* is just a different (legal) schedule.
> - **Legality** — a new schedule is legal iff it preserves all array **dependences** ([[dependence-analysis]]).

---

## 1. Why it helps — locality via tiling

The canonical example is matrix multiply. Naively it streams whole rows/columns and thrashes the cache:
```c
for (i=0;i<N;i++) for (j=0;j<N;j++) for (k=0;k<N;k++)
  C[i][j] += A[i][k] * B[k][j];
```
**Tiling** (a.k.a. blocking) restructures the iteration space into cache-sized blocks so reused data stays hot:
```c
for (ii=0;ii<N;ii+=T) for (jj=0;jj<N;jj+=T) for (kk=0;kk<N;kk+=T)
  for (i=ii;i<ii+T;i++) for (j=jj;j<jj+T;j++) for (k=kk;k<kk+T;k++)
    C[i][j] += A[i][k] * B[k][j];
```
In the polyhedral model, tiling is one affine reshaping of the iteration polytope — composed freely with interchange, fusion, and skewing.

## 2. In LLVM — Polly

> [!info] What Polly is
> **Polly** is LLVM's in-tree **polyhedral loop optimizer** (a subproject). It detects **SCoPs** (*Static Control Parts* — loop nests with affine bounds/indexes and no side effects), lifts them to a polyhedral representation backed by **ISL** (the Integer Set Library), applies polyhedral **tiling / fusion / interchange / vectorization / parallelization**, and regenerates LLVM IR. It builds on [[scalar-evolution|SCEV]] (to recover affine index functions) and [[dependence-analysis|dependence info]] (for legality).

## 3. Limits & reality

> [!warning] Affine-only, and not in the default pipeline
> The model applies **only to affine** loop nests (SCoPs); data-dependent bounds, pointer chasing, and irregular control fall outside it. Polly is **not in the default `-O2/-O3` pipeline** — it's opt-in (`-O3 -mllvm -polly`). In practice most of LLVM's locality/parallelism wins come from the simpler loop passes and the **vectorizer** ([[loop-transformations]]); Polly is the heavyweight option when affine restructuring pays off. This is also the bridge to your relational numerical domains — **polyhedra** as an abstract domain show up here as the iteration-space representation.

> [!summary] The one thing to remember
> Affine loop nests are integer polyhedra; transformations are affine reschedulings chosen for locality + parallelism, legal iff they preserve [[dependence-analysis|dependences]]. LLVM's realization is **Polly** (ISL-backed, on SCoPs), opt-in rather than default.

> [!quote] Further reading
> - **Source:** [`polly/`](https://github.com/llvm/llvm-project/tree/main/polly) (LLVM subproject)
> - **Dragon Book §11** — iteration spaces, affine array indexes, locality optimizations, affine transforms.
> - [Polly — polyhedral optimization in LLVM](https://polly.llvm.org/).
