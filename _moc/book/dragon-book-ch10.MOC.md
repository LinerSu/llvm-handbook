---
title: Dragon Book Ch.10 — Instruction-Level Parallelism → LLVM
type: book-moc
book: "Aho, Lam, Sethi, Ullman — Compilers: Principles, Techniques & Tools (Dragon Book, 2e)"
chapter: 10
tags: [moc, kind/moc, book]
status: draft
verified_on: 2026-06-28
---

# Dragon Book Ch.10 — Instruction-Level Parallelism → LLVM

> 🧭 **Book bridge** · Chapter of [[Home]] · ecosystem map [[LLVM.MOC]]
> **Source:** Dragon Book (2e) Chapter 10, pp. 707–766.

> [!abstract] What this bridge delivers
> A **reading map** into LLVM's instruction scheduler. Chapter 10's local, global, and software-pipelining scheduling all land in one LLVM-side note (plus its register-allocation neighbor).

## 🗂 Section-by-section crosswalk

| § | Book topic | LLVM realization | Vault note |
|---|---|---|---|
| 10.1 | Processor architectures (pipelines, superscalar, VLIW) | the machine model the scheduler targets | [[instruction-scheduling]] |
| 10.2 | Code-scheduling constraints (data/control/resource deps) | the dependence DAG | [[instruction-scheduling]] |
| 10.3 | Basic-block scheduling | local **list scheduling** | [[instruction-scheduling]] |
| 10.4 | Global code scheduling | **MachineScheduler** over regions | [[instruction-scheduling]] |
| 10.5 | Software pipelining | **MachinePipeliner** (Swing Modulo Scheduling) | [[instruction-scheduling]] |

## 📚 Suggested reading path (book ↔ vault)

1. **§10.2–10.3 → [[instruction-scheduling]]** — dependences and basic-block list scheduling.
2. **§10.4 → [[instruction-scheduling]]** — global scheduling (MachineScheduler) and the register-pressure trade with [[register-allocation]].
3. **§10.5 → [[instruction-scheduling]]** — software pipelining (modulo scheduling).

## 📝 Reading notes — what's different in modern LLVM

> [!info] Two things to keep in mind while reading the book
> - **One scheduler, register-pressure-aware.** LLVM folds local + global scheduling into the **MachineScheduler**, whose distinctive concern is balancing ILP against **register pressure** (to avoid spills) — a tension the textbook treats more separately ([[instruction-scheduling]], [[register-allocation]]).
> - **Software pipelining is opt-in / target-gated.** §10.5's pipelining is `MachinePipeliner` (Swing Modulo Scheduling), enabled on targets that benefit (e.g. Hexagon, PowerPC), not everywhere.

```dataview
TABLE facet, stage, status
WHERE book AND contains(book, "§10")
SORT file.name ASC
```
