---
title: Garbage-Collection Support (Statepoints)
facet: concept
stage: codegen
ecosystem: [llvm]
concepts: [garbage-collection, code-generation]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/Scalar/RewriteStatepointsForGC.cpp" }
docs: "Garbage Collection Safepoints in LLVM ↗ https://llvm.org/docs/Statepoints.html"
book: "Dragon Book (Aho/Lam/Sethi/Ullman, 2e) §7.5"
prereqs: [code-generation-overview]
related: [code-generation-overview]
tags: [kind/transform, status/verified]
status: verified
verified_on: 2026-06-28
---

# Garbage-Collection Support (Statepoints)

> 🧭 **Concept** · `concept · codegen · llvm` · Index [[LLVM.MOC]] · the LLVM sliver of Dragon Ch.7
> **Prerequisites:** [[code-generation-overview]]

> [!abstract] Chapter map
> LLVM **does not ship a garbage collector** — it provides the **infrastructure** for a language runtime to implement a precise, *relocating* GC: the `gc.statepoint` / `gc.relocate` intrinsics and the `RewriteStatepointsForGC` pass, which make every live managed pointer **findable and updatable** at each point GC might run.

---

## 1. The problem GC poses to a compiler

A **precise relocating** collector may **move** live objects, so at any **safepoint** (a call that might trigger collection) the runtime must (a) **find** every live GC pointer on the stack/in registers and (b) **update** it to the object's new address. The compiler has to surface that information; the runtime does the collecting.

## 2. In LLVM — statepoints

> [!info] `RewriteStatepointsForGC`
> The **`RewriteStatepointsForGC`** pass lowers from an abstract model (GC pointers in a dedicated address space) to the explicit **statepoint** model: it replaces calls that might reach a safepoint with a **`gc.statepoint`**, followed by a **`gc.relocate`** for each live GC pointer — so after the call the program uses the *relocated* value. It distinguishes **base pointers** (start of an allocation) from **derived pointers** (offset into one), duplicating code as needed so the collector can relocate a derived pointer to the same offset from the moved base. The recorded live-pointer sets become **stack maps** the runtime reads at GC time.

> [!info] Strategies
> A function opts in with a **GC strategy** (`gc "statepoint-example"`, or a custom one); the older **shadow-stack** approach is simpler but slower. The front end (for a managed language) emits the GC-pointer address space and the strategy; LLVM threads the pointers through to the stack maps.

> [!summary] The one thing to remember
> LLVM supplies **GC plumbing, not a collector**: `RewriteStatepointsForGC` turns calls into **`gc.statepoint` + `gc.relocate`** sequences and emits **stack maps** of live base/derived GC pointers, so a relocating runtime can find and move them at safepoints.

> [!quote] Further reading
> - **Source:** [`Transforms/Scalar/RewriteStatepointsForGC.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Scalar/RewriteStatepointsForGC.cpp)
> - **Dragon Book §7.5** — introduction to garbage collection; [Garbage Collection Safepoints in LLVM](https://llvm.org/docs/Statepoints.html).
