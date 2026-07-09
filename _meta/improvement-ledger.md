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
| data-structure/ssa-form.md | ssa-form-phi-placement.gif (pilot, hand-authored) | pass (5 applied: why-care, use-def scoping, predict-first, DF intuition, phi-edge dominance) | yes | 2026-07-09 | — |
| concept/mem2reg.md | mem2reg-promotion.gif | pass (3 applied: glosses, predict-first, §3 trace) | yes | 2026-07-09 | — |
| data-structure/dominator-tree.md | dominator-tree-idom-build.gif | pass (5 applied: predict-first, DF check-on-figure, iterated gloss, running-example DF trace, EarlyCSE contrast) | yes | 2026-07-09 | — |
| concept/data-flow-analysis.md | data-flow-analysis-worklist.gif | pass (6 applied: SCCP trace, predict-first, init clarification, sparse gloss, MFP-loss example, NAC expansion) | yes | 2026-07-09 | — |
| theory/dataflow-foundations.md | dataflow-foundations-lattice-climb.gif | pass (5 applied: meet example, height definition, backward form, collecting-semantics gloss, non-distributivity example) | yes | 2026-07-09 | — |
| concept/register-allocation.md | queued | queued | queued | — | — |
| concept/instruction-scheduling.md | queued | queued | queued | — | — |
| concept/partial-redundancy-elimination.md | queued | queued | queued | — | — |
| concept/sparse-conditional-constant-propagation.md | queued | queued | queued | — | — |
| concept/value-numbering.md | queued | queued | queued | — | — |
| concept/simplifycfg.md | queued | queued | queued | — | — |
| data-structure/loop-info.md | queued | queued | queued | — | — |

**Batch order** (clustered by shared example/prereqs): ① ssa-form · mem2reg · dominator-tree → ② data-flow-analysis · dataflow-foundations → ③ register-allocation · instruction-scheduling → ④ onward from the queue above.
