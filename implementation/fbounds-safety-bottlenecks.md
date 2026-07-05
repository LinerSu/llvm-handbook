---
title: -fbounds-safety — precision & performance bottlenecks
facet: implementation
stage: analysis
ecosystem: [clang]
concepts: [memory-safety, range-analysis]
implements:
  - { ecosystem: clang, src: "clang/docs/BoundsSafety.rst" }
src: "clang/docs/BoundsSafety.rst"
docs: "Clang — -fbounds-safety ↗ https://clang.llvm.org/docs/BoundsSafety.html"
prereqs: [fbounds-safety, constraint-elimination]
related: [fbounds-safety, constraint-elimination, data-flow-analysis, pointer-alias-analysis, interprocedural-summaries, scalable-static-analysis]
tags: [kind/analysis, status/draft, version-sensitive]
status: draft
verified_on: ""
---

# -fbounds-safety — precision & performance bottlenecks

> 🧭 **Implementation** · `implementation · analysis · clang` · Index [[LLVM.MOC]]
> **Companion to:** [[fbounds-safety|-fbounds-safety]] (how the model works) · **Discharged by:** [[constraint-elimination|ConstraintElimination]] · **Chapter:** [[Memory-Safety-Hardening.MOC|Memory Safety & Hardening]]

> [!abstract] What this note adds
> [[fbounds-safety|-fbounds-safety]] is **fail-closed**: an obligation it cannot prove statically becomes a **runtime trap**, never an out-of-bounds access. So within its enforced spatial subset the bottleneck is **cost**, not safety — *a check that survives to run time* (precision) or *what that check costs* (performance). This note reads those bottlenecks in abstract-interpretation terms and lays out where the headroom is. It reasons over the design docs and the [[fbounds-safety|verified mechanism]]; the performance *rankings* are argued, not benchmarked (flagged where they appear).

---

## 0. Root cause — a bound is a *value*, not a *fact*

Almost every bottleneck below collapses to one design choice:

> **A bound is a mutable runtime *value* (often memory-resident — a struct field or global), not a static fact.**

That is exactly what buys ABI-compatibility and expressiveness — and exactly what forces the compiler to *prove* each access in range or emit a dynamic check. In abstract-interpretation terms: `__counted_by(n)` is a **value-dependent refinement** `{ p | len(p) == n }` whose witness `n` is an ordinary lvalue, so discharging the access obligation `0 ≤ i < n` reduces to reasoning about *the value of `n` at this program point* — a numeric + alias problem, not a lookup.

The obligation calculus is the same one split two ways: each dereference emits a verification condition; [[constraint-elimination|ConstraintElimination]] discharges what it can prove, and the residue is compiled in as a compare-and-`llvm.ubsantrap`. **Precision = how often the static side wins.** Everything below is a reason it loses.

---

## 1. Precision bottlenecks

*How often the compiler can prove an access safe and delete the check — and how often it accepts correct code without complaint.*

> [!info] The six precision ceilings
>
> | # | Bottleneck | Why the static proof fails |
> |---|---|---|
> | 1.1 | **Discharge engine is bounded** | [[constraint-elimination|ConstraintElimination]] handles affine relations, monotone IVs (via SCEV), decomposed GEPs, and `min`/`max`/`assume` facts — but **not** genuinely non-linear reasoning (products of unknowns, opaque loaded indices, hashing/bit-twiddling, disjunctive path-merged facts). Those keep a runtime check. |
> | 1.2 | **Memory-resident witness can't be shown invariant** | When `n` is a field/global/address-taken local, any opaque call or aliasing store may change it, so "can I delete this check?" reduces to "is `n` **unchanged** between two points?" — i.e. [[pointer-alias-analysis|alias]] + mod-ref, C's weak spot. *This, not the textbook loop, is the real ceiling.* (A by-value `n` is a stable SSA value and is exempt.) |
> | 1.3 | **No-wrap knowledge is lost at the frontend→IR boundary** | The refinement's *content* survives (the check is emitted against `p + count`), but the **no-wrap** facts around it don't; the frontend must hand-re-add `inbounds` on `p + count`, and the pass must re-derive the rest from loop facts. |
> | 1.4 | **Defined-OOB semantics strip the optimizer's facts** | To make wide-pointer arithmetic safe-by-construction, forming an out-of-bounds pointer is **well-defined**, so those GEPs get **no `inbounds`** — but `nusw`/`nuw` GEP flags are precisely what SCEV and `decomposeGEP` need. *The model's own semantics weaken its discharge engine* (`decomposeGEP` bails on a flagless GEP). |
> | 1.5 | **Paired-assignment rule is syntactic → false rejections** | The `buf`/`count` invariant is enforced by a coarse **must-adjacency** CFG condition (both writes in one basic block, no side effects between). Correct code that updates the pointer and count in separate helpers or across a call is **rejected at compile time**. Precision loss at the *source* level, a distinct axis from residual checks. |
> | 1.6 | **No interprocedural constraint propagation** | Facts cross function boundaries only through **inlining**. An un-inlined callee re-checks even when every caller established the bound; across TUs it is hopeless without LTO. Modularity *is* the ABI win — and *is* the precision cost. |

