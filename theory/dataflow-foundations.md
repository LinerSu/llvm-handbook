---
title: Foundations of Data-Flow Analysis
facet: theory
stage: analysis
ecosystem: [general]
concepts: [dataflow-analysis, lattice-theory]
docs: "Cousot & Cousot 1977; Kildall 1973"
book: "Dragon Book (Aho/Lam/Sethi/Ullman, 2e) §9.3"
prereqs: []
related: [data-flow-analysis, value-numbering, dominator-tree]
tags: [kind/theory, status/unverified]
status: unverified
verified_on: ""
---

# Foundations of Data-Flow Analysis

> 🧭 **Theory** · `theory · analysis · general` · Index [[LLVM.MOC]] · see also [[dragon-book-ch9.MOC|Dragon Ch.9]]
> **Applied in:** [[data-flow-analysis]] · **Instantiated by:** [[value-numbering]] (and SCCP, ranges)

> [!abstract] Chapter map
> The lattice-theoretic skeleton every concrete [[data-flow-analysis|dataflow analysis]] hangs on: a **lattice** of facts, a **monotone** transfer function, a **meet/join**, and the guarantee that **iteration reaches a fixpoint**. This is the "why it works (and terminates)" layer — tool-agnostic, then connected to how LLVM uses it.

> [!info] The framework
> A monotone dataflow framework is $(L, \sqsubseteq, \sqcap, F)$: a **lattice** $L$ of facts ordered by $\sqsubseteq$ (less precise $\sqsubseteq$ more precise), a **meet** $\sqcap$ (combine facts arriving from several edges), and a set $F$ of **monotone** transfer functions $f_b : L \to L$ (one per block). The analysis solves the equations $\mathrm{out}[b] = f_b(\mathrm{in}[b])$, $\mathrm{in}[b] = \bigsqcap_{p \to b} \mathrm{out}[p]$ (the *forward* form; a backward analysis such as liveness runs the same equations over reversed CFG edges).

---

## 1. Lattices, meet, join

**Figure — a tiny lattice.** `meet` ($\sqcap$) is the greatest lower bound, `join` ($\sqcup$) the least upper bound; here `a ⊔ b = ⊤`, `a ⊓ b = ⊥`.

```mermaid
flowchart BT
  BOT["⊥ (bottom)"]
  A["a"]
  B["b"]
  TOP["⊤ (top)"]
  BOT --> A --> TOP
  BOT --> B --> TOP
```

A dataflow value is an element of $L$; combining information at a CFG merge is the meet of the incoming values. Concretely, in the constant-propagation lattice for one variable, take $a$ = "x is 2" and $b$ = "x is 3": the merge computes $a \sqcap b = \bot$ ("x is not a known constant"), because the meet is the most precise fact still true on *both* incoming paths.

## 2. Why iteration converges

> [!note] The termination theorem
> If every $f_b$ is **monotone** ($x \sqsubseteq y \Rightarrow f_b(x) \sqsubseteq f_b(y)$) and $L$ has **finite height** (the longest strictly increasing chain $\bot \sqsubset \cdots \sqsubset \top$ is finite, so no value can climb forever), then worklist iteration reaches the **least (or greatest) fixpoint** in finitely many steps. Each step only moves values monotonically along the lattice, and finite height bounds how far they can move.

