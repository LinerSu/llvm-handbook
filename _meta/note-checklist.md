---
title: Note Checklist (definition of done)
type: meta
tags: [meta, rulebook]
---

# Note checklist — the self-inspection loop

Run this after writing or updating **any** vault note, as a matter of course — not only when asked. A note isn't "done" until these pass; fix issues before reporting.

## Always
1. **Links** — every wiki-link resolves (no dangling links); the new note is cross-linked from related notes and listed in its MOC.
2. **Callout tables** — a table placed *after a sentence* inside a `> [!callout]` has a blank `>` line before it (lists render either way). → [[callout-legend]]
3. **Mermaid** — no label starts with `-`/`+`/`*` (markdown-list trap) and none contains `<`/`>`; one `flowchart`/`graph` opener per ` ```mermaid ` block. → [[callout-legend]]
4. **Fences** — code fences balanced (even count); no stray inline triple-backticks in prose.
5. **LLVM-first** — the note describes LLVM directly; a source book appears only in the `book:` frontmatter and a `> [!quote] Further reading` footer — never `§x` citations in the body.
6. **House style** — frontmatter contract complete (`facet · stage · ecosystem · concepts · status · verified_on`); the arc + **≥1 worked example**; a diagram where shape is the point; a `[!summary]` one-line takeaway.
7. **Classification** — `facet`/`stage`/`ecosystem` assigned per [[classification-protocol]]; any new `concepts:` key added to [[controlled-vocabulary]].

## When the note makes LLVM claims
8. **Correctness** — fact-check each non-obvious LLVM claim against a **primary source** ([[source-hierarchy]]); set `status: verified` + `verified_on` only after checking; wrap anything unconfirmed in `> [!danger] Unverified`.
9. **Version** — version-dependent specifics carry the `version-sensitive` tag and link [[llvm-version]]; never hardcode a release number.
10. **Source link** — a note about a *specific LLVM pass/transformation* includes a **clickable GitHub source link** to the implementing file or directory (`https://github.com/llvm/llvm-project/blob/main/llvm/lib/…`) in the `[!quote]` footer. The `src:`/`implements:` frontmatter keeps the path; the footer makes it a link. (Paths are version-stable; the version lives in [[llvm-version]].)

## Reading pass
11. Each heading carries its point; the story is consistent across the note (and its chapter); the note is right-sized — cut redundancy, add only where a reader would be lost.

> [!tip] Automation
> Checks 1–4 are mechanical — the shell sweep in [[chapter-bridge-pipeline]] step 6 runs them across the vault. Checks 5–10 are judgment; do them per note. This is the manual form of the `vault-lint` + verify jobs in the blueprint.
