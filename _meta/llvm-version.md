---
title: LLVM Version (vault anchor)
type: meta
tags: [meta, rulebook]
llvm_stable: "22.1.8"
llvm_series: "22.1.x"
llvm_dev: "23.x"
as_of: 2026-06-28
source: "https://github.com/llvm/llvm-project/releases"
---

# LLVM Version — vault anchor

**This vault describes LLVM `22.1.x`** (latest stable **22.1.8**, released 2026-06-16). The next major series, **23.x**, is in development. *(Auto-checked monthly — see §Auto-update.)*

> [!info] Why a single anchor
> Most notes describe **version-stable** concepts (SSA, GEP, dominators, the dataflow framework) that don't change across releases. Only a few specifics are version-sensitive (defaults, framework maturity, the release number). Those notes are tagged **`version-sensitive`** and point here, so the version lives in **one place** instead of being hardcoded across the vault.

## Policy

- The exact release number (e.g. `22.1.8`) lives **only in this note's frontmatter** — don't hardcode patch numbers in content notes.
- A note whose accuracy depends on the LLVM version carries the tag **`version-sensitive`** and links back to `[[llvm-version]]`.
- On a version bump, re-verify the claims listed below and update each note's `verified_on`.

## Version-sensitive claims to re-check on a bump

| Claim | Note | Current (22.1.x) |
|---|---|---|
| Default register allocator | [[register-allocation]] | **Greedy** at `-O1+`, Fast at `-O0` |
| Default instruction selector | [[instruction-selection]], [[code-generation-overview]] | **SelectionDAG** on most targets; **GlobalISel** default/most-mature on **AArch64** |
| PRE availability | [[partial-redundancy-elimination]] | **load PRE in GVN** on by default; full **GVN-PRE off** by default |
| Pointer/alias passes in-tree | [[pointer-alias-analysis]] | `basic-aa`, `tbaa`, `globals-aa`, `scev-aa`, `cfl-anders-aa`, `cfl-steens-aa`; DSA in external `poolalloc` |
| Latest stable release | (this note) | **22.1.8** |

## Notes currently tagged `version-sensitive`

```dataview
TABLE status, verified_on FROM #version-sensitive SORT file.name ASC
```

## Auto-update

A scheduled task (`llvm-version-check`, monthly) web-checks the latest LLVM stable release; if it differs from `llvm_stable` above, it updates this note's frontmatter + `as_of` and lists the `version-sensitive` notes to re-verify. The task only edits this anchor — content notes are updated by hand after review.

> [!quote] Source
> [llvm/llvm-project releases](https://github.com/llvm/llvm-project/releases) · [releases.llvm.org](https://releases.llvm.org/)
