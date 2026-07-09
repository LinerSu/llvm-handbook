export const meta = {
  name: 'note-animate',
  description: 'Author + render an explanatory GIF per note (≤3) via _meta/anim storyboards, with a fresh-eyes visual review loop; the note embed is left to the main session',
  whenToUse: 'Per-batch animation pass of the improvement loop (see _meta/improvement-ledger.md and _meta/anim/storyboard-spec.md). args: { base: "<abs repo root>", notes: ["<relpath>", ...], scratch: "<abs scratch dir for QA frames>" } — max 3 notes per run. On success each note has a committed-ready storyboard JSON + GIF; the main session embeds the [!figure], lints, updates the ledger.',
  phases: [
    { title: 'Animate', detail: 'author storyboard, render, self-QA against frame PNGs' },
    { title: 'Visual review', detail: 'fresh-eyes reviewer judges the rendered frames' },
  ],
}

// ---- Phase A output: authored + rendered animation ----
const AUTHORED = {
  type: 'object',
  additionalProperties: false,
  required: ['worth_animating', 'process', 'example_source', 'storyboard', 'gif', 'sheet', 'frames_dir', 'gif_bytes', 'notes_for_embed'],
  properties: {
    worth_animating: { type: 'boolean', description: 'false if NO process in this note genuinely benefits from motion over the existing static/Mermaid diagrams — then all other fields are ""/0' },
    process: { type: 'string', description: 'the one step-by-step process the animation teaches' },
    example_source: { type: 'string', description: 'where the program came from (e.g. "running-example §2 pre-mem2reg CFG" or "the note\'s §4 worked example") — animations must reuse an existing example' },
    storyboard: { type: 'string', description: 'abs path of the storyboard JSON written under _meta/anim/storyboards/' },
    gif: { type: 'string', description: 'abs path of the rendered GIF in the note\'s facet attachments/ dir' },
    sheet: { type: 'string', description: 'abs path of the QA contact sheet PNG' },
    frames_dir: { type: 'string', description: 'abs dir holding the QA frame PNGs' },
    gif_bytes: { type: 'integer' },
    notes_for_embed: { type: 'string', description: 'one-sentence reading of the animation, ready for the [!figure] caption line' },
  },
}

// ---- Phase B output: fresh-eyes visual verdict ----
const REVIEW = {
  type: 'object',
  additionalProperties: false,
  required: ['pass', 'issues'],
  properties: {
    pass: { type: 'boolean' },
    issues: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['frame', 'problem', 'fix'],
        properties: {
          frame: { type: 'integer', description: 'frame number (0-based) where the problem shows; -1 if it spans the whole animation' },
          problem: { type: 'string', description: 'what is unreadable, wrong, or confusing' },
          fix: { type: 'string', description: 'the concrete storyboard change that would fix it' },
        },
      },
    },
  },
}

const authorPrompt = (base, abs, rel, scratch, rework) => `You are creating ONE animated GIF that teaches a step-by-step process from ONE study note, by authoring a storyboard JSON and rendering it.

Note file (read it with Read): ${abs}
(vault-relative note id: ${rel})
Repo root: ${base}
Scratch dir for QA frames: ${scratch}

DO, in order:
1. Read ${base}/_meta/anim/storyboard-spec.md — it is the full authoring contract (schema, styles, glyph rules, size budget). Follow it exactly.
2. Read the note. Pick THE ONE step-by-step process where MOTION teaches something the note's existing static/Mermaid figures cannot (worklist iteration, insertion order, propagation…). If the note links application/running-example.md for its example, read that too.
   - HARD RULE: the animation must replay an example that ALREADY EXISTS in the note or the running example. Never invent a new program. Record where it came from in example_source.
   - If genuinely nothing in the note benefits from motion, return worth_animating=false and stop — do not force an animation.
3. Write the storyboard to ${base}/_meta/anim/storyboards/<id>.json with id "<note-basename>-<short-topic>" (e.g. "mem2reg-promotion"). 6–14 content frames, one idea per frame, captions that carry the narration, and a summary_caption.
4. Render: python3 ${base}/_meta/anim/render.py <storyboard> --gif-dir ${base}/<note's facet folder>/attachments --frames-dir ${scratch}/<id>
5. SELF-QA: Read the contact sheet <id>-sheet.png AND flip through the individual fNN.png frames with Read. Fix EVERY "WARN:" line the renderer printed (label overflow, tofu glyphs, size) and anything you can SEE is wrong: overlapping edges/labels, a step that contradicts the algorithm, a caption that doesn't match what changed in the frame. Edit the JSON and re-render until clean. Check the algorithm trace like an examiner: every frame must show a true intermediate state.
${rework ? `\nThis is a REWORK. A fresh-eyes reviewer rejected the previous attempt at <id> for these issues — fix ALL of them (the storyboard JSON from the previous attempt is still on disk; edit it rather than starting over):\n${rework}\n` : ''}
Return ONLY the structured object (worth_animating=true plus the paths/fields, or worth_animating=false).`