This is why a constant lattice (height 2) or a bit-vector lattice (height = #facts) always terminates; it is also why **abstract domains of infinite height** (intervals, polyhedra) need **widening** to force termination.

> [!figure]+ Animation — the termination theorem in motion
> ![dataflow-foundations-lattice-climb.gif](attachments/dataflow-foundations-lattice-climb.gif)
> The loop-header facts `i` and `sum` from [[running-example|the running example]] climb the constant lattice as worklist iteration runs — monotone transfers only move facts *up*, and the height-2 chain caps each fact at two moves, which is exactly why the fixpoint (MFP) must arrive. (Regenerate: `_meta/anim/storyboards/dataflow-foundations-lattice-climb.json`.)

The theorem above says iteration *stops*. It says nothing about **when** — and that gap is why no real engine visits blocks in arbitrary order.

> [!info] Why every engine walks in reverse post-order
> Visit blocks in **reverse post-order** — a topological order of the CFG once back edges are ignored — and each fact propagates as far as it can along forward edges **within a single sweep**. Only a **back edge** can carry a fact to a block already visited this pass, and so only a back edge can force another sweep.
>
> The consequence is the striking part: the number of sweeps is bounded by the flow graph's **loop nesting depth**, *not by its size*. A 10,000-block function nested two loops deep converges in a couple of passes; a 50-block function nested five deep takes more. Formally, depth $d$ is the greatest number of back edges on any acyclic path from entry, the flow graph must be **reducible**, and the classical bound is stated for bit-vector ("rapid") frameworks — Hecht & Ullman's result, generalized to monotone frameworks by Kam & Ullman.

> [!danger] Unverified — the exact constant
> Sources state the bound as **$d+2$** or **$d+3$**, differing on how passes are counted (whether the initial sweep and the final confirm-nothing-changed sweep are included) and on the precise framework conditions. This note therefore asserts only the **shape** — linear in loop depth, independent of graph size — and deliberately does not commit to a constant. Settling it requires Hecht & Ullman (1975) or Kam & Ullman (1976) directly; three secondary sources consulted disagreed with each other.

> [!tip] Where this shows up in LLVM
> It's why `llvm/ADT/PostOrderIterator.h` ships a `ReversePostOrderTraversal` at all, and why Clang's dataflow engine walks its CFG in RPO rather than in layout order (see [[dataflow-worked-example]]). [[loop-invariant-code-motion|LICM]] leans on the same property for a different purpose: it hoists in RPO so that an operand is already hoisted by the time its user is examined — which is what lets it get away with a *local* invariance test instead of iterating to a fixpoint at all. Choosing the traversal order is how you avoid needing the fixpoint.

## 3. MFP vs. MOP — precision

> [!info] The two solutions
> - **MOP** (Meet-Over-all-Paths) is the *ideal*: meet the effect of every path reaching a point.
> - **MFP** (Maximal Fixed Point) is what iteration *computes*.
>
> Always $\mathrm{MFP} \sqsubseteq \mathrm{MOP}$ (iteration is sound but may be less precise). They **coincide iff the transfer functions are distributive** ($f(x \sqcap y) = f(x) \sqcap f(y)$). Bit-vector problems (liveness, reaching defs) are distributive ⇒ MFP = MOP; constant propagation is **not** distributive ⇒ MFP can be strictly less precise.

> [!question] Predict first
> Two branches merge: one sets `x = 2, y = 3`, the other `x = 3, y = 2`; after the merge, `z = x + y`. On *every* path `z` is 5. Does iterative constant propagation discover that?

> [!example] Why constant propagation loses at merges
> - **MOP** (path-by-path): path 1 gives `z = 2+3 = 5`, path 2 gives `z = 3+2 = 5`; meeting the two results keeps `z = 5`.
> - **MFP** (iterate): at the merge block, `x = 2 ⊓ 3 = ⊥` (not a constant) and `y = 3 ⊓ 2 = ⊥`; the transfer function then computes `z = ⊥ + ⊥ = ⊥`.
>
> Meeting *before* applying the transfer function threw away the correlation between `x` and `y` — exactly the failure of distributivity: $f(x \sqcap y) \sqsubset f(x) \sqcap f(y)$.

## 4. In LLVM (and the abstract-interpretation view)

> [!info] How LLVM instantiates the framework
> Each LLVM analysis picks a lattice and transfer functions and runs worklist iteration: **SCCP** uses the constant lattice; the generic **`SparsePropagation`** solver lets a client supply $L$ and the merge; **liveness** is a distributive bit-vector problem. See [[data-flow-analysis]] for the concrete passes. By the **Galois-connection** view (Cousot & Cousot), a dataflow analysis *is* an abstract interpretation: $L$ is an abstract domain that over-approximates the *collecting semantics* (the set of concrete states that can actually reach each program point), and soundness is exactly "the abstract transfer over-approximates the concrete one."

> [!summary] The one thing to remember
> A dataflow analysis is **monotone functions on a finite-height lattice**; that pair guarantees a sound fixpoint that **terminates**. Distributivity is the extra property that makes the computed answer (MFP) as precise as the ideal (MOP).

> [!quote] Further reading
> - **Also in:** Muchnick *Advanced Compiler Design & Impl.* §8.1–8.3 — lattices and the iterative framework.
> - **Dragon Book §9.3** — foundations of data-flow analysis (lattices, monotone frameworks, MOP vs MFP).
> - Kildall 1973 (monotone framework); Cousot & Cousot 1977 (abstract interpretation / Galois connections).
