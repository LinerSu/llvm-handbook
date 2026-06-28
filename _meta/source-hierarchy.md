---
title: Source Hierarchy
type: meta
tags: [meta, rulebook]
---

# Source Hierarchy

Trust order for citations. A note's `sources:`/`docs:` should prefer the highest available tier; the verify pass downgrades `status` on any claim that conflicts with a higher-tier source.

1. **Primary — the artifact itself.** LLVM/MLIR source (`src:` path), LangRef, MLIR LangRef, official doxygen. The ground truth. For a specific **pass/transformation**, link the implementing source directly (`https://github.com/llvm/llvm-project/blob/main/llvm/lib/…`) in the note's footer — it is tier-1 evidence, not just a citation.
2. **Canonical papers.** e.g. Kildall 1973 (dataflow), Cousot & Cousot 1977 (abstract interpretation), Cytron et al. 1991 (SSA), Wegman & Zadeck 1991 (SCCP), Lattner & Adve (DSA).
3. **Official tutorials / docs prose.** Useful but can lag the code — *verify API names against tier 1*.
4. **Blogs / StackOverflow / talks.** Orientation only; never the sole citation for a claim.

## Known-stale watch
- The MLIR *"Writing DataFlow Analyses"* tutorial documents the old `ForwardDataFlowAnalysis`/`LatticeElement` API; the current framework is the generic **`DataFlowSolver`** (`mlir/include/mlir/Analysis/DataFlow/`). Treat tutorial API names as suspect until checked against current doxygen.
