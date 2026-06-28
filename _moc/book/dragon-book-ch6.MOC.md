---
title: Dragon Book Ch.6 — Intermediate-Code Generation → LLVM
type: book-moc
book: "Aho, Lam, Sethi, Ullman — Compilers: Principles, Techniques & Tools (Dragon Book, 2e)"
chapter: 6
tags: [moc, kind/moc, book]
status: draft
verified_on: 2026-06-28
---

# Dragon Book Ch.6 — Intermediate-Code Generation → LLVM

> 🧭 **Book bridge** · Chapter of [[Home]] · ecosystem map [[LLVM.MOC]]
> **Source:** Dragon Book (2e) Chapter 6, pp. 357–425.

> [!abstract] What this bridge delivers
> A **reading map**: if you're reading Dragon Book Chapter 6, this points each section to the vault note that covers the same idea **in LLVM**. The vault notes describe LLVM directly (with examples); the book is the optional companion for the language-agnostic theory. The shared thesis: **typed three-address code in SSA form is the right waist** between front ends and back ends.

## 🗂 Section-by-section crosswalk

| § | Book topic | LLVM realization | Vault note |
|---|---|---|---|
| 6.1.1 | DAGs for expressions | shared subexpressions ⇒ reuse | [[value-numbering]] |
| 6.1.2 | **Value-number method** for DAGs | LVN/GVN value-number table *is* the DAG | [[value-numbering]] |
| 6.2 | **Three-address code** (addresses, instructions) | LLVM IR *is* 3AC: `%x = op ty %a, %b` | [[three-address-code]] |
| 6.2.2–3 | Quadruples / triples | in-memory `Instruction` (quadruple-like; SSA value = result) | [[three-address-code]] |
| 6.2.4 | **Static single-assignment form** | LLVM IR is intrinsically SSA | [[ssa-form]] |
| 6.3.1–2 | Type expressions; equivalence | LLVM structural types (`iN`,`[N x T]`,`{…}`,`ptr`) | [[type-checking]], [[extending-llvm-ir]] |
| 6.3.3–6 | Declarations; **storage layout**; fields | `alloca` + `DataLayout` + GEP offsets | [[type-checking]], [[getelementptr]] |
| 6.4.1–2 | Translation of expressions; temporaries | `IRBuilder` emits 3AC; SSA temporaries | [[three-address-code]] |
| 6.4.3–4 | **Addressing array elements** / array refs | `base + i × w` ⇒ `getelementptr` | [[getelementptr]] |
| 6.5.1–3 | Type checking; conversions; overloading | **Clang `Sema`** (front end); explicit IR casts | [[type-checking]] |
| 6.5.4 | Type inference / polymorphism | HM inference in ML/Rust/Swift front ends | [[type-checking]] |
| 6.5.5 | **An algorithm for unification** | type inference **and** Steensgaard/DSA alias | [[unification]] |
| 6.6 | Control flow; **short-circuit** booleans | `br i1` between basic blocks; jumping code | [[control-flow-translation]] |
| 6.7 | **Backpatching** (one-pass labels) | not needed — real `BasicBlock` refs + `mem2reg`/φ | [[control-flow-translation]] |
| 6.8 | Switch-statements | `switch` instruction; table/tree in codegen | [[control-flow-translation]] |
| 6.9 | Intermediate code for procedures | `call`/`ret`, calling conventions | [[llvm-basics]] |

## 📚 Suggested reading path (book ↔ vault)

1. **§6.2 → [[three-address-code]]** then **§6.2.4 → [[ssa-form]]** — the IR shape.
2. **§6.1 → [[value-numbering]]** — the expression DAG and its reuse.
3. **§6.3 → [[type-checking]]** and **§6.4.3 → [[getelementptr]]** — types, layout, addressing.
4. **§6.5.5 → [[unification]]** — then follow it *sideways* into [[pointer-alias-analysis]] (the same algorithm!).
5. **§6.6–6.8 → [[control-flow-translation]]** — booleans, backpatching, switch → a CFG ([[control-flow-graph]]).

## 📝 Reading notes — what's different in modern LLVM

> [!info] Three things to keep in mind while reading the book
> - **SSA is not optional.** The book presents SSA as one 3AC *variant* (§6.2.4); in LLVM every value is SSA by construction.
> - **No backpatching.** §6.7's truelist/falselist machinery is a one-pass artifact; LLVM builds a CFG of real blocks and resolves merges with `phi` / `mem2reg` (see [[dominator-tree]]).
> - **Opaque pointers + `DataLayout`.** The book's storage-layout arithmetic is split into a target-independent `getelementptr` plus a per-target `DataLayout`; pointers are now type-erased (`ptr`).

```dataview
TABLE facet, stage, ecosystem, status
WHERE book AND contains(book, "Dragon")
SORT file.name ASC
```
