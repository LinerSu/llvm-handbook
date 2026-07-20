---
title: Clang CodeGen (lowering the AST to LLVM IR)
facet: implementation
stage: ir
ecosystem: [clang]
concepts: [intermediate-code, control-flow-translation, source-level-analysis]
implements:
  - { ecosystem: clang, src: "clang/lib/CodeGen" }
src: "clang/lib/CodeGen"
docs: "Clang Internals Manual — The CodeGen Library ↗ https://clang.llvm.org/docs/InternalsManual.html"
prereqs: [clang-ast, llvm-basics]
related: [clang-frontend-pipeline, control-flow-translation, clang-ast, code-generation-overview, mem2reg, running-example]
tags: [kind/pass, status/verified]
status: verified
verified_on: 2026-07-20
---

# Clang CodeGen (lowering the AST to LLVM IR)

> 🧭 **Implementation** · `implementation · ir · clang` · Index [[LLVM.MOC]]
> **Realizes:** intermediate-code generation (AST → IR) · **Prerequisites:** [[clang-ast]], [[llvm-basics]] · **Consumes:** the [[clang-ast|Clang AST]] · **Produces:** unoptimized [[llvm-basics|LLVM IR]]

> [!abstract] What this note adds
> The stage *after* [[clang-frontend-pipeline|Lex → Parse → Sema → AST]] and the exact boundary where source fidelity ends: **`clang/lib/CodeGen`** walks the typed [[clang-ast|AST]] and emits LLVM IR. Its defining trait is that it emits **naïve, `alloca`-heavy IR** — every local becomes a stack slot with explicit `load`/`store` — leaving all optimization (starting with [[mem2reg]]) to the middle end. Two state classes carry the walk: **`CodeGenModule`** (cross-function state, *"organizes the cross-function state … while generating LLVM code"*) and **`CodeGenFunction`** (*"the per-function state"*), of which only `CodeGenFunction` holds an `IRBuilder`. Not to be confused with [[code-generation-overview|LLVM CodeGen]], which is the *backend* (IR → machine code).

---

## 1. The pass

**Clang CodeGen** (`clang/lib/CodeGen`) is the front-end component that lowers the AST into LLVM IR. It is driven as an **`ASTConsumer`**: `CodeGenerator` *is a* `ASTConsumer` (`CodeGeneratorImpl` in `ModuleBuilder.cpp`), so the [[clang-frontend-actions|frontend action]] feeds it each top-level `Decl` and it emits the corresponding IR. It realizes what the Dragon Book calls *intermediate-code generation*; the control-flow slice of it (branches, loops, `&&`, φ) is detailed separately in [[control-flow-translation]].

## 2. What it realizes (and why promoted)

This is the concrete answer to *"how does a `for` loop / a `+` / a virtual call become IR?"* — the counterpart on the Clang side of the LLVM-side lowering notes. It earns its own note because CodeGen is where **the AST's source information is deliberately discarded** (see [[clang-ast]] §Limitations): the sugar-preserving, source-located tree collapses into SSA-able three-address IR. Everything a source-level analysis needs ([[source-level-analysis]]) must be read *before* this point.

## 3. Where it runs

Immediately after Sema produces (part of) the AST, and before the LLVM optimizer. The two state classes divide the work by scope:

> [!info] The two CodeGen state classes (confirmed, pinned Clang [[llvm-version]])
>
> | Class | Scope | Header comment |
> |---|---|---|
> | `CodeGenModule` | per **module** (globals, types, vtables, linkage) | *"organizes the cross-function state that is used while generating LLVM code"* |
> | `CodeGenFunction` | per **function** (locals, the IR builder, one `llvm::Function`) | *"organizes the per-function state that is used while generating LLVM code"* |

