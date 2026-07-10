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
| concept/register-allocation.md | register-allocation-coloring-spill.gif | pass (5 applied: ext-asm worked example, predict-first, MIR gloss, spill-weight gloss, two-address example) | yes | 2026-07-09 | — |
| concept/instruction-scheduling.md | instruction-scheduling-list-schedule.gif | pass (5 applied: loop-body schedule table, predict-first, pre/post-RA expansion, SDAG-fallback reword, latency gloss) | yes | 2026-07-09 | — |
| concept/partial-redundancy-elimination.md | partial-redundancy-elimination-insert-then-delete.gif | pass (student: 3 tightens, pre-load.ll walkthrough) | yes | 2026-07-10 | PR #4 |
| concept/sparse-conditional-constant-propagation.md | sccp-edge-kill.gif | pass (student: 2 tightens, sparse/φ rule, try-it) | yes | 2026-07-10 | PR #4 |
| concept/value-numbering.md | value-numbering-lvn-table.gif | pass (student: §§1–4 merged, dom-tree figure, try-it) | yes | 2026-07-10 | PR #4 |
| concept/simplifycfg.md | simplifycfg-diamond-to-select.gif | pass (student: before/after Mermaid, try-it, Limits) | yes | 2026-07-10 | PR #5 |
| data-structure/loop-info.md | loop-info-lcssa-closing.gif | pass (student: headings, LCSSA bug fix, rotation) | yes | 2026-07-10 | PR #5 |
| implementation/llvm-gvn.md | — (pass note; concept GIFs cover it) | pass (student: −130 words, arrow pipeline, ext-gvn) | yes | 2026-07-10 | PR #5 |
| data-structure/memory-ssa.md | memory-ssa-clobber-walk.gif | pass (student: version-graph Mermaid, API scoping, reproduce line) | yes | 2026-07-10 | PR #6 |
| data-structure/scalar-evolution.md | — (Mermaid/examples suffice) | pass (student: reproduce pipe, {a,+,4} fold, 🎥 SCEV talk) | yes | 2026-07-10 | PR #6 |
| concept/instruction-selection.md | instruction-selection-tiling.gif | pass (student: verified x86/RISC one-liner, 🎥 SDAG tutorial) | yes | 2026-07-10 | PR #6 |
| concept/pointer-alias-analysis.md | pointer-alias-analysis-dsa-local.gif | pass (student: BU/TD Mermaid, aa-eval try-it, −60 words) | yes | 2026-07-10 | PR #7 |
| concept/instruction-combining.md | instruction-combining-worklist.gif | pass (student: goal-claim fix, worklist GIF replaces PNG, try-it) | yes | 2026-07-10 | PR #7 |
| concept/loop-transformations.md | loop-transformations-licm-hoist.gif | pass (student: summary table, golden-rule dedup, -Rpass try-it) | yes | 2026-07-10 | PR #7 |
| data-structure/control-flow-graph.md | — (Mermaid + dot-cfg tip suffice) | pass (student: dedup, dot-cfg try-it) | yes | 2026-07-10 | PR #8 |
| concept/getelementptr.md | getelementptr-index-walk.gif | pass (student: repetition purge, -O0/-O1 reproduce, nuw fix) | yes | 2026-07-10 | PR #8 |
| concept/inlining.md | inlining-clone-and-fold.gif | pass (student: knob table, cost-model remark example) | yes | 2026-07-10 | PR #8 |
| concept/llvm-basics.md | — (7 captioned figures; 3 dupes deleted) | pass (student: figure-dump cleanup, Get-it column, 🎥 IR tutorial) | yes | 2026-07-10 | PR #9 |
| implementation/clang-frontend-pipeline.md | clang-frontend-pipeline-acton-loop.gif | pass (student: 5×→2× thesis, ast-dump try-it) | yes | 2026-07-10 | PR #9 |
| data-structure/clang-ast.md | clang-ast-construction.gif | pass (student: Type node shown in Mermaid, 🎥 Klimek tutorial) | yes | 2026-07-10 | PR #9 |
| data-structure/call-graph.md | — (SCC Mermaid + see-it tip suffice) | pass (student: SCC-in-diagram, print-callgraph-sccs tip) | yes | 2026-07-10 | PR #10 |
| concept/dead-code-elimination.md | dead-code-elimination-adce-liveness.gif | pass (student: BDCE example bug fix, dce-vs-adce try-it) | yes | 2026-07-10 | PR #10 |
| concept/early-cse.md | early-cse-scoped-hash.gif | pass (student: memssa reproduce line, broom cut) | yes | 2026-07-10 | PR #10 |
| concept/scalar-replacement-of-aggregates.md | — (split→promote Mermaid suffices) | pass (student: phantom-name fix, optnone reproduce gotcha) | yes | 2026-07-10 | PR #11 |
| concept/induction-variables-and-strength-reduction.md | induction-variables-and-strength-reduction-pointer-iv.gif | pass (student: LSR-pipeline fix, handoff Mermaid, loop-reduce see-it) | yes | 2026-07-10 | PR #11 |
| concept/jump-threading.md | jump-threading-edge-clone.gif | pass (student: paste-and-run phi .ll, dedup) | yes | 2026-07-10 | PR #11 |

**Batch order** (clustered by shared example/prereqs): ① ssa-form · mem2reg · dominator-tree → ② data-flow-analysis · dataflow-foundations → ③ register-allocation · instruction-scheduling → ④ onward from the queue above.
