---
title: Function Specialization (Cloning)
facet: concept
stage: optimization
ecosystem: [llvm]
concepts: [interprocedural]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/IPO/FunctionSpecialization.cpp" }
docs: "IPO FunctionSpecialization ↗ https://llvm.org/doxygen/FunctionSpecialization_8cpp_source.html"
book: "Muchnick, Advanced Compiler Design & Implementation §19"
prereqs: [ipsccp, inlining]
related: [ipsccp, inlining]
tags: [kind/transform, status/verified, version-sensitive]
status: verified
verified_on: 2026-06-28
---

# Function Specialization (Cloning)

> 🧭 **Concept** · `concept · optimization · llvm` · Index [[LLVM.MOC]] · see also [[muchnick.MOC|Muchnick]]
> **Prerequisites:** [[ipsccp]], [[inlining]] · vault tracks [[llvm-version]]

> [!abstract] Chapter map
> When a function is called with a **constant argument at many sites** but [[inlining]] each call is too costly (or impossible), specialization **clones** the function with that argument fixed, so the clone's body can be optimized for it — capturing much of inlining's benefit without inlining's code growth.

---

## 1. The idea

> [!info] Clone-and-fix
> If callers pass a recurring constant (a flag, a size, a function pointer), a specialized **clone** with that parameter pinned can be constant-folded, branch-pruned, and devirtualized internally; the matching call sites are redirected to the clone. It sits **between inlining and [[ipsccp|IPSCCP]]**: inlining specializes *at one site* by copying the body; specialization makes *one shared specialized copy* for many sites.

> [!example]
> ```c
> int run(Mode m, Data *d) { if (m == FAST) {…} else {…} }
> // called as run(FAST, …) in dozens of places
> ```
> Specialize `run` for `m == FAST` → the clone drops the branch and the slow path; the FAST call sites use it. Inlining all of them would bloat code; one specialized clone won't.

## 2. In LLVM

LLVM's **`FunctionSpecialization`** finds arguments that are frequently a common constant and creates specialized versions, guided by a **cost model** (benefit of folding vs. the size of an extra clone). It **depends on [[ipsccp|IPSCCP]]** (to know which arguments are constant and propagate them) and on **dead-argument elimination** to clean up afterward.

> [!warning] Version-sensitive
> Function specialization is a **relatively recent** pass whose default enablement and aggressiveness have changed across releases (and is integrated with the IPSCCP pipeline). Confirm its status for your version — see [[llvm-version]].

> [!summary] The one thing to remember
> Specialization = **clone a function with a recurring constant argument fixed**, so the clone optimizes for it — inlining's payoff without inlining's bloat. LLVM's `FunctionSpecialization` is cost-model-gated and built on IPSCCP.

> [!quote] Further reading
> - **Source:** [`Transforms/IPO/FunctionSpecialization.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/IPO/FunctionSpecialization.cpp)
> - **Muchnick §19** — procedure specialization and cloning.
