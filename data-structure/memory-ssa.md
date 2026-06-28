---
title: Memory SSA
facet: data-structure
stage: analysis
ecosystem: [llvm]
concepts: [ssa, memory-analysis]
src: llvm/lib/Analysis/MemorySSA.cpp
docs: "MemorySSA ↗ https://llvm.org/docs/MemorySSA.html"
prereqs: [ssa-form]
related: [pointer-alias-analysis, loop-transformations]
tags: [kind/data-structure, status/verified]
status: verified
verified_on: 2026-06-28
---

# Memory SSA

> 🧭 **Data structure** · `data-structure · analysis · llvm` · Index [[LLVM.MOC]]
> **Prerequisites:** [[ssa-form]] · **Pairs with:** [[pointer-alias-analysis]] · **Powers:** [[loop-transformations]]

> [!abstract] Chapter map
> Lift SSA's def-use/use-def convenience to *memory* via `MemoryDef` / `MemoryUse` / `MemoryPhi`, so a pass can ask "what could have clobbered this memory?" without re-running a full data-flow analysis.

> [!info]+ From classic compiler theory → LLVM
> | Classic concept | LLVM realization |
> |---|---|
> | SSA is for *scalars*; memory is opaque | **Memory SSA** gives memory the same def-use/use-def chains |
> | May-def / may-use of a memory location | `MemoryDef` / `MemoryUse`, disambiguated against [[pointer-alias-analysis|alias analysis]] |

---

### 1. Definition

> [!note] Definition
> **Memory SSA** is an analysis that lets us cheaply reason about interactions between memory operations — it provides an **SSA-style form for memory**, with def-use/use-def chains, so you can quickly find the may-defs and may-uses for a memory op. ([MemorySSA doc](https://llvm.org/docs/MemorySSA.html))

> [!info] ==Clobber==
> An access **clobbers** another when it overwrites part of the memory that the other reads from or writes to. Memory SSA's job is to track, for each access, the most recent thing that could clobber it.

> [!note] Three kinds of memory access
> | Node | Meaning | Examples |
> |---|---|---|
> | **MemoryDef** | may *modify* memory or impose ordering | `store`, calls, `acquire`+ `load`s, `volatile`, fences |
> | **MemoryUse** | reads but does *not* modify memory | `load`, `readonly` call |
> | **MemoryPhi** | φ for memory at CFG merges | merges may-reaching memory versions |
>
> Each `MemoryDef`/`MemoryUse` links to the access it depends on. Initially every `MemoryDef` conservatively clobbers every other; the analysis then disambiguates.

### 2. Worked example

> [!example]- Memory chains in IR (click to expand)
> ```llvm
> define void @foo() {
> entry:
>   %p1 = alloca i8
>   %p2 = alloca i8
>   %p3 = alloca i8
>   ; 1 = MemoryDef(liveOnEntry)
>   store i8 0, ptr %p3
>   br label %while.cond
> while.cond:
>   ; 6 = MemoryPhi({entry,1},{if.end,4})
>   br i1 undef, label %if.then, label %if.else
> if.then:
>   ; 2 = MemoryDef(6)
>   store i8 0, ptr %p1
>   br label %if.end
> if.else:
>   ; 3 = MemoryDef(6)
>   store i8 1, ptr %p2
>   br label %if.end
> if.end:
>   ; 5 = MemoryPhi({if.then,2},{if.else,3})
>   ; MemoryUse(5)
>   %1 = load i8, ptr %p1
>   ; 4 = MemoryDef(5)
>   store i8 2, ptr %p2
>   ; MemoryUse(1)
>   %2 = load i8, ptr %p3
>   br label %while.cond
> }
> ```

> [!info]- Reading the annotations (click to expand)
> - `6 = MemoryPhi({entry,1},{if.end,4})` — entering `while.cond`, the reaching memory def is either **1** or **4**; this MemoryPhi is named **6**.
> - `2 = MemoryDef(6)` / `3 = MemoryDef(6)` — the two stores in `if.then`/`if.else`; each is reached by **6**.
> - `5 = MemoryPhi({if.then,2},{if.else,3})` — the clobber before `if.end` is either **2** or **3**.
> - `MemoryUse(5)` — `load %p1` is clobbered by **5**.
> - `4 = MemoryDef(5)` — `store %p2` is a def reached by **5**.
> - `MemoryUse(1)` — `load %p3` only depends on memory version **1** (the `store %p3` above the loop); newer versions don't affect it — exactly the kind of fact that lets [[loop-transformations#7. Loop-invariant code motion (LICM)|LICM]] hoist a load.

> [!tip] Where this gets used
> Memory SSA powers memory-aware passes: LICM (is this load invariant?), GVN/DSE, and [[loop-transformations#9. Fission (distribution)|loop distribution]] — anywhere you must ask *"what could have clobbered this memory?"* without re-running a full data-flow analysis each time.

> [!quote] Sources
> - [MemorySSA](https://llvm.org/docs/MemorySSA.html)
