---
title: If-Conversion (Predication)
facet: concept
stage: codegen
ecosystem: [llvm]
concepts: [control-flow]
implements:
  - { ecosystem: llvm, src: "llvm/lib/CodeGen/IfConversion.cpp" }
  - { ecosystem: llvm, src: "llvm/lib/CodeGen/EarlyIfConversion.cpp" }
docs: "CodeGenerator ↗ https://llvm.org/docs/CodeGenerator.html"
book: "Muchnick, Advanced Compiler Design & Implementation §18"
prereqs: [control-flow-graph, instruction-scheduling]
related: [simplifycfg, instruction-scheduling]
tags: [kind/transform, status/verified, version-sensitive]
status: verified
verified_on: 2026-06-28
---

# If-Conversion (Predication)

> 🧭 **Concept** · `concept · codegen · llvm` · Index [[LLVM.MOC]] · see also [[muchnick.MOC|Muchnick]]
> **Prerequisites:** [[control-flow-graph]] · IR-level cousin: [[simplifycfg]] (branch → `select`) · vault tracks [[llvm-version]]

> [!abstract] Chapter map
> If-conversion **removes a branch** by turning **control dependence into data dependence**: the two arms of a small `if` become **predicated** instructions (executed under a condition) or a `select`, so there is no branch to mispredict and the straight-line code can be scheduled for ILP. The cost is that both arms' work may execute.

---

## 1. The transform

```text
if (c) x = A; else x = B;     ⟶     x = select c, A, B          (no branch)
```
On targets with **predicated execution** (e.g. ARM), the arms' instructions are kept but guarded by the predicate `c`; on others, small diamonds become `select`. Either way the conditional branch disappears.

## 2. In LLVM — two passes

> [!info] Early vs. late
> - **`EarlyIfConversion`** — runs on **SSA machine IR**, converting simple diamonds to `select`-like predicated form early, before register allocation (works with [[instruction-scheduling]] to expose parallelism).
> - **`IfConversion`** — runs late, using the **target's predication** to guard whole blocks of instructions.
> At the IR level, [[simplifycfg]] already does the simplest branch → `select` rewrites; these codegen passes handle the machine-level, target-predicated cases.

## 3. When it pays — and when it doesn't

> [!warning] A profitability / target call
> If-conversion helps when the branch is **unpredictable** (misprediction cost > executing both arms) and the arms are **short**. It hurts when one arm is large or the branch is well-predicted. So it is **heavily target- and profile-dependent**, and which form runs by default varies by target/version — confirm via [[llvm-version]].

> [!summary] The one thing to remember
> If-conversion trades a branch for **predication/`select`** — control dependence becomes data dependence, removing misprediction and exposing ILP, at the cost of running both arms. LLVM: `EarlyIfConversion` (SSA MIR, `select`) and `IfConversion` (late, target predication); [[simplifycfg]] does the IR-level version.

> [!quote] Further reading
> - **Source:** [`CodeGen/IfConversion.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/CodeGen/IfConversion.cpp) · [`CodeGen/EarlyIfConversion.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/CodeGen/EarlyIfConversion.cpp)
> - **Muchnick §18** — control-flow and low-level optimizations.
