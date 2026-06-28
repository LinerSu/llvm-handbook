---
title: GetElementPtr (GEP)
facet: concept
stage: ir
ecosystem: [llvm]
concepts: [llvm-ir, addressing]
src: llvm/lib/IR/Instructions.cpp
docs: "The Often Misunderstood GEP ↗ https://llvm.org/docs/GetElementPtr.html"
prereqs: [llvm-basics]
related: [pointer-alias-analysis]
tags: [kind/concept, status/verified]
status: verified
verified_on: 2026-06-28
---

# GetElementPtr (GEP) — address computation in LLVM IR

> 🧭 **Concept** · `concept · ir · llvm` · companion to [[llvm-basics]] · Index [[LLVM.MOC]]
> **Prerequisites:** [[llvm-basics]] · **Related:** [[pointer-alias-analysis]]

> [!abstract] Chapter map
> 1. The one-sentence truth: **GEP computes an address; it never touches memory.**
> 2. How indices work — and why the **first index steps the pointer**.
> 3. The famous **extra `0`** and "no superfluous indices".
> 4. **`inbounds`**, overflow/`poison`, and GEP's **aliasing contract**.

> [!info]+ From classic compiler theory → LLVM
> | What you already know | LLVM realization |
> |---|---|
> | Array indexing `a[i]` = `base + i*sizeof(elem)` | `getelementptr` with element type + indices |
> | Field selection `s.f` = `base + offsetof(f)` | a struct index (always `i32`) into the type |
> | Address-of `&expr` (no load) | GEP — pure address arithmetic, **no dereference** |
> | Pointer arithmetic + aliasing assumptions | GEP carries **extra aliasing rules** the optimizer relies on |
>
> Mental model: GEP is the **typed `&` operator**. `load`/`store` are the only things that touch memory.

---

### 1. What GEP is (and is not)

> [!note] Definition
> `getelementptr` performs **address calculation** from a base pointer and a list of indices, guided by an LLVM type. ==It dereferences nothing== — that's what `load`/`store` are for. *(Source: LLVM "The Often Misunderstood GEP Instruction".)*

> [!warning] The #1 confusion: the **first index steps through the pointer**
> GEP is **not** the C `[]` operator. In C, `&Foo->F` looks like a single field selection — but `Foo` is a pointer that must be indexed *explicitly* in LLVM. The equivalent C is `&Foo[0].F`: the first index walks the pointer (`[0]`), the second selects the field.
> No memory is read to do this — the pointer **value** is already an operand.

> [!example]+ Clang lowering `P[0].f1 = P[1].f1 + P[2].f2;`
> ```c
> struct munger_struct { int f1; int f2; };
> void munge(struct munger_struct *P) {
>   P[0].f1 = P[1].f1 + P[2].f2;
> }
> ```
> ```llvm
> define void @munge(ptr %P) {
> entry:
>   %tmp  = getelementptr %struct.munger_struct, ptr %P, i32 1, i32 0  ; &P[1].f1
>   %tmp1 = load i32, ptr %tmp
>   %tmp2 = getelementptr %struct.munger_struct, ptr %P, i32 2, i32 1  ; &P[2].f2
>   %tmp3 = load i32, ptr %tmp2
>   %tmp4 = add i32 %tmp3, %tmp1
>   %tmp5 = getelementptr %struct.munger_struct, ptr %P, i32 0, i32 0  ; &P[0].f1
>   store i32 %tmp4, ptr %tmp5
>   ret void
> }
> ```
> Every GEP's **second operand** is the base pointer `%P`; the **first index** (`1`, `2`, `0`) steps through it; the **second index** picks the field.

---

### 2. Indices are byte offsets *derived from types*

> [!example]+ Offsets from a base
> ```llvm
> @MyVar = external global i32
> %idx1 = getelementptr i32, ptr @MyVar, i64 0   ; &MyVar + 0
> %idx2 = getelementptr i32, ptr @MyVar, i64 1   ; &MyVar + 4
> %idx3 = getelementptr i32, ptr @MyVar, i64 2   ; &MyVar + 8
> ```
> Because `i32` is 4 bytes, indices `0,1,2` ⇒ offsets `0,4,8`. No memory is touched — the address of `@MyVar` is passed directly.

> [!warning] Why the extra `0`? — "there are no superfluous indices"
> For a global `%MyStruct` of type `{ ptr, i32 }`, the *value* `%MyStruct` has type `ptr` (a pointer **to** the struct), not the struct itself. So:
> ```llvm
> %idx = getelementptr { ptr, i32 }, ptr %MyStruct, i64 0, i32 1
> ```
> - `i64 0` — step over the pointer (0 elements from it);
> - `i32 1` — select the second field.
>
> Drop the `0` and you'd be selecting a field of *the pointer*, which is wrong.

> [!tip] When GEP can't do it in one shot
> GEP can index *through* aggregates but **cannot dereference**. If a pointer sits **inside** the structure, you need a `load` in between:
> ```llvm
> @MyVar = external global { i32, ptr }            ; inner pointer
> %idx = getelementptr { i32, ptr }, ptr @MyVar, i64 0, i32 1
> %arr = load ptr, ptr %idx                        ; <-- must load
> %e   = getelementptr [40 x i32], ptr %arr, i64 0, i64 17
> ```
> Versus an embedded array (no pointer hop) which is a single GEP:
> ```llvm
> @MyVar = external global { i32, [40 x i32] }
> %idx = getelementptr { i32, [40 x i32] }, ptr @MyVar, i64 0, i32 1, i64 17
> ```

---

### 3. GEP and aliasing (why it matters for alias analysis)

> [!note] Leading vs. trailing zero indices
> - **Leading** zeros are *not* superfluous — they affect the address and aliasing.
> - **Trailing** zeros don't change the address (indexing element 0 of the last aggregate), so `GEP x,1,0,0` and `GEP x,1` **alias**; but `GEP x,0,0,1` and `GEP x,1` **don't** (they diverge at the first index).

> [!warning] `inbounds`, overflow, and `poison`
> - With **`inbounds`**: the result is `poison` if it leaves the underlying allocated object (other than one-past-the-end) or if the offset arithmetic wraps the address space. Optimizers *rely* on this to reason about non-aliasing.
> - Without `inbounds`: out-of-bounds address *computation* is allowed (it's just integer math); only an actual `load`/`store` then needs valid memory.
> - Indices may be **negative** (`gep i32, ptr %P, i32 -1`); the base is treated as unsigned, the offset as signed (an asymmetric, `nsw`-scaled relation).

> [!tip] GEP vs. `ptrtoint`/`inttoptr` arithmetic
> Same underlying integer math, but GEP additionally carries the **pointer-aliasing contract**: you may not GEP from object A into separately-allocated object B and dereference it. Alias analysis depends on that promise; the `ptrtoint → add → inttoptr` path deliberately drops most of these guarantees.

---

> [!summary] Five things to always remember
> 1. GEP **never accesses memory** — it only computes addresses.
> 2. The **second operand is the base pointer** and must be indexed.
> 3. There are **no superfluous indices**.
> 4. **Trailing** zero indices are superfluous for *aliasing* (but not for types).
> 5. **Leading** zero indices are superfluous for *neither* aliasing nor types.

> [!quote] Sources
> - [The Often Misunderstood GEP Instruction](https://llvm.org/docs/GetElementPtr.html)
> - [LangRef — `getelementptr`](https://llvm.org/docs/LangRef.html#getelementptr-instruction) · [Pointer aliasing rules](https://llvm.org/docs/LangRef.html#pointeraliasing)
