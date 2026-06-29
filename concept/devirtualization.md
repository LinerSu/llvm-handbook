---
title: Devirtualization
facet: concept
stage: optimization
ecosystem: [llvm]
concepts: [interprocedural]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/IPO/WholeProgramDevirt.cpp" }
docs: "doxygen — WholeProgramDevirt ↗ https://llvm.org/doxygen/WholeProgramDevirt_8cpp.html"
book: "Muchnick, Advanced Compiler Design & Implementation §19"
prereqs: [call-graph, inlining]
related: [inlining, call-graph]
tags: [kind/transform, status/verified, version-sensitive]
status: verified
verified_on: 2026-06-28
---

# Devirtualization

> 🧭 **Concept** · `concept · optimization · llvm` · Index [[LLVM.MOC]] · see also [[muchnick.MOC|Muchnick]]
> **Prerequisites:** [[call-graph]], [[inlining]] · vault tracks [[llvm-version]]

> [!abstract] Chapter map
> A virtual / indirect call goes through a function pointer (a vtable slot), so the optimizer can't see the callee — and can't inline it. **Devirtualization** replaces the indirect call with a **direct** one when the target can be pinned down, which then unlocks [[inlining]] and everything downstream.

---

## 1. When a virtual call can become direct

If the dynamic type at a call site is known — a class with a **single implementation** of the method, or a hierarchy narrow enough to enumerate — the indirect call resolves to a concrete function and becomes a direct call.

## 2. In LLVM

> [!info] Two routes
> - **Whole-program devirtualization (`WholeProgramDevirt`, WPD)** — the precise, global form. The front end emits **type metadata** on vtables (`!type`) and `llvm.type.test` / `llvm.type.checked.load` at call sites (under `-fwhole-program-vtables`, typically with LTO). WPD then, across the whole program, turns single-implementation virtual calls into **direct calls**, and uses tricks like *uniform return value* and *branch funnels* for small implementation sets.
> - **Speculative devirtualization** — without whole-program info, guard the most likely target with a **type/pointer check**: `if (vptr == &Foo::m) Foo::m(); else virtual call;`. The direct branch can then be inlined; profitable when one target dominates (often profile-guided).

> [!warning] Version- / build-sensitive
> WPD needs **whole-program visibility** (LTO + `-fwhole-program-vtables`); its availability and aggressiveness depend on the build mode and release. Confirm for your setup — see [[llvm-version]].

> [!summary] The one thing to remember
> Devirtualization turns an **indirect/virtual call into a direct call** when the target is knowable — mainly LLVM's **`WholeProgramDevirt`** using vtable **type metadata** under LTO, plus **speculative** (type-checked, often PGO-driven) devirtualization. The real payoff is the inlining it enables.

> [!quote] Further reading
> - **Source:** [`Transforms/IPO/WholeProgramDevirt.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/IPO/WholeProgramDevirt.cpp)
> - **Muchnick §19** — interprocedural optimization; [LLVM TypeMetadata / WPD docs](https://llvm.org/docs/TypeMetadata.html).
