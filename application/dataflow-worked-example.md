---
title: A Minimal clang::dataflow Analysis, Worked
facet: application
stage: analysis
ecosystem: [clang]
concepts: [source-level-analysis, dataflow-analysis]
theory: []
algorithm: []
data_structures: [clang-cfg]
applications: []
implements: []
src: "clang/include/clang/Analysis/FlowSensitive"
docs: "Clang doxygen — clang::dataflow ↗ https://clang.llvm.org/doxygen/namespaceclang_1_1dataflow.html"
prereqs: [clang-dataflow-framework, data-flow-analysis]
related: [clang-dataflow-framework, clang-cfg, source-level-analysis, clang-static-analyzer]
tags: [kind/analysis, status/verified]
status: verified
verified_on: 2026-06-30
---

# A Minimal clang::dataflow Analysis, Worked

> 🧭 **Application** · `application · analysis · clang` · Index [[LLVM.MOC]]
> **Prerequisites:** [[clang-dataflow-framework]], [[data-flow-analysis]] · **Related:** [[clang-cfg]], [[source-level-analysis]], [[clang-static-analyzer]]

> [!abstract] Chapter map
> The [[clang-dataflow-framework|framework note]] describes the engine; this note *builds one*. We read the framework's real lattice API — `LatticeEffect`, `NoopLattice`, `MapLattice`/`VarMapLattice`, and the `DataflowAnalysis<Derived, Lattice>` base — and map each piece onto the abstract-interpretation objects it realizes: the lattice $\langle L, \sqsubseteq, \sqcup, \bot \rangle$, the abstract transformer, and Kleene iteration to $\mathrm{lfp}$. The payoff: seeing exactly *where* the framework is non-relational, and what an octagon would (and wouldn't) buy over the Clang CFG.

---

## 1. What we build

A minimal **flow-sensitive, intra-procedural** analysis over the [[clang-cfg|Clang CFG]] that assigns each in-scope variable an element of some finite abstraction — the textbook shape of a non-relational value analysis, lifted per variable. We don't invent machinery: the lattice is the framework's own `VarMapLattice<ElementLattice>`, and the driver is `DataflowAnalysis<Derived, Lattice>`. Only the base `ElementLattice` (a sign abstraction, below) is illustrative.

## 2. The abstract-interpretation dictionary

The framework is, by its own headers' admission, abstract interpretation (`Value.h`: *"classes for values computed by abstract interpretation"*). The correspondence is exact:

| AI object | clang::dataflow realization | File |
|---|---|---|
| Lattice $\langle L, \sqsubseteq, \sqcup, \bot\rangle$ | a class with `bottom()`, `join(...)`, `operator==` | `DataflowLattice.h`, `MapLattice.h` |
| Ascending-chain flag ($x \sqsubset x \sqcup y$?) | `enum LatticeEffect { Unchanged, Changed }` returned by `join` | `DataflowLattice.h` |
| Abstract transformer $f^\sharp$ | `transfer(const CFGElement&, Lattice&, Environment&)` | `DataflowAnalysis.h` |
| Initial (entry) abstract state | `LatticeT initialElement()` | `DataflowAnalysis.h` |
| Edge/condition refinement | optional `transferBranch(bool, const Stmt*, ..., Environment&)` | `DataflowAnalysis.h` |
| Symbolic store + flow condition | `Environment` (storage locations → values; boolean `Formula`s to a SAT solver) | `DataflowEnvironment.h`, `Arena.h` |
| Fixpoint $\mathrm{lfp}\,f^\sharp$ | monotone worklist iteration, join at CFG merges | (engine) |

> [!note] Two lattices, not one
> A subtlety worth stating up front: a clang::dataflow analysis carries **two** lattice-like pieces. The **user lattice** `LatticeT` is the flow fact you design. The **`Environment`** is a *second*, framework-owned abstract state — a symbolic memory (storage locations → `Value`s) plus a flow condition reasoned about by SAT. The engine joins both at merges. Many models (e.g. the optional checker) push almost everything into the `Environment` and use `NoopLattice` for `LatticeT`.

## 3. The lattice layer (real source)

**Trivial lattice — one point.** When all state lives in the `Environment`, `LatticeT` is `NoopLattice`: the one-element lattice $L=\{\top\}$ with $\top=\bot$.

```cpp
class NoopLattice {
  bool operator==(const NoopLattice &Other) const { return true; }
  LatticeJoinEffect join(const NoopLattice &Other) {
    return LatticeJoinEffect::Unchanged;   // join can never ascend
  }
};
```

