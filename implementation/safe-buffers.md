---
title: C++ Safe Buffers (-Wunsafe-buffer-usage)
facet: implementation
stage: analysis
ecosystem: [clang]
concepts: [memory-safety]
implements:
  - { ecosystem: clang, src: "clang/lib/Analysis/UnsafeBufferUsage.cpp" }
src: "clang/lib/Analysis/UnsafeBufferUsage.cpp"
docs: "Clang — Safe Buffers ↗ https://clang.llvm.org/docs/SafeBuffers.html"
prereqs: [clang-ast]
related: [fbounds-safety, interprocedural-summaries, clang-ast]
tags: [kind/analysis, status/verified]
status: verified
verified_on: 2026-07-01
---

# C++ Safe Buffers (-Wunsafe-buffer-usage)

> 🧭 **Implementation** · `implementation · analysis · clang` · Index [[LLVM.MOC]]
> **Realizes:** spatial memory safety for C++ · **Prerequisites:** [[clang-ast|Clang AST]] · **Siblings:** [[fbounds-safety]] (the C answer), [[interprocedural-summaries]] (whole-program generalization)

> [!abstract] What this note adds
> The engineering of Clang's **C++ Safe Buffers** model: a *local coding rule* — "no raw pointer arithmetic or unchecked subscript" — enforced by the `-Wunsafe-buffer-usage` warning. The analysis walks the [[clang-ast|AST]] with hand-written **AST matchers**, not the Clang CFG, classifying every unsafe access as a **gadget** (`WarningGadget` = flag it; `FixableGadget` = auto-migrate it) and emitting Fix-Its that rewrite raw pointers to `std::span`/`std::array`. The runtime half is **hardened libc++** (bounds-checked `span::operator[]`). Warnings pick *where* to harden; the library *does* the check.

---

## 1. The component

`clang/lib/Analysis/UnsafeBufferUsage.cpp`, entry `checkUnsafeBufferUsage(const Decl *, UnsafeBufferUsageHandler &, ...)` (declared in `clang/include/clang/Analysis/Analyses/UnsafeBufferUsage.h`). It is invoked from Sema's `AnalysisBasedWarnings.cpp` per function body, and drives the `-Wunsafe-buffer-usage` diagnostic group. It realizes a **programming-model** idea rather than a classic dataflow pass: it recognizes syntactic patterns of unsafe buffer access and, where possible, mechanically rewrites them.

Two ideas ride together:
- ***the local rule*** — a function is "safe" if it contains no raw pointer arithmetic and no unchecked subscript on a raw pointer. This is checkable *syntactically*, one statement at a time — which is exactly why an AST walk (not a path-sensitive engine) suffices.
- ***the migration path*** — for each unsafe pattern the analysis also knows the *fix* (turn the raw pointer into a `std::span`), so adoption is a compiler-assisted refactor, not a manual rewrite.

## 2. What it realizes (and why promoted)

It gets its own note because it is a distinct **memory-safety mechanism**, not another optimization: it is a *bug-prevention coding standard baked into the compiler*. Contrast the two Clang spatial-safety stories:

> [!info] C `-fbounds-safety` vs. C++ Safe Buffers
>
> | Axis | [[fbounds-safety]] (C) | Safe Buffers (C++) |
> |---|---|---|
> | Mechanism | **type-system** extension (`__counted_by` bounds annotations + implicit wide pointers) + inserted **runtime traps** | **warning** (`-Wunsafe-buffer-usage`) + **library** bounds checks |
> | When it fires | compile-time type rules **and** runtime trap on out-of-bounds | compile-time warning; runtime check lives in hardened libc++ |
> | Adoption | annotate pointer types | replace raw pointers with `std::span`/`std::array` (Fix-Its help) |
> | Enforcement point | the language/ABI | the standard library container |

Safe Buffers deliberately keeps the language unchanged: the "safe pointer" is just `std::span`, and the "check" is `span::operator[]` in **hardened libc++**. The compiler's only job is to *point at* the raw-pointer code that must migrate.

## 3. Where it runs

- It is an **AST-based warning**, run from Sema's analysis-based warnings after a function body is built — *not* part of `-O2` codegen and *not* on the CFG.
- Enabled with `-Wunsafe-buffer-usage` (the group is `DefaultIgnore` — off unless requested). The Fix-Its are surfaced with `-fsafe-buffer-usage-suggestions`.
- The runtime companion is orthogonal: `-D_LIBCPP_HARDENING_MODE=…` selects a hardened libc++ so `span`/`array` subscripts trap.

## 4. How it's built — the gadget model

The analysis walks the AST and buckets every relevant expression into a **gadget** — a small object wrapping one matched AST node plus the logic to warn about it or fix it. The hierarchy is a two-way split under a common base:

> [!note] The gadget hierarchy (`UnsafeBufferUsage.cpp`)
>
> | Type | Role |
> |---|---|
> | `Gadget` | abstract base; a `Kind` enum (from `UnsafeBufferUsageGadgets.def`) + `matches`/`getClaimedVarUseSites` |
> | `WarningGadget` | an **unsafe operation** that warrants an immediate warning; `handleUnsafeOperation(...)` calls back into the handler. E.g. `ArraySubscriptGadget`, `PointerArithmeticGadget`, `IncrementGadget`/`DecrementGadget` |
> | `FixableGadget` | a pattern that isn't itself unsafe but must be **recognized to emit a coherent fix** (e.g. a pointer assignment that couples two variables' types); supplies `getFixits(strategy)` and `getStrategyImplications()` |
> | `UnsafeBufferUsageHandler` | the caller-supplied sink (`clang/include/…/UnsafeBufferUsage.h`) — `handleUnsafeOperation`, `handleUnsafeLibcCall`, `handleUnsafeVariableGroup`; the Sema subclass turns these into diagnostics + Fix-Its |