**1.7 — out of scope by construction.** `-fbounds-safety` is spatial-only: no temporal safety (use-after-free), no type-confusion safety. Checks needing liveness or type reasoning are simply not attempted.

> [!info]+ Why 1.3/1.4 are an *internal tension*
> The model chooses defined out-of-bounds pointer values so bounds can propagate through ordinary C arithmetic (only *dereference* traps, not pointer *formation*). But "defined OOB" means "no `inbounds`," and `inbounds` is the very fact the relational discharge engine consumes. The design pays for propagation-friendliness in discharge power — only partially clawed back by re-adding `inbounds` on the `__counted_by` upper bound (1.3).

---

## 2. Performance bottlenecks

*The runtime, code-size, and compile-time cost of the checks that survive §1.*

> [!warning] The five costs
> - **2.1 Fat pointers (2–3× size, register pressure).** A wide pointer is `⟨ptr, lower, upper⟩` (3 words) or `⟨ptr, upper⟩` (2); it spills more, and bounds are computed/moved until DCE proves them dead. Contained by keeping wide pointers to **locals** (heap/struct/ABI layout preserved), but hot code passing fat locals still pays.
> - **2.2 Count reloads defeat LICM — the real hot-loop cost.** When `n` can't be shown loop-invariant (1.2), a loop that *should* be check-free **reloads `n` every iteration**; the **load**, not the compare, is the expensive part, and it blocks hoisting. *Plausibly the dominant runtime cost over memory-resident counts — a reasoned expectation, not a measured ranking.*
> - **2.3 Blocked vectorization.** Residual checks + lost GEP no-wrap flags (1.4) are *expected* to inhibit loop/SLP vectorization, interchange, and unrolling that need provable trip counts and non-wrapping GEPs. The cost is then the **optimizations the checks prevent**, not only the checks. *(Mechanistic, not quantified here.)*
> - **2.4 Code size / I-cache / trap branches.** A check at every unproven deref means thousands of never-taken trap edges. `-fsanitize-trap` lowers each to a single `ud1` (tiny); the compiler-rt handler mode materializes handler args + a `call` (readable diagnostics, materially larger).
> - **2.5 Unoptimized builds are the worst case.** Essentially all check-elimination lives in the optimizer, so `-O0` keeps **every** emitted check. The doc frames this overhead as *not fundamental*.
> - **2.6 Compile-time solver budget feeds back into precision.** ConstraintElimination is bounded to keep builds fast, which caps how much it proves, which leaves more runtime checks — precision and compile time trade directly (loops back to 1.1).

---

## 3. The unifying picture — where does the bound live?

Every item above is one line: **bounds are values, so they must be checked, can change, and are hard to prove invariant.** The design space is really a choice of *where the bound lives*, and each choice moves the bottleneck:

| Approach | Where the bound lives | Bottleneck moves to |
|---|---|---|
| Static dependent-refinement types (SMT backend) | a compile-time **fact** | the human + the solver (more rejections, proof burden) |
| Hardware capabilities (CHERI) | **silicon** (unforgeable fat ptr) | hardware / ISA deployment |
| **`-fbounds-safety`** | an ordinary **C value in memory** | the **mid-end optimizer's** ability to prove checks redundant |

`-fbounds-safety` deliberately picks the middle: adoptable per-file with the C ABI intact, paid for in dynamic checks + count reloads + fat locals. Its precision *and* performance are therefore gated by **LLVM's mid-end** — [[pointer-alias-analysis|alias analysis]], [[constraint-elimination|ConstraintElimination]], and the redundancy-removing passes (CVP/LVI, InstCombine, GVN, SimplifyCFG) — and the doc's own position is that the overhead is *not fundamental*.

---

## 4. How to improve — three highest-leverage levers

Each attacks precision **and** performance at once:

> [!example]+ 1 — Carry frontend refinements into IR
> Emit the relation `len(p) == n` and the no-wrap facts as `llvm.assume` / metadata — a channel [[constraint-elimination|ConstraintElimination]] already consumes — so they are not erased at the frontend→IR boundary and re-derived. **Attacks 1.3, 1.4, 2.2.**

> [!example]+ 2 — Interprocedural discharge via LTO + inlining
> Let bounds facts cross function/TU boundaries so an un-inlined callee is not forced to re-check what every caller established. This is where **compositional summaries** ([[interprocedural-summaries]], and the [[scalable-static-analysis|SSAF]] direction) meet bounds checking. **Attacks 1.6, 2.2.**

> [!example]+ 3 — Stronger relational discharge (beyond affine)
> The discharge engine re-derives relations *per query* via Fourier–Motzkin and keeps **no maintained closure** ([[constraint-elimination]] §5) — so loop-carried relations are re-proven, not accumulated. A **maintained relational domain** (difference-bound matrix / octagon / template constraints) would carry `n`-invariance and scaled bounds across a loop, discharging checks the per-query engine drops — the classic abstract-interpretation upgrade of *keep a closed lattice element* over *ad-hoc constraint set*. **Attacks 1.1, 2.3.**

> [!note] Practical levers for adopters today
> Prefer external `__counted_by` over fat `__bidi_indexable` where the length already exists; keep the count local and immutable near hot loops (so it hoists); avoid opaque calls between a count's definition and its use (each forces a reload); build `-O2`+ with LTO; choose the trap mode consciously (`-fsanitize-trap` for size, handler for diagnostics).

---

> [!summary] The one thing to remember
> Within its spatial subset `-fbounds-safety` is fail-closed — its bottleneck is **cost, not safety**. That cost is single-rooted: **bounds are mutable runtime values**, so the compiler emits a check wherever it can't *prove* the access in range, and it often can't because (a) the discharge engine handles affine/monotone relations but is no general non-linear verifier, (b) a memory-resident witness can't be shown invariant across opaque calls (alias analysis), and (c) no-wrap facts are lost before the optimizer sees them. The runtime price — count reloads defeating LICM, lost vectorization, fat-pointer pressure, trap-branch code size — is the residue of those unproven obligations. None of it is fundamental: it shrinks as IR-level refinement carriage, interprocedural discharge, and relational domains improve.

> [!quote] Sources & confidence
> - **Primary docs (tier-2):** [Clang — `-fbounds-safety`](https://clang.llvm.org/docs/BoundsSafety.html) and its implementation-plans doc (`clang/docs/BoundsSafetyImplPlans.rst`) — the "Bounds check optimizations", "Maintaining correctness of bounds annotations", and "Limitations" sections underpin §1–§2.
> - **Verified mechanism (tier-1, cross-referenced):** the check-insertion + static-discharge split is documented in [[fbounds-safety]] and [[constraint-elimination]] (read from source at the pinned tag, see [[llvm-version]]).
> - **Reasoned, not measured:** the performance *rankings* in §2 (esp. 2.2 as "dominant", 2.3 vectorization loss) are mechanistic arguments from the design, not benchmarks — treat as hypotheses. `version-sensitive`: which parts of the full model are upstreamed varies by release → [[llvm-version]].
