---
title: Dragon Book Ch.8 — Code Generation → LLVM
type: book-moc
book: "Aho, Lam, Sethi, Ullman — Compilers: Principles, Techniques & Tools (Dragon Book, 2e)"
chapter: 8
tags: [moc, kind/moc, book]
status: draft
verified_on: 2026-06-28
---

# Dragon Book Ch.8 — Code Generation → LLVM

> 🧭 **Book bridge** · Chapter of [[Home]] · ecosystem map [[LLVM.MOC]]
> **Source:** Dragon Book (2e) Chapter 8, pp. 505–579.

> [!abstract] What this bridge delivers
> A **reading map**: if you're reading Dragon Book Chapter 8, this points each section to the vault note that covers the same idea **in LLVM's back end**. The vault notes describe LLVM directly (with examples + diagrams); the book is the optional companion for the language-agnostic theory.

## 🗂 Section-by-section crosswalk

| § | Book topic | LLVM realization | Vault note |
|---|---|---|---|
| 8.1 | Issues in code-generator design | the target-independent codegen + a target description | [[code-generation-overview]] |
| 8.2 | The target language | the **MC** layer (`MCInst`) + `lib/Target/<Arch>` | [[code-generation-overview]] |
| 8.3 | Addresses in the target code | stack slots (`alloca`/frame), addressing via GEP | [[getelementptr]], [[code-generation-overview]] |
| 8.4 | Basic blocks & flow graphs | `MachineBasicBlock`s; the CFG | [[control-flow-graph]] |
| 8.5 | Optimization of basic blocks (local DAG) | local value-number/DAG reuse; peephole | [[value-numbering]], [[instruction-combining]] |
| 8.6 | A simple code generator | the codegen pipeline (ISel → sched → regalloc → emit) | [[code-generation-overview]] |
| 8.7 | Peephole optimization | `instcombine` (IR) and machine peephole / late passes | [[instruction-combining]] |
| 8.8 | **Register allocation & assignment** | Greedy / Basic / Fast / PBQP over `LiveIntervals` | [[register-allocation]] |
| 8.9 | **Instruction selection by tree rewriting** | SelectionDAG / GlobalISel pattern tiling | [[instruction-selection]] |
| 8.10–8.11 | Optimal / DP code generation for expressions | TableGen pattern costs in the selectors | [[instruction-selection]] |

## 📚 Suggested reading path (book ↔ vault)

1. **§8.1–8.6 → [[code-generation-overview]]** — the shape of a back end (and where [[control-flow-graph|MIR blocks]] fit).
2. **§8.9 → [[instruction-selection]]** — tiling the IR with target instructions (SelectionDAG vs GlobalISel).
3. **§8.8 → [[register-allocation]]** — packing virtual registers into physical ones (and why LLVM splits rather than colors).
4. **§8.5, 8.7 → [[value-numbering]], [[instruction-combining]]** — the local/peephole cleanups.

## 📝 Reading notes — what's different in modern LLVM

> [!info] Three things to keep in mind while reading the book
> - **Register allocation is not graph coloring.** §8.8 teaches Chaitin-style coloring; LLVM's default **Greedy** allocator splits and evicts **live intervals** by spill-weight instead (see [[register-allocation]]).
> - **Two selectors, pattern-driven.** §8.9–8.11's tree-rewriting/DP becomes **TableGen-generated patterns** matched by **SelectionDAG** (per block) or **GlobalISel** (whole function) — see [[instruction-selection]].
> - **MIR carries SSA, then drops it.** Machine IR is in SSA through early codegen; `PHIElimination` turns φ into copies *before* register allocation.

```dataview
TABLE facet, stage, status
WHERE book AND contains(book, "§8")
SORT file.name ASC
```
