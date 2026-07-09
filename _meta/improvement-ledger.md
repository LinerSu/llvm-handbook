---
title: Improvement Ledger (GIF + pedagogy loops)
type: meta
tags: [meta, rulebook]
---

# Improvement ledger — animation + pedagogy/expert loops

Cross-session queue and record for the note-improvement loops (see `.claude/workflows/note-animate.js` and `.claude/workflows/note-improve.js`, and `_meta/anim/storyboard-spec.md`). **Each run processes ≤ 3 notes.** A session that runs a batch updates this table and commits it — the queue travels via git, not chat history.

- `gif` — the animation embedded in the note (`—` = judged not animation-worthy; blank = not attempted).
- `pedagogy` — outcome of the `note-improve` pass (`pass (N applied)` = N approved proposals applied).
- `expert-verified` — the improve pass's proposals were web-verified against LLVM @ the pinned tag (`_meta/llvm-version.md`).

| note | gif | pedagogy | expert-verified | date | commit |
|---|---|---|---|---|---|
| data-structure/ssa-form.md | ssa-form-phi-placement.gif (pilot, hand-authored) | queued | queued | 2026-07-09 | — |
| concept/mem2reg.md | queued | queued | queued | — | — |
| data-structure/dominator-tree.md | queued | queued | queued | — | — |
| concept/data-flow-analysis.md | queued | queued | queued | — | — |
| theory/dataflow-foundations.md | queued | queued | queued | — | — |
| concept/register-allocation.md | queued | queued | queued | — | — |
| concept/instruction-scheduling.md | queued | queued | queued | — | — |
| concept/partial-redundancy-elimination.md | queued | queued | queued | — | — |
| concept/sparse-conditional-constant-propagation.md | queued | queued | queued | — | — |
| concept/value-numbering.md | queued | queued | queued | — | — |
| concept/simplifycfg.md | queued | queued | queued | — | — |
| data-structure/loop-info.md | queued | queued | queued | — | — |

**Batch order** (clustered by shared example/prereqs): ① ssa-form · mem2reg · dominator-tree → ② data-flow-analysis · dataflow-foundations → ③ register-allocation · instruction-scheduling → ④ onward from the queue above.
