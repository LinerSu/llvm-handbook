---
title: Classification Protocol
type: meta
tags: [meta, rulebook]
---

# Classification Protocol

The rulebook the intake assistant (and you) follow to file **any** new topic — including topics in ecosystems not yet seen — without re-deciding the taxonomy each time. Folders encode exactly one axis (**facet**); everything else is frontmatter + links.

## Step 0 — Atomicity
One file = one topic. If a draft bundles several topics, split it. If you can't state the subject in one sentence ("This note is mainly about ⟨X⟩"), it is two notes.

## Step 1 — Read the vault first
Before assigning anything, skim existing notes' frontmatter, the MOCs, and [[controlled-vocabulary]]. **Imitate conventions already present** rather than inventing new ones — the vault is its own set of examples. This is what makes filing converge to the house style automatically.

## Step 2 — Assign the finite axes (decision trees)

**facet** (the folder home):
- a reusable definition / theorem / proof → `theory`
- a procedure / recipe → `algorithm`
- a representation / structure → `data-structure`
- a concrete pass / component in a real system → `implementation`
- a real-world use, limitation, or frontier → `application`
- a technique that ties several of the above together (the teaching unit) → `concept`

**stage** (pipeline phase): `frontend · ir · analysis · optimization · codegen · runtime · meta`. Ask "where would a compiler engineer put this?"

## Step 3 — Assign ecosystem (open vocab)
Pick from [[controlled-vocabulary]]; reuse before minting (check synonyms: `torch`→`pytorch`). Cross-cutting → `general`. A genuinely new ecosystem may be added, **but** that triggers the review gate (Step 6).

## Step 4 — Wire facets & neighbors
Fill the typed facet links (`theory`, `algorithm`, `data_structures`, `applications`, `implements`). Create `status: stub` foundation notes for any referenced-but-missing theory/algorithm/data-structure. Set `prereqs` and `related`; add the note to its concept / ecosystem / stage MOC(s).

## Step 5 — Provenance
Add `src:` (real path it documents, for tool notes), `docs:`/`sources:` (prefer primary — see [[source-hierarchy]]), and set `status`/`verified_on`. Wrap any unconfirmed claim in `> [!danger] Unverified` until checked.

## Step 6 — Confidence gate (keeps autonomy safe)
If axis assignment is low-confidence, **or** the topic would mint a new top-level concept or a new ecosystem, set `status: needs-review` and surface it — do **not** guess silently. Everything routine proceeds automatically.

## Worked routing examples
- "loop peeling" → `concept` / `optimization` / `general+llvm`; implements → LLVM `LoopPeel`, MLIR affine.
- "Clang Sema overview" → `implementation` / `frontend` / `clang`; src → `clang/lib/Sema/`.
- "octagon domain" → `theory` (domain) or `data-structure` (DBM rep); `analysis` stage; `general` ecosystem.
- "MLIR `affine` tiling" → `implementation` / `optimization` / `mlir`.