Its `join` is constantly `Unchanged` — correct, since a one-point lattice has no strictly ascending chains, so it can never delay the fixpoint.

**The workhorse — pointwise lifting.** `MapLattice<Key, ElementLattice>` is precisely the product/pointwise lift $L^{\text{Key}}$ that builds a non-relational domain from a per-element one. The header says it outright: *"lifting a particular lattice to all variables in a lexical scope … a bounded semi-lattice, so long as the user limits themselves to a finite number of keys."*

```cpp
template <typename Key, typename ElementLattice> class MapLattice {
  llvm::DenseMap<Key, ElementLattice> C;
public:
  static MapLattice bottom() { return MapLattice(); }        // ⊥ = empty map
  LatticeJoinEffect join(const MapLattice &Other) {          // pointwise ⊔
    LatticeJoinEffect Effect = LatticeJoinEffect::Unchanged;
    for (const auto &O : Other.C) {
      auto It = C.find(O.first);
      if (It == C.end()) { C.insert(O); Effect = Changed; }  // missing key ≡ ⊥
      else if (It->second.join(O.second) == Changed) Effect = Changed;
    }
    return Effect;
  }
};
template <typename ElementLattice>
using VarMapLattice = MapLattice<const clang::VarDecl *, ElementLattice>;
```

Three design facts to read off, each with an AI reading:

- **$\bot$ = the empty map.** A key absent from the map is *implicitly* $\bot$ of `ElementLattice`. So `join` treats "present in one operand only" as $\bot \sqcup e = e$ — the pointwise join, without ever materializing $\bot$ entries.
- **$\top$ is implicit**, not stored: the map sending every valid key to `ElementLattice`'s $\top$. This is why equality is *"direct equality of underlying map entries"* — a map with only-$\bot$ keys is *not* equal to the empty map, a deliberate representational choice, not a lattice one.
- **`join` returns `Changed` iff it strictly ascended.** That boolean *is* the ascending-chain check $x \sqsubset x \sqcup y$ that the worklet needs: a `Changed` at a block re-enqueues its CFG successors; global quiescence (all `Unchanged`) is the post-fixpoint. Termination requires `ElementLattice` to have no infinite ascending chains (or a `widen`).

## 4. The analysis layer

`DataflowAnalysis<Derived, LatticeT>` is CRTP: you derive and supply two members (verbatim from the header contract):

```
LatticeT initialElement();                                   // entry abstract state
void      transfer(const CFGElement&, LatticeT&, Environment&); // f♯ at one CFG element
```

and *optionally* `transferBranch(bool Branch, const Stmt*, LatticeT&, Environment&)` to refine state along a specific edge of a conditional — the hook that lets `if (p) …` learn "`p` holds" on the true edge. `Derived` may also override the `Environment::ValueModel` virtuals (its `join`/`widen` for `Value`s) — that is how you customize the *second* lattice of §2.

The engine supplies the rest: it walks the [[clang-cfg|`AdornedCFG`]] in RPO, applies `transfer` per element, and `join`s incoming states at each block entry, iterating until no `join`/transfer reports `Changed`.

## 5. Worked instantiation

Pick an illustrative `ElementLattice` — a sign abstraction (this class is *not* in-tree; it's the reader's contribution, standing in for any bounded semi-lattice):

$$\text{Sign} = \{\bot,\; \mathtt{Neg},\; \mathtt{Zero},\; \mathtt{Pos},\; \top\}, \qquad \bot \sqsubset \{\mathtt{Neg},\mathtt{Zero},\mathtt{Pos}\} \sqsubset \top.$$

Then the whole-function fact is `VarMapLattice<Sign>` — one sign per variable, i.e. the non-relational store $\text{Var} \to \text{Sign}$. Transfer for `x = <expr>;` computes the sign of `<expr>` (abstract arithmetic: $\mathtt{Pos}\times\mathtt{Pos}=\mathtt{Pos}$, $\mathtt{Pos}+\mathtt{Neg}=\top$, …) and writes `L[x]`.

Trace a diamond:

```c
int y;
if (c) { y = 1; }      // block B1:  {y ↦ Pos}
else   { y = -1; }     // block B2:  {y ↦ Neg}
use(y);                // block B3 (merge)
```

