---
title: concept/ — about this layer
type: meta
tags: [meta, facet-about]
---

# concept/ — techniques (the teaching units)

The **techniques** that tie theory, algorithm, data structure, and implementation into one teaching unit — the chapter-sized "how a class of optimization/analysis works" note. A note belongs here when its subject is a *technique a compiler applies* (value numbering, dead-code elimination, inlining, register allocation) rather than a bare definition (`theory/`), a procedure (`algorithm/`), a representation (`data-structure/`), or one concrete pass in a real system (`implementation/`). See [[classification-protocol]].

This is the vault's largest facet by design — most compiler knowledge is technique. Navigation is by **concept MOC** (`_moc/concept/`), not by sub-folders: the folder stays flat (one axis = facet) and chapters are assembled with links + Dataview. When a `concepts:` key accumulates several notes, give it a concept MOC so the cluster stays discoverable (the `vault-lint` job flags clusters that lack one).
