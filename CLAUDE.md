# CLAUDE.md — session contract for this vault

This repo is an **Obsidian vault**: a "living book" on LLVM/compilers. It is *content*, not code. Your job is to add and maintain notes **without re-deciding the taxonomy and without introducing drift**. The full rulebook lives in `_meta/` — this file is the short contract every session must honor. Read the linked `_meta/` note before doing the thing it governs.

## Invariants (never violate)

1. **One file = one topic.** If you can't say "this note is mainly about ⟨X⟩" in one sentence, it's two notes. → `_meta/classification-protocol.md`
2. **Folder = facet, and only facet.** The folder encodes exactly one axis. Everything else (stage, ecosystem, concept membership) is **frontmatter + links**, never new folders. Facets: `theory concept algorithm data-structure implementation application`.
3. **Vocabulary is closed where it says so.** `facet`, `stage`, `status` are finite; `ecosystem`/`concepts` grow but only deliberately. Reuse a value before minting one. Single source of truth: `_meta/controlled-vocabulary.md`.
4. **LLVM-first.** Describe LLVM directly with a worked example; a textbook is a `book:` field + a `[!quote] Further reading` footer, never `§x` citations in the body.
5. **No unverified claims silently.** Wrap anything unchecked in `> [!danger] Unverified` and keep `status` below `verified` until fact-checked against a primary source (`_meta/source-hierarchy.md`).

## Adding a note (the happy path)

1. Copy `_templates/topic-note.md` (or `_templates/concept-moc.md` for a chapter map, `_templates/implementation-note.md` for a single pass).
2. Assign axes with the decision trees in `_meta/classification-protocol.md`; pick existing values from `_meta/controlled-vocabulary.md`.
3. Write the arc (definition → theory/algorithm → in-LLVM example → use → limits) per `_meta/note-checklist.md`.
4. **Wire it:** cross-link related notes, and make sure it's reachable from a MOC (concept MOC under `_moc/concept/`, plus `_moc/ecosystem/LLVM.MOC.md`). If you introduce a new `concepts:` key, add it to the controlled vocabulary **and** create/extend its concept MOC.
5. If axis assignment is low-confidence, or the topic would mint a new top-level concept or ecosystem, set `status: needs-review` and surface it — don't guess silently.

## Definition of done (run before you finish — every session)

```
python3 _meta/vault-lint.py
```

Fix every **ERROR** it reports; triage **WARN**s. This is the mechanical half of `_meta/note-checklist.md` (the judgment half — correctness, right-sizing — is still on you). The linter is the already-planned `vault-lint` job from `_meta/chapter-bridge-pipeline.md` §Automation; it is the safety net that keeps the vault consistent across sessions, so **do not skip it**.

**CI runs the same check on every push and PR** (`.github/workflows/vault-lint.yml`), so an unfixed ERROR will fail the build. Run it locally first — don't rely on CI to catch what you could fix before committing.

## Inspecting LLVM source (tier-1 confirmation)

To verify an LLVM claim against the source itself (`_meta/source-hierarchy.md` tier 1):

- **Portable default (any surface, incl. cowork):** fetch the file at the pinned tag — `https://github.com/llvm/llvm-project/blob/<llvm_git_tag>/llvm/lib/…` (tag from `_meta/llvm-version.md`, *not* `main`, which drifts) via `WebFetch`/`gh`.
- **Local accelerator (dev machine):** the source is a git submodule at **`.llvm-project`** (dot-prefixed; Obsidian ignores it). Populate with `git submodule update --init --depth 1 .llvm-project`, grep it, then `git submodule deinit .llvm-project` to reclaim disk. Pinned to `llvm_git_tag`. **Never populate it casually** — this vault is in iCloud (see the warning in `_meta/llvm-version.md`).
- Bumping the LLVM version = moving the submodule pointer to a new release tag + updating `_meta/llvm-version.md` (full steps in that note).

## What travels to future sessions (incl. cowork/cloud)

Consistency rides on **committed files**, not chat history. `CLAUDE.md`, `_meta/`, `_templates/`, and `_moc/` are auto-available to any Claude Code surface working in this repo. Conversation context and `.claude/settings.local.json` do **not** travel. So: commit your structural changes, and rely on `vault-lint` (not memory) to prove consistency.

## Map

- `_meta/classification-protocol.md` — how to file any new topic
- `_meta/controlled-vocabulary.md` — the closed/open axis values (single source of truth)
- `_meta/note-checklist.md` — full definition of done
- `_meta/source-hierarchy.md` — citation trust order
- `_meta/callout-legend.md` — house-style callouts + Mermaid traps
- `_meta/chapter-bridge-pipeline.md` — the "connect textbook chapter N → LLVM" procedure
- `_meta/llvm-version.md` — the single version anchor (never hardcode release numbers)
- `Home.md` / `_moc/` — navigation
