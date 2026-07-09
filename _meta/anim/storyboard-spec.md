---
title: Storyboard Spec (GIF animations)
type: meta
tags: [meta, rulebook]
---

# Storyboard spec — authoring animated GIFs for notes

A **storyboard** is a JSON file in `_meta/anim/storyboards/` that declaratively describes a CFG-style diagram and a sequence of **cumulative frames**. The renderer (`_meta/anim/render.py`) turns it into an animated GIF in the note's facet `attachments/` folder. The JSON is the committed source of truth; the GIF is a build artifact (also committed, since Obsidian embeds it).

## Ground rules

1. **One animation = one process.** Pick the single step-by-step process in the note where *motion* teaches something a static Mermaid diagram can't (worklist iteration, φ insertion, coloring order…). The Mermaid/static figure stays the primary diagram — the GIF supplements it (see `_meta/callout-legend.md`).
2. **Reuse the note's own worked example** (usually a slice of `application/running-example.md`). Never invent a new program for an animation.
3. **Readers can't pause a GIF.** Keep 6–14 frames, slow steps (default 1400 ms), one idea per frame, and write a `summary_caption` — the renderer appends a final summary frame held for `hold_ms`.
4. **You never pick colors.** Use the named styles; the renderer owns the palette.
5. **Mind the glyphs.** Captions/edge labels render in Helvetica, which lacks set/arrow symbols (`∈ ⊆ ∪ → ⇒ ∅ ⊥`…) — write them out in words (`DF(x) = {y}`, "maps to"). Node labels/badges use Menlo, which has most math glyphs (`φ ∈ →` are fine there). The renderer emits a `WARN:` for any character that would render as a tofu box — treat every WARN as a bug.

## Schema

```jsonc
{
  "id": "ssa-form-phi-placement",        // filename-safe; names the .gif
  "title": "φ placement via dominance frontiers",   // header, every frame
  "canvas": { "cols": 3, "rows": 4, "cell": [230, 110], "margin": 24 },
  "defaults": { "step_ms": 1400, "hold_ms": 3200 },  // optional
  "summary_caption": "One φ at the join — exactly what mem2reg emits.",
  "nodes": [
    { "id": "entry", "at": [1, 0], "label": "entry\nsum = 0", "shape": "box" }
    // shape: box | rounded | diamond   (diamond = branch; keep its label short)
    // at: [col, row], 0-based; one node per cell
  ],
  "edges": [
    { "from": "entry", "to": "cond" },
    { "from": "inc", "to": "cond", "curve": "left", "label": "back edge" }
    // curve: none | left | right  ('left' bulges to the left of travel direction)
  ],
  "frames": [
    {
      "caption": "Step 1 — sum is defined in entry and in for.body",
      "nodes": { "entry": "active", "body": "active" },   // node id -> style
      "edges": { "inc->cond": "active" },                 // "from->to" -> style
      "set_labels": { "cond": "for.cond\nsum1 = φ(…)" },  // persistent label change
      "badges": [ { "node": "cond", "text": "+φ", "style": "new" } ],
      "clear_badges": false,        // true to drop all earlier badges first
      "duration_ms": 1800           // optional per-frame override (200..10000)
    }
  ]
}
```

**Frames are cumulative:** each frame inherits the previous frame's node/edge styles, labels, and badges, then applies its own overrides. To "un-highlight" something, set it back explicitly (e.g. to `done` or `normal`).

**Styles** (nodes, edges, badges): `normal` · `active` (amber — the thing happening now) · `done` (green — settled) · `dim` (grey — out of play) · `new` (blue — just created) · `error` (red outline — the pitfall).

## Workflow (author agent)

1. Write the JSON to `_meta/anim/storyboards/<id>.json`.
2. Render with QA frames into your scratch dir:

   ```sh
   python3 _meta/anim/render.py _meta/anim/storyboards/<id>.json \
       --gif-dir <facet>/attachments --frames-dir <scratch>/<id>
   ```

3. **Look at the output** — Read `<scratch>/<id>/<id>-sheet.png` (contact sheet) and individual `fNN.png` frames. Fix every `WARN:` (label overflow, caption wrap, GIF > 1.5 MB) and anything unreadable; re-render. The GIF itself shows only its first frame to the Read tool — always QA via the PNGs.
4. Keep the GIF small: ≤ 14 content frames, canvas ≤ ~800 px wide (cols × cell width), flat labels.

## Embedding (main session)

```markdown
> [!figure]+ Animation — φ placement on the running example
> ![ssa-form-phi-placement.gif](attachments/ssa-form-phi-placement.gif)
> One-sentence reading of the animation. (Regenerate: `_meta/anim/storyboards/ssa-form-phi-placement.json`.)
```
