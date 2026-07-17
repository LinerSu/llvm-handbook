---
title: LLVM Version (vault anchor)
type: meta
tags: [meta, rulebook]
llvm_stable: "22.1.8"
llvm_series: "22.1.x"
llvm_dev: "23.x"
llvm_git_tag: "llvmorg-22.1.8"
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

> [!warning] Re-check these against **source at `llvm_git_tag`**, never against docs or search
> Every row below is a claim about a *default*, and defaults are exactly what tier-3 prose and tier-4 blogs get wrong (see [[source-hierarchy]]). Three of these rows were themselves wrong until 2026-07-16 — this table shipped for three weeks asserting the existence of alias analyses LLVM had deleted. **The standing check for any "pass X uses/enables Y" claim is the `cl::opt` default**: find the `cl::init(...)` and read it. That single check refuted two claims in the 2026-07-16 audit.

| Claim | Note | Current (22.1.x) | Source of truth |
|---|---|---|---|
| Default register allocator | [[register-allocation]] | **Greedy** at `-O1+`, **Fast** at `-O0` | `TargetPassConfig.cpp` (`createTargetRegisterAllocator`) |
| Default instruction selector | [[instruction-selection]], [[code-generation-overview]] | **SelectionDAG** by default everywhere, *except*: **SPIRV** always uses GlobalISel (`setGlobalISel(true); setFastISel(false)`), and **AArch64 at `-O0`** uses GlobalISel (`aarch64-enable-global-isel-at-O` is `cl::init(0)`, and `CodeGenOptLevel::None == 0`). **FastISel runs at `-O0` only on targets that don't opt into GlobalISel** — GlobalISel is tested *first*. | `TargetPassConfig.cpp:1004-1016`; `AArch64TargetMachine.cpp:158-161,385-391`; `SPIRVTargetMachine.cpp:91-93` |
| PRE availability | [[partial-redundancy-elimination]] | In GVN, **both** `enable-pre` (scalar) and `enable-load-pre` are **`cl::init(true)`** — on by default. Off by default: `enable-load-pre-split-backedge`, `enable-gvn-memoryssa`. There is **no `gvn-pre` pass**; complete VanDrunen/Hosking-style PRE is not implemented upstream at all (which is different from "off by default"). | `GVN.cpp:108-117` |
| Pointer/alias passes in-tree | [[pointer-alias-analysis]] | Exactly six registered: `globals-aa` (module), `basic-aa`, `objc-arc-aa`, `scev-aa`, `scoped-noalias-aa`, `tbaa` (function). **CFL-AA is gone** — `cfl-anders-aa`/`cfl-steens-aa` have no registration and their sources 404 at this tag. DSA remains out-of-tree in `poolalloc`. | `llvm/lib/Passes/PassRegistry.def:47,392-396` |
| GlobalISel maturity | [[instruction-selection]] | **Not a checkable claim — do not assert it.** "Most mature on AArch64" has no source metric. The checkable fact is which targets call `setGlobalISel(true)`: SPIRV (always) and AArch64 (`-O0` only). Notably **not** AMDGPU, which still needs explicit `-global-isel`. | `grep -rn "setGlobalISel(true)" llvm/lib/Target/` |
| Latest stable release | (this note) | **22.1.8** | [releases](https://github.com/llvm/llvm-project/releases) |

> [!note] Table last source-verified
> **2026-07-16**, against `llvmorg-22.1.8`, by reading the files in the *Source of truth* column directly. Prior to that date this table had never been checked against source — it was authored alongside the vault and inherited its claims from the notes it was meant to govern.

## Notes currently tagged `version-sensitive`

```dataview
TABLE status, verified_on FROM #version-sensitive SORT file.name ASC
```

## Source checkout (submodule) — for confirmation

Tier-1 verification ([[source-hierarchy]]) is the LLVM source itself. The vault pins it as a git submodule at **`.llvm-project`** (dot-prefixed so Obsidian doesn't index it), checked out at the tag in `llvm_git_tag` above. The submodule **pointer** is committed (tiny); the multi-hundred-MB working tree is **opt-in** — only present after you populate it, and excluded from Obsidian.

- **Populate (on demand, for grep):**
  `git submodule update --init --depth 1 .llvm-project`
  (configured shallow + sparse — limited to `llvm/lib`, `llvm/include`, `mlir/lib`, `mlir/include`, `clang/lib`).
- **Free the disk again:** `git submodule deinit .llvm-project`.
- **Bump to a new LLVM release** (keeps the vault in lock-step):
  1. `cd .llvm-project && git fetch --depth 1 origin tag <new-tag> && git checkout <new-tag> && cd ..`
  2. update `llvm_stable` / `llvm_git_tag` / `as_of` above and re-verify the table below.
  3. commit the moved submodule pointer + this note together.

> [!warning] iCloud
> This vault lives in iCloud. Populating the submodule lands its files in the synced folder; prefer populating on a **non-iCloud clone**, or `deinit` when done. The committed pointer alone syncs no source.

## Auto-update

A scheduled task (`llvm-version-check`, monthly) web-checks the latest LLVM stable release; if it differs from `llvm_stable` above, it updates this note's frontmatter + `as_of` and lists the `version-sensitive` notes to re-verify. The task only edits this anchor — content notes are updated by hand after review.

> [!quote] Source
> [llvm/llvm-project releases](https://github.com/llvm/llvm-project/releases) · [releases.llvm.org](https://releases.llvm.org/)
