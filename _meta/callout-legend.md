---
title: Callout Legend
type: meta
tags: [meta, rulebook]
---

# Callout Legend

The house-style callouts used across notes (Obsidian admonitions). Keep usage consistent so notes read uniformly.

| Callout | Use for |
|---|---|
| `[!abstract]` | the chapter map / what the note delivers |
| `[!info]` | a definition's context, a comparison table, "classic theory → LLVM" |
| `[!note]` | a crisp definition |
| `[!tip]` | a method, habit, or practical win |
| `[!example]` | worked IR / code to reproduce (use `+`/`-` to default-open/closed) |
| `[!figure]` | an embedded image (diagram) |
| `[!warning]` | a pitfall, legality condition, or common confusion |
| `[!question]` | predict-first / think-about-it prompt |
| `[!summary]` | "things to always remember" |
| `[!quote]` | sources, or a quoted design observation |
| `[!danger]` | **Unverified / source-unchecked** claim — must be resolved by the verify pass before `status: verified` |

## Diagrams

Use fenced `mermaid` code blocks (Obsidian renders them natively) for structure that text can't carry — **CFGs, expression DAGs, dominator trees, lattices**. Convention: a **bold caption** line above, a one-sentence reading below, and keep the block at the top level (not nested inside a `>` callout) so it always renders. Prefer Mermaid over pasted images for new diagrams — it stays editable and diff-friendly.

Two Mermaid gotchas that silently break rendering: a node label must **not start with `-`, `+`, or `*`** (parsed as a markdown list → "Unsupported markdown: list" — use `(+)` not `+`), and **avoid `<`/`>` inside labels** (treated as HTML).

## Tables & lists inside callouts

A markdown **table** inside a `> [!callout]` placed **after a sentence** needs a **blank `>` separator line** before it — otherwise Obsidian glues the header to the sentence and renders the raw `| … |` text. (A table directly under the `[!type]` title line is fine.) Bulleted/numbered lists usually render either way, but a blank `>` before them never hurts.