`CodeGenFunction` builds instructions through its `CGBuilderTy Builder` (a thin wrapper over LLVM's `IRBuilder`). `CodeGenModule` has **no** builder at all — globals, constants and vtables are not instructions and have no insertion point, so it emits them directly.

## 4. How it's built — the emit walk

CodeGen is a recursive walk over `Stmt`/`Expr`, one *emit* method per node kind:

- **Statements** → `CodeGenFunction::EmitStmt` (`CGStmt.cpp`) dispatches on statement kind.
- **Expressions** → `EmitScalarExpr` / `EmitLValue` (`CGExpr.cpp`, `CGExprScalar.cpp`, `CGExprAgg.cpp`) — an *rvalue* is emitted as a value, an *lvalue* as an address.
- **Calls & ABI** → `CGCall.cpp` implements the platform **calling convention** (how arguments are classified and passed) — the hardest, most target-specific part of CodeGen.
- **C++** → `CGClass.cpp` (constructors, vtables, `this` adjustment), `CGException.cpp` (`invoke`/landing pads).

## 5. Textbook → Clang (what the emitted IR looks like)

> [!info]+ Where real CodeGen differs from "just translate the tree"
>
> | Naïve expectation | What Clang CodeGen actually does |
> |---|---|
> | Locals become SSA values | Every local becomes an **`alloca`** with explicit `load`/`store`; *locals* are not promoted to SSA registers here — [[mem2reg]] does that later (CodeGen does emit `phi` directly for short-circuit and ternary operators) |
> | One clean value per expression | Redundant reloads are emitted freely (two `load`s of the same var); the optimizer cleans up |
> | Types carry through | Pointee types are dropped (opaque `ptr`); only operation-level type info survives |

The alloca-heavy shape is deliberate: it keeps CodeGen simple and correct, and hands a uniform starting point to the optimizer.

## 6. Run it yourself

> [!example]+ See the front-end IR (before any optimization)
> ```bash
> clang -O0 -emit-llvm -S -fno-discard-value-names -Xclang -disable-O0-optnone cg.c -o -
> ```
> For `int f(int a) { return a*a + 1; }`:
>
> ```llvm
> define i32 @f(i32 noundef %a) #0 {
> entry:
>   %a.addr = alloca i32, align 4      ; the local 'a' is a stack slot
>   store i32 %a, ptr %a.addr, align 4
>   %0 = load i32, ptr %a.addr, align 4
>   %1 = load i32, ptr %a.addr, align 4 ; reloaded, not reused — optimizer's job
>   %mul = mul nsw i32 %0, %1          ; 'nsw' from signed-int semantics Sema recorded
>   %add = add nsw i32 %mul, 1
>   ret i32 %add
> }
> ```
> The `nsw` (no-signed-wrap) flags are CodeGen translating a *semantic* fact (signed overflow is UB) into an IR flag. The fuller picture — a whole function with a loop, then `mem2reg` — is [[running-example#2. Front-end IR — everything is a stack slot|running example §2]].

## 7. Flags & knobs

`-emit-llvm -S` emits textual `.ll` and `-emit-llvm -c` emits bitcode `.bc` (`-emit-llvm-bc` is the `-cc1`-only spelling the driver passes internally, not a driver flag); `-O0` with `-Xclang -disable-O0-optnone` lets you see un-`optnone` front-end IR you can then feed to `opt` one pass at a time. `-fno-discard-value-names` keeps readable `%a.addr`-style names.

## 8. Siblings & variants

- [[control-flow-translation]] — the branch/loop/φ slice of this same walk.
- [[code-generation-overview]] — the **backend** that takes this IR to machine code (different meaning of "code generation").
- ClangIR (CIR) — an emerging MLIR-based path that inserts a higher-level IR *between* the AST and LLVM IR (out of scope here).

## 9. Limitations & version notes

> [!warning] What CodeGen won't do
> - **It does not optimize.** Reloads, redundant `alloca`s, and dead code are emitted on purpose; the middle end removes them.
> - **ABI is target law, not choice.** `CGCall` must match the platform ABI exactly (struct-by-value classification, `sret`, varargs) — a mismatch is silent miscompilation, which is why it is the most intricate corner of CodeGen.
> - **It is the point of no return for source info.** After CodeGen, an analysis sees only IR; source-directed checks must run on the AST ([[source-level-analysis]]).

> [!summary] The one thing to remember
> `clang/lib/CodeGen` walks the typed AST as an `ASTConsumer` and emits **naïve, alloca-heavy LLVM IR** — `CodeGenModule` for module state, `CodeGenFunction` (with an `IRBuilder`) per function. It does not build SSA or optimize; [[mem2reg]] and the middle end do. This is the boundary where the AST's source fidelity is dropped.

> [!quote] Sources & confidence
> **Verified 2026-07-20** — every falsifiable claim in this note was enumerated and checked against the pinned Clang source ([[llvm-version]], `llvmorg-22.1.8`) by the `note-correctness-review` pass; refuted claims were corrected (batch error rate 8.6%, 23/269). GitHub links track `main`; the checked revision is the pinned tag.
> - [clang/lib/CodeGen/CodeGenModule.h](https://github.com/llvm/llvm-project/blob/main/clang/lib/CodeGen/CodeGenModule.h) — *"organizes the cross-function state … while generating LLVM code."*
> - [clang/lib/CodeGen/CodeGenFunction.h](https://github.com/llvm/llvm-project/blob/main/clang/lib/CodeGen/CodeGenFunction.h) — *"the per-function state";* `CGBuilderTy Builder`.
> - [clang/lib/CodeGen/CGStmt.cpp](https://github.com/llvm/llvm-project/blob/main/clang/lib/CodeGen/CGStmt.cpp) — `CodeGenFunction::EmitStmt`; [`CGExpr.cpp`](https://github.com/llvm/llvm-project/blob/main/clang/lib/CodeGen/CGExpr.cpp) — `EmitLValue`/`EmitScalarExpr`; `CGCall.cpp`, `CGClass.cpp`, `CGException.cpp`.
> - [clang/lib/CodeGen/ModuleBuilder.cpp](https://github.com/llvm/llvm-project/blob/main/clang/lib/CodeGen/ModuleBuilder.cpp) — `CodeGeneratorImpl : public CodeGenerator`; `CodeGenerator : public ASTConsumer`.
> - Example IR produced locally with **Apple clang 17** (Apple's own versioning — *not* an upstream LLVM release number, and not the pinned tag; cosmetics track the clang version — see [[llvm-version]]). Lowering strategy is version-stable.
