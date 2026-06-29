---
title: implementation/ — about this layer
type: meta
tags: [meta, facet-about]
---

# implementation/ — system-specific realizations

How a specific system realizes a technique: a particular LLVM pass, an MLIR dialect/pattern, a Swift SIL pass, a Rust MIR optimization. Every note here carries `ecosystem:` and a `src:` path. (Migrated notes that teach a concept *and* its LLVM realization currently live in `concept/`; promote a realization here once it grows or is reused.) See [[classification-protocol]].

**Promotion trigger (agreed):** create an `implementation/` note when one pass realizes **≥2 concepts** (the reuse case) or **deviates sharply from the textbook**; otherwise leave the LLVM detail in the concept note. Template: [[implementation-note]].

**Notes here:**
- [[llvm-gvn]] — the GVN pass; realizes [[value-numbering]] + [[partial-redundancy-elimination]]. *(first promoted note; `status: draft` pending review)*
