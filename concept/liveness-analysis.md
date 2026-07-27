---
title: Liveness Analysis
facet: concept
stage: analysis
ecosystem: [general, llvm]
concepts: [dataflow-analysis]
implements:
  - { ecosystem: llvm, src: "llvm/lib/CodeGen/LiveVariables.cpp" }
  - { ecosystem: llvm, src: "llvm/lib/CodeGen/LiveIntervals.cpp" }
src: "llvm/lib/CodeGen/LiveVariables.cpp"
book: "Dragon Book (Aho/Lam/Sethi/Ullman, 2e) §9.2 — live-variable analysis"
docs: "LLVM — The LLVM Target-Independent Code Generator ↗ https://llvm.org/docs/CodeGenerator.html"
prereqs: [data-flow-analysis, control-flow-graph, ssa-form]
related: [data-flow-analysis, register-allocation, graph-coloring, dead-code-elimination, ssa-form, code-generation-overview]
tags: [kind/analysis, status/verified]
status: verified
verified_on: 2026-07-20
---

# Liveness Analysis

> 🧭 **Concept** · `concept · analysis · general+llvm` · Index [[LLVM.MOC]] · see also [[dragon-book-ch9.MOC|Dragon Ch.9]]
> **Prerequisites:** [[data-flow-analysis]], [[control-flow-graph]], [[ssa-form]] · **Feeds:** [[register-allocation]]

