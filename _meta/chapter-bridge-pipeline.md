---
title: Pipeline — connect a textbook chapter to the LLVM vault
type: meta
tags: [meta, rulebook, pipeline]
---

# Pipeline — "build Dragon Book Chapter N → LLVM"

The repeatable procedure for the recurring request *"take chapter N of the Dragon Book (or another compiler text) and connect it to LLVM."* Run the steps in order. The guiding rule is **LLVM-first**: **describe LLVM directly with examples; the book is a footer reference, never a side-by-side comparison.**

## 1. Parse the chapter (ground in the source)
- Extract the real TOC from the PDF: `pdftotext book.pdf /tmp/b.txt`, then grep the TOC region for `^N\.[0-9]+ ` headings. Don't work from memory — confirm exact section titles/numbers.

## 2. Assess LLVM relevance (the "what do you think" step)
For each section, classify: **HIGH** (LLVM implements it directly), **MEDIUM** (partial / frontend-runtime), **LOW** (not LLVM-central). For each HIGH/MEDIUM item record: *what LLVM actually has*, *which existing vault note already covers it*, and *what is genuinely new*. Surface this assessment and confirm scope before building a lot.

## 3. Write each new note — LLVM-first (see [[classification-protocol]])
- **Frontmatter contract:** `title, facet, stage, ecosystem, concepts, implements:[{ecosystem,src}], src, docs, book:"… §N.x", prereqs, related, tags, status, verified_on`.
- **Body arc:** definition → theory/algorithm → **in LLVM** (with a worked `.ll`/MIR example) → where it's used → limitations. One concrete example per idea (per **LLVM-first**).
- **Diagram where shape is the point:** a `mermaid` block for CFG / DAG / tree / lattice / pipeline (see [[callout-legend]] for the syntax traps).
- **`[!summary]` takeaway** (one line a scanner can grab) and a **`[!quote] Further reading`** footer — the only place the book `§N.x` is cited. No `§` in the body.

## 4. Build the bridge MOC `_moc/book/dragon-book-chN.MOC`
A **reading map**, not a comparison: a `§ → LLVM realization → vault note` table, a short reading path, a "what's different in modern LLVM" note, and a Dataview block `WHERE book AND contains(book, "§N")`.

## 5. Wire
Add new `concepts:` keys to [[controlled-vocabulary]]; add the bridge to [[Home]] ("Book bridges") and [[LLVM.MOC]]; add cross-links from related existing notes to the new ones.

## 6. Checks (run the sweep — see [[callout-legend]]; full definition of done: [[note-checklist]])
- callout **tables** glued to a sentence (need a blank `>`); Mermaid labels (no leading `-`/`+`/`*`, no `<`/`>`); code-fence parity (even); dangling/unresolved links. Fix before review.

## 7. Review (the correctness pass — see [[source-hierarchy]])
- **Fact-check every non-obvious LLVM claim against a primary source** (LLVM docs, blog, source). Set `status: verified` + `verified_on` only after checking; flag the unverifiable with `> [!danger] Unverified`.
- **Reading flow:** confirm each heading carries its point, the story is consistent across the chapter's notes, and the note is right-sized (cut redundancy, add only where a reader would be lost).

## Automation (future)
This is the manual form. The automated form (from the vault blueprint) is a `compiler-note` **skill** (steps 3–5), a verify **sub-agent** (step 7 fact-check), and a `vault-lint` **scheduled task** (step 6). Skills can't be installed from a Cowork session — create them in Settings → Capabilities using this doc as the spec.
