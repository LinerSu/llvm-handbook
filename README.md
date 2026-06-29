# LLVM Study Notes

A personal, evolving set of notes on LLVM — its IR, passes, analyses, data structures, and surrounding tooling. The notes are written as a small interlinked "living book": layered topic folders, concept maps (MOCs), and heavy cross-linking. Drafted with LLM assistance and curated by hand.

## Read it in Obsidian

These notes are an [Obsidian](https://obsidian.md) vault. They use wikilinks, callouts, tags, embedded diagrams, and inline queries, so plain Markdown viewers (including GitHub's renderer) will show the raw syntax rather than the intended result. For the real reading experience:

1. Clone or download this repository.
2. In Obsidian: **Open folder as vault** → select the cloned folder.
3. Enable the required community plugin below, then open `Home.md` to start.

### Required plugin

- **[Dataview](https://github.com/blacksmithgu/obsidian-dataview)** — 11 notes embed `dataview` query blocks (index pages and MOCs that auto-list notes). Without it, those blocks render as empty code fences. Install via **Settings → Community plugins → Browse → "Dataview"**, then enable it.

That is the only third-party plugin a reader needs. Everything else relies on Obsidian **core** features that ship enabled by default:

- Wikilinks and backlinks (graph navigation)
- Callouts (`> [!note]`, `> [!warning]`, …)
- Tags and frontmatter properties
- Mermaid diagrams (13 notes)
- MathJax for the occasional `$$ … $$` block

### Optional, for contributors

- **Templater** — only if you want to author new notes from the templates in `_templates/`. Not needed to read.

## Layout

```
Home.md            Entry point / dashboard
_moc/              Maps of Content: book/, concept/, ecosystem/, stage/
_meta/             Notes about the vault itself (conventions, structure)
_templates/        Note templates (authoring only)
theory/            Foundations and semantics
concept/           Core LLVM concepts (+ attachments/)
algorithm/         Pass and analysis algorithms
data-structure/    IR and in-memory data structures (+ attachments/)
implementation/    How things are built in the LLVM codebase
application/       Worked examples and end-to-end uses
```

Start at `Home.md` or any `_moc/` map and follow the links.

## How these notes were made

Content was drafted collaboratively with a large language model and then reviewed and edited. Treat it as study notes, not authoritative documentation: verify against the [official LLVM documentation](https://llvm.org/docs/) and source before relying on any detail. Corrections are welcome.

Image attachments may include excerpts or adaptations from external sources for educational purposes; rights to any such excerpts remain with their original holders and are not covered by the license below.

## License

The notes (text and original diagrams) are licensed under **[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)** — see [`LICENSE`](LICENSE). You may share and adapt them, including commercially, with attribution.