const reviewPrompt = (abs, rel, authored) => `You are a fresh-eyes visual reviewer. Someone else authored an animated GIF for a study note; judge the RENDERED FRAMES — you did not make them, be skeptical.

Note file (read it with Read): ${abs}
(vault-relative note id: ${rel})
Claimed process: ${authored.process}
Claimed example source: ${authored.example_source}
Contact sheet (Read it): ${authored.sheet}
Individual frames (Read several, especially any you doubt): ${authored.frames_dir}/f00.png, f01.png, ...
Storyboard JSON (for reference): ${authored.storyboard}

JUDGE four things, by LOOKING at the frames:
1. Readable at a glance: labels legible, nothing overlapping or clipped, no tofu boxes (□), captions fit.
2. Algorithm correctness: replay the algorithm yourself from the note; every frame must show a TRUE intermediate state, in the right order, with the highlight on the thing actually happening at that step. This is the most important check.
3. Example fidelity: the program shown must match the note's / running example's actual code and block names — not an invented one.
4. Narrative: captions form a coherent story; the summary frame states the takeaway; one idea per frame.

pass=true only if ALL four hold. Otherwise list every issue with the frame number and a CONCRETE storyboard-level fix. Do not nitpick aesthetics that don't impair reading.

Return ONLY the structured object.`

let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { throw new Error('args string was not valid JSON: ' + e.message) } }
const BASE = A && A.base
const NOTES = A && A.notes
const SCRATCH = A && A.scratch
if (!BASE || !Array.isArray(NOTES) || !SCRATCH) throw new Error('args must be { base, notes: [...], scratch }; got: ' + typeof args)
if (NOTES.length > 3) throw new Error('max 3 notes per run (small batches — see _meta/improvement-ledger.md); got ' + NOTES.length)

const MAX_ATTEMPTS = 2

const perNote = (await pipeline(
  NOTES,
  async (rel) => {
    const abs = `${BASE}/${rel}`
    let rework = ''
    let authored = null
    let review = null
    for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
      authored = await agent(authorPrompt(BASE, abs, rel, SCRATCH, rework), { label: `animate:${rel} (attempt ${attempt})`, phase: 'Animate', schema: AUTHORED })
      if (!authored) return null
      if (!authored.worth_animating) return { note: rel, verdict: 'not-animation-worthy', authored, issues: [] }
      review = await agent(reviewPrompt(abs, rel, authored), { label: `review:${rel} (attempt ${attempt})`, phase: 'Visual review', schema: REVIEW })
      if (review && review.pass) return { note: rel, verdict: 'pass', authored, issues: [] }
      const issues = (review && review.issues) || [{ frame: -1, problem: 'reviewer agent died', fix: 'rerun' }]
      rework = issues.map((i) => `- frame ${i.frame}: ${i.problem} — fix: ${i.fix}`).join('\n')
    }
    return { note: rel, verdict: 'needs-human', authored, issues: (review && review.issues) || [] }
  }
)).filter(Boolean)

const passed = perNote.filter((r) => r.verdict === 'pass')
log(`Animated ${passed.length}/${NOTES.length} notes (${perNote.filter((r) => r.verdict === 'needs-human').length} need human review, ${perNote.filter((r) => r.verdict === 'not-animation-worthy').length} judged not animation-worthy)`)

return { perNote }
