---
title: Extending LLVM IR
facet: concept
stage: ir
ecosystem: [llvm]
concepts: [llvm-ir]
src: llvm/lib/IR/
docs: "LangRef ↗ https://llvm.org/docs/LangRef.html"
prereqs: [llvm-basics]
related: [getelementptr, pointer-alias-analysis]
tags: [kind/concept, status/verified]
status: verified
verified_on: 2026-06-28
---

# Extending LLVM IR

> 🧭 **Concept** · `concept · ir · llvm` · Index [[LLVM.MOC]]
> **Prerequisites:** [[llvm-basics]] · **Related:** [[getelementptr]], [[ssa-form]]

> [!abstract] Chapter map
> The building blocks you meet when **reading and producing real IR**, and how front ends pass extra knowledge to the optimizer/back end:
> **Instruction → Type → Intrinsic → Parameter attribute → Metadata → Remarks.**

> [!info]+ From classic compiler theory → LLVM
> | What you know | LLVM mechanism |
> |---|---|
> | A fixed opcode set | a small, typed **instruction** set (extended mainly via *intrinsics*, not new opcodes) |
> | A type system over values | LLVM's **first-class types** + aggregates |
> | Compiler "builtins" | **intrinsics** (`@llvm.*`) the optimizer/back end understand specially |
> | ABI annotations (by-value, noalias…) | **parameter attributes** |
> | Side-channel facts that don't change semantics | **metadata** (`!...`) — droppable without affecting correctness |
> | `-Rpass` diagnostics | **optimization remarks** |

---

### 1. Instruction

> [!note] Primer (added)
> LLVM's instruction set is **small, typed, and RISC-like** — `add`/`sub`/`mul`, `load`/`store`, `getelementptr`, `icmp`/`fcmp`, `br`/`switch`, `call`/`ret`, `phi`, casts, etc. Rather than inventing new opcodes, you usually **extend behavior through intrinsics** (below). Full list: [LangRef — Instruction Reference](https://llvm.org/docs/LangRef.html#instruction-reference). Recall the operand model (`User`/`Use`) from [[llvm-basics#5. Core classes (Type, Value, Use)|core classes]].

### 2. Type

> [!note] Primer (added)
> Values are **strongly typed**. Key families: integers `iN` (`i1`, `i8`, `i32`…), floats (`float`, `double`), pointers (modern LLVM uses a single **opaque `ptr`**), and aggregates — arrays `[N x T]`, structs `{ ... }`, and vectors `<N x T>`. Types drive `getelementptr`'s address math (see [[getelementptr]]). Full reference: [LangRef — Type System](https://llvm.org/docs/LangRef.html#type-system).

### 3. Intrinsic

> [!note] Definition
> ==Intrinsics== are "internal" functions whose **semantics are defined directly by LLVM** — builtins the compiler knows how to lower optimally (often to a few machine instructions) for each back end. They also let front ends pass extra facts (e.g. pointer alignment) to the code generator for better codegen.

> [!info] Two flavors
> - **Target-independent** — e.g. `@llvm.memcpy.*`, `@llvm.memset.*`.
> - **Target-specific** — map to a particular ISA's special operations.

> [!example]+ A `memcpy` intrinsic
> ```llvm
> define void @test6(ptr %P) {
>   call void @llvm.memcpy.p0.p0.i64(ptr %P, ptr %P, i64 8, i1 false)
>   ret void
> }
> ```
> LLVM *defines* the meaning of this call — and `MemCpyOpt` will delete this particular one because copying a buffer onto itself has no effect.

> [!tip] Why intrinsics matter
> They make LLVM **extensible**: expose new hardware capabilities (vector ops, atomics, prefetch…) without adding core opcodes or hand-writing assembly.

### 4. Parameter attribute

> [!note] Definition
> The return type and each parameter of a function may carry **parameter attributes** — extra information about the result/arguments that guides optimization and ABI lowering.

> [!example]+ `byval`
> ```llvm
> define i32 @foo(ptr byval(%struct.x) %a) nounwind {
>   ret i32 undef
> }
> ```
> `%a` is passed ==by value== (the callee gets a copy). The `byval` attribute cannot generally be discarded — it changes the ABI. Other common ones: `noalias`, `nocapture`, `nonnull`, `readonly`, `sret`. ([LangRef — parameter attributes](https://llvm.org/docs/LangRef.html#parameter-attributes))

### 5. Metadata

> [!note] Definition
> **Metadata** attaches *optional* information to instructions/modules that can be **dropped without affecting correctness**. It conveys extra hints to optimizers/codegen. Metadata has **no type and is not a `Value`**.

> [!info] Syntax
> - A **metadata string**: text in quotes → `!"test\00"`.
> - A **metadata node**: a brace-delimited list preceded by `!` → `!{ !"test\00", i32 10 }`. Nodes may hold any values as operands.

> [!example]+ `!range` metadata
> ```llvm
> define zeroext i1 @_Z3fooPb(ptr nocapture %x) {
> entry:
>   %a      = load i8, ptr %x, align 1, !range !0
>   %b      = and i8 %a, 1
>   %tobool = icmp ne i8 %b, 0
>   ret i1 %tobool
> }
> !0 = !{ i8 0, i8 2 }
> ```
> `!range !0` tells the optimizer the loaded `%a` is in $[0,2)$, i.e. `0` or `1`. Other uses you'll meet: `!tbaa` (type-based alias info — see [[pointer-alias-analysis]]), `!llvm.loop` (loop hints — see [[loop-transformations]]), debug info.

### 6. Remarks

> [!note] Definition
> **Optimization remarks** are diagnostics emitted by passes describing whether an optimization was performed or missed (and why) — visibility into what the compiler actually did. (Surface them with `-Rpass=`, `-Rpass-missed=`, `-Rpass-analysis=`.)

> [!info] Three kinds
> | Remark | Meaning |
> |---|---|
> | **Passed** | an optimization *succeeded* |
> | **Missed** | an optimization was *attempted but not applied* |
> | **Analysis** | an analysis result that explains the generated code |

> [!quote] Sources
> - [LangRef](https://llvm.org/docs/LangRef.html) — [intrinsics](https://llvm.org/docs/LangRef.html#intrinsic-functions), [parameter attributes](https://llvm.org/docs/LangRef.html#parameter-attributes), [metadata](https://llvm.org/docs/LangRef.html#metadata), [type system](https://llvm.org/docs/LangRef.html#type-system).
> - [Optimization Remarks](https://llvm.org/docs/Remarks.html).