> [!abstract] Chapter map
> The canonical **backward** dataflow analysis: a variable is **live** at a point if its current value **may be used before being overwritten** on some path to the exit. It is the textbook companion to reaching-definitions ([[data-flow-analysis]]) and the analysis [[register-allocation]] stands on — two values can share a register exactly when their live ranges don't overlap. The instructive LLVM twist: on **SSA IR**, [[ssa-form|def-use chains]] give you use information directly, so classic liveness isn't run there; it **resurfaces at the machine level**, where LLVM computes it as `LiveVariables` (per-instruction *killed*/*dead* sets) and `LiveIntervals` (the numbered live ranges the allocator consumes).

---

## 1. Definition

> [!note] Definition
> A variable `v` is **live** at program point `p` if there is a path from `p` to a use of `v` that does **not** redefine `v` first. Otherwise `v` is **dead** at `p`. The information wanted per point is the set of live variables — computed **backward** from uses toward definitions.

## 2. Theory — the dataflow equations

Liveness is a **backward, may (union)** analysis over the [[control-flow-graph|CFG]] (see [[data-flow-analysis]] for the framework):

> [!info] Live-variable equations
>
> - `LiveOut[B] = ⋃ over successors S of  LiveIn[S]`
> - `LiveIn[B]  = use[B] ∪ (LiveOut[B] − def[B])`
>
> where `use[B]` = variables used in `B` before any redefinition, `def[B]` = variables defined in `B`. Iterate to a fixpoint; **backward** because information flows from uses back to defs, **union** because a variable is live if used on *any* successor path.

The pairing to remember: **reaching definitions** is forward/may, **liveness** is backward/may — the two archetypes every dataflow course teaches.

## 3. Why it matters — register allocation

Liveness is the enabling analysis for [[register-allocation]]: build an **interference graph** whose nodes are values and whose edges connect values *live at the same time*; a legal register assignment is a coloring of that graph ([[graph-coloring]]). It also underpins **dead-code** reasoning — a definition whose result is never live is dead ([[dead-code-elimination]]) — and dead-store elimination.

## 4. Textbook → LLVM (the deviation worth knowing)

> [!info]+ Where classic liveness meets LLVM
>
> | Classic compiler | What LLVM does |
> |---|---|
> | Run liveness on the IR to get use/def info | On **SSA IR**, [[ssa-form\|def-use chains]] already give uses directly — no separate liveness pass needed there |
> | One liveness result | Two machine-level forms: **`LiveVariables`** (kills/deads per instruction) and **`LiveIntervals`** (numbered ranges) |
> | Bit-vector over all vars per block | *"a sparse implementation based on the machine code SSA form"* |

So the classic analysis lives (pun intended) in the **backend**, computed on `MachineInstr`s just before/for register allocation:

- **`LiveVariables`** — *"for each instruction … calculates the set of registers that are immediately **dead** after the instruction … and the set of registers … **killed**"* (used but never used again). This is liveness expressed as kill/def flags.
- **`LiveIntervals`** — computed **independently**, *not* derived from `LiveVariables`' flags: it requires only `SlotIndexes` + `MachineDominatorTree`, and `LiveIntervalCalc` builds each `LiveInterval` — *"represents the liveness of a register, or stack slot"* — directly from `MachineRegisterInfo`'s def/use operands over numbered slots. This is the form the [[register-allocation|allocator]] queries for overlap.

## 5. Worked example

> [!example]+ Live ranges visible in the asm (real Apple clang, arm64)
> ```c
> int f(int a, int b, int c) { int t = a + b; return t * c; }
> ```
> ```asm
> add  w8, w1, w0    ; t = b + a   — a (w0), b (w1) used here, then dead
> mul  w0, w8, w2    ; t * c       — t (w8) and c (w2) live to here; result in w0
> ```
> Read the live ranges off it: `a`,`b` are **live into** the `add` and **die** there (last use); `t` is **born** at the `add` and **live to** the `mul`; `c` is **live** across both. Because `a`'s range **ended**, the allocator was free to reuse a register for the result — that reuse is a liveness decision. (Seeing the numbered `LiveInterval`s directly needs `llc -debug-only=regalloc`.)

## 6. Limitations & notes

> [!warning] What to keep in mind
> - **May-analysis, so conservative.** "Live" means *possibly* used later; it can over-approximate, which is safe (never frees a still-needed value) but not exact.
> - **SSA changes where you need it.** On IR, uses are explicit; liveness earns its keep at the machine level, which is why the LLVM implementations are in `CodeGen`, not `Analysis`.
> - **PHIs complicate the edges.** As `LiveVariables.h` notes, *"PHI nodes complicate things a bit"* — a value used by a PHI is live out of the *predecessor* edge, not the PHI's block.

> [!summary] The one thing to remember
> Liveness is the **backward/union** dataflow analysis — `LiveIn[B] = use[B] ∪ (LiveOut[B] − def[B])` — answering "is this value still needed?" It is what [[register-allocation]] turns into an interference graph. On SSA IR, [[ssa-form|def-use chains]] replace it; LLVM computes it at the **machine level** as `LiveVariables` (kills/deads) and `LiveIntervals` (ranges).

> [!quote] Sources & confidence
> **Verified 2026-07-20** — every falsifiable claim in this note was enumerated and checked against the pinned LLVM source ([[llvm-version]], `llvmorg-22.1.8`) by the `note-correctness-review` pass; refuted claims were corrected (batch error rate 8.6%, 23/269). GitHub links track `main`; the checked revision is the pinned tag.
> - [llvm/include/llvm/CodeGen/LiveVariables.h](https://github.com/llvm/llvm-project/blob/main/llvm/include/llvm/CodeGen/LiveVariables.h) — per-instruction *dead*/*killed* sets; *"a sparse implementation based on the machine code SSA form";* *"PHI nodes complicate things."*
> - [llvm/include/llvm/CodeGen/LiveInterval.h](https://github.com/llvm/llvm-project/blob/main/llvm/include/llvm/CodeGen/LiveInterval.h) — `LiveInterval` *"represents the liveness of a register, or stack slot";* [`LiveIntervals.h`](https://github.com/llvm/llvm-project/blob/main/llvm/include/llvm/CodeGen/LiveIntervals.h).
> - Example asm produced locally with **Apple clang 17** (Apple's own versioning — *not* an upstream LLVM release number, and not the pinned tag; register names are target-specific — see [[llvm-version]]). The analysis is classic and version-stable.
> - **Dragon Book** §9.2 (live-variable analysis) — canonical text; see [[dragon-book-ch9.MOC]].
