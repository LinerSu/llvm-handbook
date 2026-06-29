---
title: Data-Flow Analysis
facet: concept
stage: analysis
ecosystem: [general, llvm, mlir]
concepts: [dataflow-analysis]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/Scalar/SCCP.cpp" }
  - { ecosystem: llvm, src: "llvm/include/llvm/Analysis/SparsePropagation.h" }
  - { ecosystem: mlir, src: "mlir/include/mlir/Analysis/DataFlow/" }
docs: "doxygen — SparsePropagation ↗ https://llvm.org/doxygen/SparsePropagation_8h_source.html"
prereqs: [control-flow-graph]
related: [value-numbering, pointer-alias-analysis, dominator-tree, lazy-value-info]
tags: [kind/analysis, status/verified]
status: verified
verified_on: 2026-06-28
---

# Data-Flow Analysis

> 🧭 **Concept** · `concept · analysis · general+llvm+mlir` · Index [[LLVM.MOC]]
> **Prerequisites:** [[control-flow-graph]] · **Feeds:** [[value-numbering]], [[pointer-alias-analysis]] · **On-demand ranges:** [[lazy-value-info]]

> [!abstract] Chapter map
> The program-analysis backbone, as the arc *theory → algorithm → LLVM/MLIR → use → frontier*: a monotone-framework definition, the worklist that solves it, how LLVM and MLIR realize it, where it pays off, and where it runs out of road.

> [!info]+ From classic compiler theory → LLVM/MLIR
> | Classic concept | Realization |
> |---|---|
> | Monotone dataflow framework (Kildall) | iterate transfer functions to a fixpoint over the [[control-flow-graph|CFG]] |
> | Sparse constant lattice | **SCCP** (`Transforms/Scalar/SCCP.cpp`) |
> | Generic *sparse* solver | `AbstractLatticeFunction` / `SparseSolver` (`Analysis/SparsePropagation.h`) |
> | Reusable monotone framework | **MLIR** `DataFlowSolver` (`mlir/Analysis/DataFlow/`) — *not* in core LLVM |
> | Dataflow = abstract interpretation | a dataflow analysis is an AI over a chosen abstract domain (Cousot & Cousot) |

---

### 1. Definition

> [!note] Definition
> A **data-flow analysis** computes, at every program point, an element of a lattice that **over-approximates** the set of states reachable there, by propagating facts along CFG edges until a fixpoint. "Over-approximate" is the soundness contract: the computed fact must cover every real execution (it may also cover some that never happen).

### 2. Theory

> [!info] Monotone framework
> A finite-height lattice $(L,\sqsubseteq)$, a **monotone** transfer function $f_b:L\to L$ per block, and a meet/join to combine paths. Convergence is guaranteed because a monotone function on a finite-height lattice reaches a fixpoint (Kleene/Kildall iteration).

**Figure — the constant-propagation lattice (what SCCP uses).** A value starts at `⊥` (nothing known), rises to a specific constant, then to `⊤` (overdefined) once two different constants meet. Finite height ⇒ the worklist must terminate.

```mermaid
flowchart BT
  BOT["⊥ undef / unreached"]
  K1["const −1"]
  K0["const 0"]
  K2["const 1 …"]
  TOP["⊤ overdefined (NAC)"]
  BOT --> K1 --> TOP
  BOT --> K0 --> TOP
  BOT --> K2 --> TOP
```

> [!info] MFP vs. MOP
> The iterative solution (**Maximal Fixed Point**) is *sound but possibly less precise* than the ideal **Meet-Over-all-Paths** solution. **MFP = MOP if the transfer functions are distributive** (sufficient, not necessary) (Kildall 1973); for non-distributive analyses (e.g. constant propagation) MFP $<$ MOP in precision.

> [!tip] As abstract interpretation
> A dataflow analysis *is* an abstract interpretation over a particular abstract domain; soundness = the abstract transfer over-approximates the concrete one through a Galois connection (Cousot & Cousot 1977). This is the bridge to relational numerical domains (intervals, octagons, polyhedra); the lattice/fixpoint theory is in [[dataflow-foundations]].