At the merge B3 the engine computes `join(B1_out, B2_out)` — pointwise, so `y ↦ join(Pos, Neg) = ⊤`. The analysis carries **one** state past the merge: `{y ↦ ⊤}`. That single lattice element per program point is the defining move — contrast the [[clang-static-analyzer]], which would instead keep the two branch states as **separate symbolic paths** through B3 (no join, path count grows). The fork-vs-join figure lives in the [[clang-dataflow-framework#4. Flow-sensitive join vs. path fork|framework note §4]].

> [!warning] The merge is where precision leaks
> `join(Pos, Neg) = ⊤` discards the *correlation* `c ⟹ y>0`. A path-sensitive engine keeps it; a flow-sensitive one buys scalability by forgetting it. `transferBranch` recovers *some* of this by refining on the guard, but only for facts expressible in your lattice + the `Environment`'s flow condition.

## 6. Where it is (and isn't) relational

`VarMapLattice` is **non-relational by construction**: the state is a *product* $\prod_{v} \text{Sign}$, so it can express "`x` is `Pos` and `y` is `Neg`" but never a *relation* like $x \le y$ or $x + y \le 3$. This is the same expressiveness ceiling as an interval store, and the same reason the framework cannot, as-is, prove a relational invariant that an octagon (DBM) or polyhedron would.

Two consequences worth internalizing:

- **The framework ships no relational numerical domain.** Neither does the [[clang-static-analyzer]] (its `RangeConstraintManager` is range/interval-flavored). Relational precision on the source CFG is simply not on offer in-tree; you would supply it as a custom `ElementLattice` *and* a custom `Environment::ValueModel`, and pay for it.
- **Relational reasoning here is boolean, not numeric.** What the `Environment` *does* track relationally is the **flow condition** — a boolean `Formula` over `Atom`s (owned by `Arena`) discharged by `WatchedLiteralsSolver` (a SAT solver, `WatchedLiteralsSolver.h`). So the framework reasons about *which paths are feasible* via SAT, but about *numeric values* only pointwise. An octagon would live in the numeric layer the framework leaves non-relational; wiring one in means teaching `ValueModel::join`/`widen` a DBM, not touching the SAT layer.

> [!info] Precision–cost, stated
> Pointwise `VarMapLattice` join is $O(|\text{Var}|)$ per merge and terminates on any bounded `ElementLattice`. A relational `ElementLattice` (octagon: $O(n^2)$ DBM, closure $O(n^3)$) changes both the per-join cost and the termination story — you now *need* a `widen`, supplied via `ValueModel::widen`, because the DBM lattice has infinite ascending chains.

## 7. Limitations & pointers

- **Intra-procedural by default** (an opt-in, bounded context-sensitive mode exists), single `LatticeT` type — same envelope as the [[clang-dataflow-framework|framework]] itself.
- **Termination is your obligation.** A finite `ElementLattice` (like Sign) is safe; anything with infinite ascending chains needs `widen` on the user lattice and/or `ValueModel::widen` on the `Environment`.
- **This note is a scaffold, not a shipped analysis.** The real in-tree exemplar to read next is `Models/UncheckedOptionalAccessModel` — which, tellingly, uses `NoopLattice` and puts *all* its state in the `Environment`, the opposite end of the design space from the `VarMapLattice` sketch here.

> [!quote] Sources & confidence
> - **Source (tier 1, verified 2026-06-30 against the pinned tag — see [[llvm-version]]):** `clang/include/clang/Analysis/FlowSensitive/` — `DataflowLattice.h` (`enum LatticeEffect { Unchanged, Changed }`; `LatticeJoinEffect` = deprecated alias), `NoopLattice.h` (one-element lattice; `join` ⇒ `Unchanged`), `MapLattice.h` (`bottom()` = empty map, pointwise `join`, missing-key ≡ `bottom`, `VarMapLattice` alias), `DataflowAnalysis.h` (`DataflowAnalysis<Derived, LatticeT>` contract: `initialElement()`, `transfer(const CFGElement&, LatticeT&, Environment&)`, optional `transferBranch`), `DataflowEnvironment.h` / `Arena.h` (`Environment`, `Value`, `Formula`, `WatchedLiteralsSolver`).
> - **Doc:** [Clang doxygen — `clang::dataflow`](https://clang.llvm.org/doxygen/namespaceclang_1_1dataflow.html).
> - **Illustrative, not tier-1:** the `Sign` `ElementLattice` and the diamond trace are the author's pedagogical construction — standard non-relational AI, *not* an in-tree class. Everything attributed to a named header above *is* in-tree.
> - **Theory:** pointwise lifting, ascending chains, and $\mathrm{lfp}$ per the monotone framework of [[data-flow-analysis]] (Kildall/Cousot).
