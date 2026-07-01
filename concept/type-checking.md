---
title: LLVM Types & Where Type-Checking Lives
facet: concept
stage: ir
ecosystem: [general, llvm, clang]
concepts: [type-checking, type-systems]
book: "Dragon Book (Aho/Lam/Sethi/Ullman, 2e) §6.3, §6.5"
prereqs: [llvm-basics]
related: [unification, extending-llvm-ir, getelementptr, source-level-analysis, clang-ast]
tags: [kind/concept, status/verified]
status: verified
verified_on: 2026-06-28
---

# LLVM Types & Where Type-Checking Lives

> 🧭 **Concept** · `concept · ir · general+llvm+clang` · Index [[LLVM.MOC]] · see also [[dragon-book-ch6.MOC|Dragon Ch.6]]
> **Prerequisites:** [[llvm-basics]] · **Realized by:** [[extending-llvm-ir]], [[getelementptr]] · **Inference uses:** [[unification]]

> [!abstract] Chapter map
> LLVM IR is **strongly, structurally typed**. This note shows the type system with examples (types, storage layout, casts, the verifier), then draws the boundary that matters in practice: **source-language type *checking* happens in the front end (Clang `Sema`), not in LLVM** — IR arrives already typed.

---

## 1. LLVM's types — examples

```llvm
i1  i8  i32  i64        ; integers of any bit width
half  float  double     ; floating point
ptr                     ; one opaque pointer type (no pointee type since LLVM 15)
[4 x i32]               ; array
{ i32, double }         ; (literal) struct
<4 x float>             ; vector (SIMD)
i32 (i32, ptr)          ; function type: returns i32, takes (i32, ptr)
```
Types are **structural**: two `{ i32, double }` values are interchangeable. Whether `struct Foo` must differ from `struct Bar` despite identical layout is a *source-language* rule, settled before IR exists.

## 2. Storage layout — `DataLayout` + GEP

The type fixes the *shape*; the module's **`DataLayout`** string fixes per-target sizes/alignments; address arithmetic is emitted as [[getelementptr]].

```llvm
; struct S { i32 a; double b; }
%S = type { i32, double }
%p = getelementptr %S, ptr %s, i32 0, i32 1   ; &s->b  (field index 1, always i32)
%v = load double, ptr %p
```
Locals start as `alloca` slots (then usually promoted to SSA registers by `mem2reg`, see [[three-address-code]]).

## 3. Casts are explicit — no implicit coercion

The front end's widening/narrowing conversions become **explicit** cast instructions; LLVM IR never coerces silently:
```llvm
%w = sext  i32 %x to i64     ; signed widen
%n = trunc i64 %y to i32     ; narrow
%f = sitofp i32 %i to double ; int → double
%q = bitcast ptr %p to ptr   ; reinterpret (no bits change)
```

## 4. The verifier — IR-level type consistency

LLVM's **verifier** enforces that the IR is well-typed *structurally*: operand types match the opcode, branch targets are blocks, GEP indices are well-formed, `phi` has one entry per predecessor. It rejects e.g. `add i32 %a, %b` where `%b : i64`. It does **not** re-check source semantics (it has no idea about C's conversion rules).

## 5. Where source type-checking lives

> [!tip] The boundary
> Type-checking **rules**, **conversions**, **overload resolution**, and **inference** are the **front end's** job — in the LLVM world, **Clang `Sema`**. By the time IR is produced, the operator and callee are fixed and every conversion is an explicit cast. Polymorphic **type inference** (ML/Hindley–Milner, and the inference in Rust/Swift) solves type-equality constraints by **[[unification]]** — the very algorithm that also powers Steensgaard/DSA alias analysis. So in this vault, "type checking" is a `frontend`/`clang` topic that *produces* the typed IR the rest of the notes analyze. `Sema` is also where **security-relevant type attributes** are enforced — e.g. `-fbounds-safety`'s `__counted_by` (carried on the [[clang-ast|AST]] as a `CountAttributedType`) — part of the broader front-end analysis layer surveyed in [[source-level-analysis]].

> [!summary] The one thing to remember
> LLVM keeps a **typed, structurally-verified IR** with explicit casts — but the real **type-checking** (rules, conversions, overloading, inference) is the **front end's** job (Clang `Sema`). LLVM assumes well-typed input and never re-checks source semantics.

> [!quote] Further reading
> - **Dragon Book §6.3** (type expressions, equivalence, declarations, storage layout) and **§6.5** (type-checking rules, conversions, overloading, inference & unification) — the language-agnostic theory.
> - [LangRef — Type System](https://llvm.org/docs/LangRef.html#type-system); Clang `Sema`.