### 3. Algorithm

> [!info] Worklist iteration
> Initialize each point to ⊥ (or ⊤), push all blocks on a worklist; pop a block, apply its transfer function, and if its out-fact changed, push its CFG successors (forward) or predecessors (backward). Iterate to fixpoint.
> - **Forward** (reaching defs, constant prop) vs **backward** (liveness, very-busy expressions).
> - **May** (join $=\cup$, "on some path") vs **must** (meet $=\cap$, "on all paths").

### 4. In LLVM and MLIR

- **SCCP** — Sparse Conditional Constant Propagation (Wegman & Zadeck): lattice `undef → constant → overdefined`, tracking block reachability simultaneously. `Transforms/Scalar/SCCP.cpp` (+ `Utils/SCCPSolver.cpp`). → [[sparse-conditional-constant-propagation]]
- **Generic sparse solver** — `SparsePropagation.h` exposes `AbstractLatticeFunction`; a client supplies the lattice and merge. Used by e.g. `CalledValuePropagation`.
- **Range/value facts** — `LazyValueInfo`, `ConstraintElimination`, known/demanded bits (`ValueTracking`).
- **Liveness** — `LiveVariables` / `LiveIntervals` in `lib/CodeGen` (backward, may), the input to register allocation ([[code-generation-overview]]).

> [!warning] Core LLVM has no single generic *monotone* dataflow framework for IR
> Beyond the **sparse** propagation solver, most IR-level analyses are hand-written (often bit-vector). The reusable, composable monotone framework lives in **MLIR**: the generic `DataFlowSolver` (`mlir/include/mlir/Analysis/DataFlow/`) with built-in `DeadCodeAnalysis`, `SparseConstantPropagation`, and `IntegerRangeAnalysis`.

### 5. Where it's used

Constant propagation & folding; dead-code elimination; available-expression CSE → [[value-numbering]]; integer-range bounds-check elimination; register-allocation liveness. *(Note: DataFlowSanitizer is dynamic taint instrumentation, not static dataflow.)*

### 6. Limitations & future

- **Precision ceiling**: MFP attains MOP only under distributivity; most useful analyses are non-distributive ⇒ conservative.
- **No relational numeric domains in core LLVM**: facts are non-relational (a range per value at best); relationships among variables (octagons, polyhedra) need external engines — **Crab** (AI on LLVM IR), **Apron**, or **Polly**'s polyhedral model.
- **Scale vs. context/path sensitivity**: precise interprocedural/path-sensitive dataflow is expensive; production passes are mostly intraprocedural, flow-sensitive, path-insensitive.
- **Frontier**: MLIR's `DataFlowSolver` as the converging home for reusable, composable analyses.

> [!danger] Source-unchecked — known-stale upstream doc
> The official MLIR tutorial *"Writing DataFlow Analyses in MLIR"* still documents the **old** `ForwardDataFlowAnalysis`/`LatticeElement` API; the current framework is the generic **`DataFlowSolver`** (added in D126751). Verify class names against current doxygen before relying on the tutorial. (This note records the discrepancy per [[source-hierarchy]].)

> [!quote] Sources & confidence
> - **Also in:** Muchnick *Advanced Compiler Design & Impl.* §8 — iterative & control-tree data-flow analysis.
> - **Source:** [`Transforms/Scalar/SCCP.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/SCCP.cpp) · [`include/llvm/Analysis/SparsePropagation.h`](https://github.com/llvm/llvm-project/blob/main/llvm/include/llvm/Analysis/SparsePropagation.h)
> - Kildall 1973 (monotone framework, MFP/MOP) · Cousot & Cousot 1977 (abstract interpretation) · Wegman & Zadeck 1991 (SCCP) — *verified, canonical*.
> - `SparsePropagation.h` generic sparse solver — *verified against LLVM doxygen (2026-06)*.
> - "core LLVM has no generic monotone framework" — *inference from source layout; re-check if precision matters*.
