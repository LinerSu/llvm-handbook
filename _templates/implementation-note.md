---
title: <System> <Pass/Component>          # e.g. "LLVM GVN"
facet: implementation     # this folder
stage: optimization       # frontend | ir | analysis | optimization | codegen | runtime | meta
ecosystem: [llvm]         # the ONE system this note documents (llvm | mlir | clang | rust | swift | …)
concepts: []              # chapter keys this realization belongs to
implements:               # the realization pointer(s): which concept + the real path
  - { ecosystem: llvm, src: "llvm/lib/Transforms/…" }
data_structures: []       # → data-structure/ notes this pass consumes
src: ""                   # real path this note documents (the implementing file/dir)
docs: ""                  # primary doc link (prefer tier-1, see _meta/source-hierarchy)
prereqs: []
related: []               # the concept/ notes this pass REALIZES go here
tags: [kind/pass, status/stub]   # add version-sensitive if any claim depends on the release
status: stub              # stub | draft | unverified | verified | disputed | needs-review
verified_on: ""
sources: []
---

# <System> <Pass/Component>

> 🧭 **Implementation** · `implementation · <stage> · <ecosystem>` · Index [[LLVM.MOC]]
> **Realizes:** [[ ]] (the concept) · **Prerequisites:** [[ ]] · **Consumes:** [[ ]]

> [!abstract] What this note adds
> One or two sentences: the *engineering* specifics of this concrete pass that don't belong in the concept note — exact file/class, pipeline slot, flags, and where LLVM deviates from the textbook.

---

## 1. The pass
What it is in one line: the pass name, the implementing file, the entry class/function. Link the concept it realizes → [[ ]].

## 2. What it realizes (and why promoted)
Which concept note(s) this pass implements. If it realizes **more than one** concept, say so — that reuse is the reason this note exists separately.

## 3. Where it runs
Position in the pass pipeline; the opt levels that schedule it; what runs before/after that matters.

## 4. How it's built
Key classes and the [[ |data structures]] it consumes; the analyses it depends on.

## 5. Textbook → LLVM (deviations)
> [!info]+ Where the real pass differs from the classic algorithm
> | Classic algorithm | What LLVM actually does |
> |---|---|
> | … | … |

## 6. Run it yourself
> [!example]+ Reproduce the transform
> ```bash
> opt -passes='…' -S input.ll
> ```

## 7. Flags & knobs
The `cl::opt` switches that toggle/tune it (defaults noted).

## 8. Siblings & variants
Related passes (rewrites, hoist/sink variants), and which are default vs opt-in.

## 9. Limitations & version notes
Guards, what it won't do, and anything `version-sensitive` → link [[llvm-version]].

> [!summary] The one thing to remember
> …

> [!quote] Sources & confidence
> - **Source:** [`Transforms/…`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/…) — tier-1 evidence.
> - Primary docs / doxygen; mark unverified claims with `> [!danger] Unverified`.
