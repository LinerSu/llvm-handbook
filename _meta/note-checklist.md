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
   - **Reuse the running example** ([[running-example]]) — link the relevant anchor and show only the slice you need, rather than inventing a fresh program. Mint a new example *only* when the running one genuinely can't show the concept; if you extend it, add the extension to [[running-example]] §7 (one place), not scattered across notes. Prefer **real `clang`/`opt` output** over hand-written IR (hand-authored examples are how subtly-wrong ones creep in).
7. **Classification** — `facet`/`stage`/`ecosystem` assigned per [[classification-protocol]]; any new `concepts:` key added to [[controlled-vocabulary]].

## When the note makes LLVM claims

> [!danger] What `status: verified` means — read this before setting it
> **`verified` = every falsifiable claim in this note was checked against LLVM source at the tag in [[llvm-version]], on the date in `verified_on`.** It does *not* mean the note reads plausibly, that `vault-lint` passed, or that a web search agreed. If you did not open the file, the note is **`unverified`**. That is a normal, honest status — 69 notes carried it after the 2026-07-16 audit.
>
> This bar exists because the vault failed it. From the initial commit until 2026-07-16, every note was born `status: verified`; `verified_on` recorded the authoring date, not a check. A correctness pass did run, was **web**-verified, edited [[dominator-tree]], and still left five wrong claims in it — including that LLVM builds dominator trees with "near-linear **Lengauer–Tarjan**" when it ships **Semi-NCA**. Measured error rate across a 9-note sample: **13 of 132 claims refuted (9.8%); 8 of 9 notes wrong.**

8. **Correctness** — **enumerate every falsifiable claim** (one naming an LLVM pass, class, file, function, flag, default, algorithm, complexity, or version) and check **each** against tier-1 source ([[source-hierarchy]]) at the tag in [[llvm-version]]. Then set `status: verified` + `verified_on`. Wrap anything unconfirmed in `> [!danger] Unverified` and leave the note `unverified`.
   - **Check every claim, not the doubtful ones.** Verification triggered by suspicion is a *plausibility filter*: it catches only claims that look wrong, which is the exact complement of the dangerous set. The claims that survive are the confident, wrong, well-written ones.
   - **Search is not evidence.** It cannot catch an error the web shares — and in the 2026-07-16 audit, **10/10 refuted claims were ones search would have confirmed**. Tier-3 docs "can lag the code"; tier-4 blogs are "never the sole citation".
   - **LLVM's own comments are not evidence either.** `GVN.cpp` carries `// Top-down walk of the dominator tree.` directly above `ReversePostOrderTraversal<Function *> RPOT(&F);` — a vault note copied that comment and was wrong for it. The code is truth; the comment beside it is a claim.
   - **The standing check for any "pass X uses/enables Y" claim is the `cl::opt` default** — find the `cl::init(...)` and read it. The failure pattern is always "the feature exists, so it reads true, but it's off by default or is an enhancement rather than the mechanism". This one check refuted two claims in the audit.
   - **A wrong refutation is as costly as the original error.** Before contradicting a note, rule out: non-default flags, virtual dispatch, template instantiations, semantics-vs-procedure, classic-theory register, target overrides, incomplete≠contradicted, and deliberately out-of-tree subjects. Discarding your own draft refutation is a success.
   - Automated by the `note-correctness-review` skill, which implements exactly this and reports an **error rate** — a pass with no denominator can't tell you whether the badge means anything.
9. **Version** — version-dependent specifics carry the `version-sensitive` tag and link [[llvm-version]]; never hardcode a release number. On a bump, re-verify that note's claims **against source** and re-stamp `verified_on`; a stale `verified_on` on a `version-sensitive` note is a `vault-lint` WARN.
10. **Source link** — a note about a *specific LLVM pass/transformation* includes a **clickable GitHub source link** to the implementing file or directory (`https://github.com/llvm/llvm-project/blob/main/llvm/lib/…`) in the `[!quote]` footer. The `src:`/`implements:` frontmatter keeps the path; the footer makes it a link. (Paths are version-stable; the version lives in [[llvm-version]].)
    - **These links track `main` for navigation — they are not the verified revision.** Verification happens at the tag; `main` may have drifted since. Say so in the footer rather than letting "verified" sit next to a `main` URL, which reads as though `main` is what was checked.

## Reading pass
11. Each heading carries its point; the story is consistent across the note (and its chapter); the note is right-sized — cut redundancy, add only where a reader would be lost.

> [!tip] Automation
> Checks 1–4 (plus the frontmatter contract in 6 and classification in 7) are mechanical and **implemented** as `vault-lint` — run `python3 _meta/vault-lint.py` before finishing any session; fix every ERROR, triage WARNs. Checks 5, 8–11 are judgment; do them per note. The linter is the session-level safety net referenced by [[chapter-bridge-pipeline]] §Automation and the root `CLAUDE.md` contract.
