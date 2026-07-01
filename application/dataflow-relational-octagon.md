---
title: Wiring an Octagon into clang::dataflow — Which Seam?
facet: application
stage: analysis
ecosystem: [clang]
concepts: [source-level-analysis, dataflow-analysis]
theory: []
algorithm: []
data_structures: [clang-cfg]
applications: []
implements: []
src: "clang/include/clang/Analysis/FlowSensitive/DataflowEnvironment.h"
docs: "Clang doxygen — clang::dataflow ↗ https://clang.llvm.org/doxygen/namespaceclang_1_1dataflow.html"
prereqs: [dataflow-worked-example, clang-dataflow-framework]
related: [dataflow-worked-example, clang-dataflow-framework, clang-static-analyzer, source-level-analysis, data-flow-analysis]
tags: [kind/analysis, status/verified]
status: verified
verified_on: 2026-06-30
---

# Wiring an Octagon into clang::dataflow — Which Seam?

> 🧭 **Application** · `application · analysis · clang` · Index [[LLVM.MOC]]
> **Prerequisites:** [[dataflow-worked-example]], [[clang-dataflow-framework]] · **Related:** [[clang-static-analyzer]], [[source-level-analysis]], [[data-flow-analysis]]

> [!abstract] Chapter map
> [[dataflow-worked-example]] left the framework *non-relational*: the state is a per-variable product, so it can say "`x` is `Pos`" but never $x \le y$. This note asks the concrete follow-up — *where would a relational octagon (DBM) go?* The framework exposes two seams: the framework-owned `Environment::ValueModel` and the user lattice `LatticeT`. The interface signatures decide it: `ValueModel` is **per storage location** and therefore structurally non-relational; the octagon must live in a custom `LatticeT`. This note sketches both and shows why one can't hold a relation.

---

## 1. The question

An octagon over variables $V=\{x_1,\dots,x_n\}$ is a single relational object: a difference-bound matrix (DBM) $m$ with entries bounding $\pm x_i \pm x_j \le c$. It is *not* decomposable into one fact per variable — the whole point is that it ties variables together. So the design question is not "what's the abstract value of `x`?" but "**which extension point can own a state that spans all variables at once?**" clang::dataflow gives two candidates.

## 2. The `ValueModel` seam (real interface)

`Environment::ValueModel` is the framework's hook for custom lattice behavior on modeled `Value`s (`DataflowEnvironment.h`). Its three virtuals, verbatim in shape:

```cpp
enum class ComparisonResult { Same, Different, Unknown };
struct WidenResult { Value *V; LatticeEffect Effect; };

class ValueModel {
  virtual ComparisonResult compare(QualType Type,
      const Value &Val1, const Environment &Env1,
      const Value &Val2, const Environment &Env2);
  virtual void join(QualType Type,
      const Value &Val1, const Environment &Env1,
      const Value &Val2, const Environment &Env2,
      Value &JoinedVal, Environment &JoinedEnv);        // "must obey the properties of a lattice join"
  virtual std::optional<WidenResult> widen(QualType Type,
      Value &Prev,    const Environment &PrevEnv,
      Value &Current,       Environment &CurrentEnv);
};
```

Read the **requirements** the header attaches to all three (not the types — the contract):

> [!quote] From `DataflowEnvironment.h` (`ValueModel::join` / `compare`)
> *"`Val1` and `Val2` must model values of type `Type`. `Val1` and `Val2` must be assigned to the **same storage location** in `Env1` and `Env2` respectively."*

That single clause is the whole answer. The hook is invoked **once per storage location**, handed the two `Value`s bound to *that same location* in the two incoming environments. The `Environment` join is a `joinValues` loop over locations; `ValueModel::join` is its per-location kernel. It never sees `x`'s value and `y`'s value in the same call.

> [!warning] Why an octagon cannot live here
> A DBM relates *distinct* locations ($x_i - x_j \le c$). But `ValueModel::join` is, by signature and by its stated requirement, a **per-location** operation: $\text{join} : \text{Val}(\ell) \times \text{Val}(\ell) \to \text{Val}(\ell)$. It is the point-wise kernel of exactly the lift that made [[dataflow-worked-example|`VarMapLattice`]] non-relational. You cannot express a cross-location relation as a family of independent per-location joins — that is the definition of *non-relational*. The `ValueModel` seam is structurally the wrong shape.
>
> The only way to smuggle a DBM through it is degenerate: bind the entire octagon to **one** synthetic storage location (an aggregate `Value`), so a single `join` call sees the whole matrix. But then transfer functions, the store, and the SAT flow condition know nothing about it; you would be re-implementing the store and the fixpoint by hand inside one value's `join`/`widen`, fighting the framework rather than using it.

## 3. The `LatticeT` seam (the right home)

The user lattice `LatticeT` in `DataflowAnalysis<Derived, LatticeT>` is the *whole* per-program-point fact — you own it entirely (see [[dataflow-worked-example]] §4). That is where a relation over all in-scope variables belongs. Set

$$\texttt{LatticeT} = \mathrm{Oct}(V), \qquad \text{a DBM } m \in (\mathbb{Z}\cup\{+\infty\})^{2n \times 2n} \text{ over } V=\text{in-scope } \texttt{VarDecl}\text{s},$$

and implement the framework contract directly on it:

| Contract member | Octagon realization | AI object |
|---|---|---|
| `LatticeT initialElement()` | $\bot$ = the empty (unsatisfiable) DBM, or $\top$ = all bounds $+\infty$ | entry abstract state |
| `transfer(const CFGElement&, Oct&, Environment&)` | interpret assignments/tests as DBM ops: $x := e$, $x := x+c$, guards $x-y\le c$ | abstract transformer $f^\sharp$ |
| `transferBranch(bool, const Stmt*, Oct&, Environment&)` | refine the DBM with the (negated) guard on each edge | condition refinement |
| `Oct::join` | **closure**, then component-wise $\max$ of the two closed DBMs | $\sqcup$ |
| `Oct::operator==` + returned `LatticeEffect` | equality of closed DBMs; `Changed` iff strict ascent | ascending-chain test |
| `Oct::widen` (needed — see §4) | standard octagon widening: keep stable bounds, send unstable ones to $+\infty$ | $\nabla$ |

The framework's Kleene loop then does the rest: iterate `transfer`, `join` at merges, until every block reports `Unchanged`. This is precisely the monotone framework of [[data-flow-analysis]], now with a relational element type instead of a product.

> [!note] Closure is not optional
> DBM join and comparison are only exact on the **closed** (shortest-path–tightened) canonical form. Two DBMs denoting the same octagon can differ entry-wise unless both are closed, so `join`/`==` must close first — otherwise the `LatticeEffect` flag lies and the fixpoint is wrong. For octagons this is the modified Floyd–Warshall *strong closure*.

## 4. Precision–cost, stated

- **Space / time.** Pointwise `VarMapLattice` join is $O(n)$ per merge. An octagon is $O(n^2)$ space; strong closure is $O(n^3)$, run after transfer and before join/compare. Relational precision on the source CFG is genuinely expensive — the same reason neither in-tree engine ships it.
- **Widening is now mandatory.** The finite `Sign` lattice of [[dataflow-worked-example]] terminated for free (no infinite ascending chains). The octagon lattice has **infinite ascending chains** — a bound can loosen without bound across loop iterations — so `Oct::widen` (or `ValueModel::widen` if you'd split state, which §2 rules out) is required for termination. The `WidenResult{Value*, LatticeEffect}` contract maps cleanly: return the widened DBM and `Changed`/`Unchanged` per whether it moved. Recover precision after stabilization with a narrowing pass, as usual.
- **Plumbing to the source model.** DBM columns key on `const VarDecl*` (or `StorageLocation`); because the source CFG has no [[ssa-form|SSA]], you handle re-assignment by DBM *forget* + *assign*, not by fresh names. The framework's symbolic `Value`/`Environment` layer stays orthogonal — you consult it only to resolve which variables a `CFGElement` reads/writes.

## 5. How this lands against CSA

Neither shipped Clang engine is relational. The [[clang-static-analyzer]]'s default constraint solver (`RangeConstraintManager`) tracks **per-symbol ranges** — an interval-flavored, non-relational store; it exposes `getSymMinVal`/`getSymMaxVal`, never a $x_i - x_j$ bound. CSA can swap in an **SMT** constraint manager (`SMTConstraintManager`), which *can* discharge relational path conditions, but that reasons over the path formula, not a widened numeric domain, and is off by default. So:

- **clang::dataflow**: relational numerics are a *DIY `LatticeT`* — build the octagon yourself (this note).
- **CSA**: relational numerics come, if at all, from the *SMT backend on the path condition* — a different mechanism (per-path feasibility, not a joined abstract domain).

The contrast is the same fork-vs-join axis as [[clang-dataflow-framework#4. Flow-sensitive join vs. path fork|the framework §4]]: an octagon in `LatticeT` *joins* a relational over-approximation at every point; CSA's SMT *forks* and checks feasibility per path.

## 6. Limitations & pointers

- This is a **design sketch**, not an in-tree analysis: clang::dataflow ships no octagon, and this note builds one at the API level. Everything attributed to `DataflowEnvironment.h` / `DataflowAnalysis.h` is real; the octagon construction is standard AI (Miné), supplied by the analysis author.
- A production version would reuse a maintained relational-domain library (an Apron-style DBM/octagon backend) as the `LatticeT` implementation rather than hand-rolling closure and widening.
- Next door: [[dataflow-worked-example]] (the non-relational baseline this sharpens), [[clang-static-analyzer]] (the path-sensitive alternative and its SMT option).

> [!quote] Sources & confidence
> - **Tier-1 source (verified 2026-06-30 against the pinned tag — see [[llvm-version]]):** `clang/include/clang/Analysis/FlowSensitive/DataflowEnvironment.h` — `enum class ComparisonResult { Same, Different, Unknown }`, `struct WidenResult { Value *V; LatticeEffect Effect; }`, and `class Environment::ValueModel` with `compare` / `join` / `widen`. The **"same storage location"** requirement (§2) is quoted from the `ValueModel::compare` and `ValueModel::join` doc-comments. `DataflowAnalysis.h` for the `LatticeT` contract (`initialElement`, `transfer`, `transferBranch`).
> - **CSA cross-check:** `clang/include/clang/StaticAnalyzer/Core/PathSensitive/` — `RangedConstraintManager.h` (`Range` = closed interval, `RangeSet`), `ConstraintManager.h` (`getSymMinVal`/`getSymMaxVal`, `assume`/`assumeDual`), `SMTConstraintManager.h` (optional SMT backend). Detailed in [[clang-static-analyzer]].
> - **Theory (not LLVM):** octagon domain, DBM strong closure, and octagon widening are standard abstract interpretation (Miné, *The Octagon Abstract Domain*, 2006); the fixpoint/monotone-framework backbone is [[data-flow-analysis]] (Cousot & Cousot). These are the author's construction, not in-tree code.
