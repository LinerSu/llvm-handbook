---
title: Unification
facet: algorithm
stage: analysis
ecosystem: [general]
concepts: [unification, type-inference]
book: "Dragon Book (Aho/Lam/Sethi/Ullman, 2e) §6.5.5"
prereqs: []
related: [type-checking, pointer-alias-analysis]
tags: [kind/algorithm, status/verified]
status: verified
verified_on: 2026-06-28
---

# Unification

> 🧭 **Algorithm** · `algorithm · analysis · general` · Index [[LLVM.MOC]] · see also [[dragon-book-ch6.MOC|Dragon Ch.6]]
> **Powers:** [[type-checking]] (type inference) **and** [[pointer-alias-analysis]] (Steensgaard / DSA)

> [!abstract] Chapter map
> Unification finds a substitution that makes two term/type expressions identical. It earns a note because the *same* union-find algorithm drives two things in the LLVM world: **type inference** in front ends and **unification-based pointer analysis** (Steensgaard, and LLVM's DSA). This note gives the algorithm with a worked trace, then shows the alias-analysis use concretely.

---

## 1. Definition

> [!note] Definition
> A **substitution** $S$ maps variables to terms. $S$ **unifies** $t_1,t_2$ if $S(t_1)=S(t_2)$. The **most general unifier (mgu)** is the least-committing such $S$ — every other unifier is an instance of it.

## 2. The algorithm (union-find + occurs-check)

Represent each term as a node; variables are leaves. `unify(m,n)` on representatives `s=find(m)`, `t=find(n)`:
- `s==t` → done;
- both **constructors** with the same operator/arity (e.g. `→`, `array`) → `union(s,t)`, then `unify` corresponding children;
- one is a **variable** → `union(s,t)`, after an **occurs-check** (don't bind `α` inside a term containing `α`);
- otherwise → **fail** (clash).

With union-by-rank + path compression this is near-linear, $O(n\,\alpha(n))$.

> [!example]+ Worked trace — unify `α → int` with `bool → β`
> Both are function constructors `_ → _`, arity 2 ⇒ unify children pairwise:
> - domains: `unify(α, bool)` ⇒ `α := bool`
> - codomains: `unify(int, β)` ⇒ `β := int`
>
> **mgu = { α ↦ bool, β ↦ int }**; both sides become `bool → int`. ✓

> [!example]- Two failures (click to expand)
> - **Clash:** `unify(int → α, bool)` → one side is `→`, the other the constructor `bool` ⇒ **fail**.
> - **Occurs-check:** `unify(α, list(α))` → binding `α := list(α)` would build an infinite type ⇒ **fail**.

## 3. The LLVM connection — points-to as unification

> [!tip] Why a type-inference algorithm appears in alias analysis
> **Steensgaard's** analysis and LLVM's **DSA** ([[pointer-alias-analysis]]) treat "two pointers may point to the same object" as an **equivalence** and *unify* their points-to nodes — literally `union` in a union-find.

> [!example]+ Worked merge
> ```c
> p = &a;   // pts(p) ⊇ {A}      node A
> q = p;    // unify pts(q) with pts(p)        → q also points to A
> *p = &b;  // contents(A) points to node B
> *q = &d;  // *q aliases *p (p,q unified), so unify contents(A) with {D}
> ```
> The last step **merges B and D into one node** (a single union). After analysis, `*p` and `*q` reach the *same* node ⇒ reported **may-alias**. Merging is what keeps the points-to graph **finite** (bounded nodes) and the analysis near-linear — exactly DSA's `mergeCells`.

> [!note] Precision/cost — unification vs. subset
> Unification (Steensgaard) uses **equality** constraints: fast, coarse, merges aggressively. Andersen uses **subset/inclusion** constraints $pts(a)\supseteq pts(b)$: more precise, costlier. Same equality-vs-inclusion precision–cost axis you meet in abstract domains.

> [!summary] The one thing to remember
> One union-find algorithm, two jobs: **Hindley–Milner type inference** and **Steensgaard/DSA alias analysis** are the same move — merge two things into one equivalence class (with an occurs-check). Equality-based merging is what makes both fast and coarse.

> [!quote] Further reading
> - **Dragon Book §6.5.5** — the unification algorithm, in the context of polymorphic type inference.
> - Steensgaard, *Points-to Analysis in Almost Linear Time* (POPL 1996); Lattner & Adve, *Data Structure Analysis*.