Matching is **hand-written**, not the classic `MatchFinder` DSL: each gadget exposes a static `matches(const Stmt *, ASTContext &, MatchResult &)`, and a `WarningGadgetMatcher` / `FixableGadgetMatcher` (both `FastMatcher`s) run them while `forEachDescendantEvaluatedStmt` walks the body. This is still AST-matcher-style pattern recognition over the [[clang-ast|AST]] — just tuned for speed on every compile.

The two-phase shape: collect **warning** gadgets (what to flag) and **fixable** gadgets (what a migration would touch), group the variables whose types must change together, then either emit warnings or, under `-fsafe-buffer-usage-suggestions`, a `std::span`-typed Fix-It for the whole group.

## 5. A flagged subscript

> [!example]+ An unsafe subscript warns; the safe form doesn't
> ```cpp
> void f(int *p, unsigned i) {
>   int a = p[i];   // WARN: unsafe buffer access  (-Wunsafe-buffer-usage)
>   int b = p[0];   // no warning — literal-0 index is treated as safe
> }
> ```
> ```
> clang -Wunsafe-buffer-usage -std=c++20 f.cpp
> warning: unsafe buffer access [-Wunsafe-buffer-usage]
> ```
> `p[i]` matches `ArraySubscriptGadget` (a `WarningGadget`): the base has pointer type and the index is not a literal zero, so `matches` returns true and the handler emits the diagnostic. `p[0]` is skipped — `ArraySubscriptGadget::matches` treats a literal-zero (or an `ArrayInitIndexExpr`) index as safe. The fix is to make `p` a `std::span<int>`, after which `p[i]` is a bounds-checked call under hardened libc++.

## 6. Warning → runtime: hardened libc++

The warning has **no runtime effect on its own** — it just relocates each raw-pointer access onto a library container. The actual bounds check is `std::span::operator[]` / `std::array::operator[]` under a **hardened libc++** mode (`_LIBCPP_HARDENING_MODE`), which asserts (and traps) on out-of-bounds. So Safe Buffers is a *division of labour*: the analysis proves nothing about values; it only guarantees that every buffer access flows through a container whose subscript is checked. Contrast [[fbounds-safety]], where the trap is inserted by the compiler into the C code itself.

## 7. Whole-program generalization

The local rule is intraprocedural: it flags a raw pointer crossing a function boundary but can't reason about the callee. Extending spatial safety across calls needs **function-level bounds contracts** — the direction captured by [[interprocedural-summaries]] and the broader "Scalable" whole-program safety framework: summarize each function's buffer-bounds pre/post-conditions so a caller's safety can be discharged against a callee's summary rather than re-analyzed. Safe Buffers is the per-function leaf of that story.

## 8. Limitations & version notes

> [!warning] What it will and won't do
> - **Syntactic, per-statement, intraprocedural.** It recognizes *patterns of access*, not *values*: it cannot prove an index in-range, so it flags the operation regardless of provability (that's the point — the check is deferred to the library). It does not follow calls.
> - **`DefaultIgnore`.** The group is off unless `-Wunsafe-buffer-usage` is passed; Fix-Its need `-fsafe-buffer-usage-suggestions`.
> - **Fixes are best-effort.** A `FixableGadget` returns `std::nullopt` when it can't produce a coherent rewrite; grouped variables that can't all migrate cleanly are left for the human.
> - **Runtime safety is opt-in and separate.** Without a hardened libc++, migrating to `std::span` moves the code past the warning but adds no runtime check. `version-sensitive` — gadget set, sub-groups (`unsafe-buffer-usage-in-container`, `…-in-libc-call`), and libc++ hardening knobs evolve release to release → [[llvm-version]].

> [!summary] The one thing to remember
> **C++ Safe Buffers = a local rule ("no raw pointer arithmetic/subscript") the compiler enforces by AST-matcher gadgets.** `-Wunsafe-buffer-usage` flags each unsafe access (`WarningGadget`) and offers Fix-Its (`FixableGadget`) that migrate raw pointers to `std::span`/`std::array`; the real bounds check happens later, in **hardened libc++**. It is the C++ counterpart to [[fbounds-safety]]'s type-system-plus-trap approach in C.

> [!quote] Sources & confidence
> - **Tier-1 source (pinned tag):** [`clang/lib/Analysis/UnsafeBufferUsage.cpp`](https://github.com/llvm/llvm-project/blob/main/clang/lib/Analysis/UnsafeBufferUsage.cpp) and [`clang/include/clang/Analysis/Analyses/UnsafeBufferUsage.h`](https://github.com/llvm/llvm-project/blob/main/clang/include/clang/Analysis/Analyses/UnsafeBufferUsage.h) — the `Gadget` / `WarningGadget` / `FixableGadget` / `UnsafeBufferUsageHandler` classes, the AST-matcher (`matches` + `forEachDescendantEvaluatedStmt`) walk, and `ArraySubscriptGadget`/`PointerArithmeticGadget` were read directly from these files. Warning group `UnsafeBufferUsage` confirmed in [`DiagnosticGroups.td`](https://github.com/llvm/llvm-project/blob/main/clang/include/clang/Basic/DiagnosticGroups.td); diagnostics `warn_unsafe_buffer_*` in `DiagnosticSemaKinds.td`; driven from `clang/lib/Sema/AnalysisBasedWarnings.cpp`.
> - **Primary docs:** [Clang — Safe Buffers](https://clang.llvm.org/docs/SafeBuffers.html); hardened libc++ hardening modes in the libc++ docs.
