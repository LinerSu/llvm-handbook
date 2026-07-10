export const meta = {
  name: 'note-improve',
  description: 'Pedagogy reviewer + LLVM-expert verifier panel on ≤3 notes; report structured, expert-approved improvement proposals (never edits files)',
  whenToUse: 'Per-batch understanding/pedagogy pass of the improvement loop (see _meta/improvement-ledger.md). args: { base: "<abs repo root>", notes: ["<relpath>", ...], persona?: "student" } — max 3 notes per run. Default persona is a first-time learner (tends to ADD scaffolding); persona "student" is a compilers-course CS student (tends to CUT words and swap prose for visuals). The main session applies approved fixes, runs vault-lint, updates the ledger.',
  phases: [
    { title: 'Pedagogy', detail: 'one learner-persona reviewer per note' },
    { title: 'Expert verify', detail: 'one skeptical LLVM expert per note with proposals' },
  ],
}

// ---- Phase A output: pedagogy proposals ----
const PROPOSALS = {
  type: 'object',
  additionalProperties: false,
  required: ['clarity_ok', 'proposals'],
  properties: {
    clarity_ok: { type: 'boolean', description: 'true if the note already teaches well and needs no changes' },
    proposals: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['kind', 'location_quote', 'problem', 'proposal_text', 'fix_class', 'old_string', 'new_string'],
        properties: {
          kind: { type: 'string', enum: ['clarify', 'reorder', 'add_worked_step', 'add_question', 'add_diagram', 'tighten'] },
          location_quote: { type: 'string', description: 'exact text from the note marking WHERE the problem is' },
          problem: { type: 'string', description: 'what a first-time learner stumbles on here, and why' },
          proposal_text: { type: 'string', description: 'the improvement, concretely — full replacement/addition text where possible' },
          fix_class: { type: 'string', enum: ['low_risk_autofix', 'judgment_call'] },
          old_string: { type: 'string', description: 'VERBATIM substring of the file to replace (low_risk_autofix only; else "")' },
          new_string: { type: 'string', description: 'replacement text (low_risk_autofix only; else "")' },
        },
      },
    },
  },
}

// ---- Phase B output: expert verdicts on the proposals ----
const VERDICTS = {
  type: 'object',
  additionalProperties: false,
  required: ['verdicts'],
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['index', 'verdict', 'reason', 'evidence', 'revised_new_string'],
        properties: {
          index: { type: 'integer', description: '0-based index into the proposals array you were given' },
          verdict: { type: 'string', enum: ['approve', 'revise', 'reject'] },
          reason: { type: 'string', description: 'one line: why approved/revised/rejected' },
          evidence: { type: 'string', description: 'primary-source URL + one line for any technical claim touched; "" if none needed' },
          revised_new_string: { type: 'string', description: 'corrected replacement text (verdict=revise only; else "")' },
        },
      },
    },
  },
}

const pedagogyPrompt = (abs, rel) => `You are reviewing ONE study note as a FIRST-TIME LEARNER of compilers, to find where it fails to teach.

Note file (read it with Read): ${abs}
(vault-relative note id: ${rel})

CONTEXT
- This vault is a "living book" on LLVM. House rules you must respect (do not propose violating them):
  - Note arc: definition → theory/algorithm → in-LLVM worked example → where used → limitations.
  - House callouts per _meta/callout-legend.md ([!note] definition, [!example] worked code, [!question] predict-first prompt, [!warning] pitfall, [!summary] takeaway); Mermaid for structural diagrams.
  - Worked examples should reuse application/running-example.md (read it if the note links it), not invent new programs.
- Your scope is PEDAGOGY, not fact-checking: unclear explanations, steps a learner cannot follow, missing intermediate steps in worked examples, concepts used before defined, missing "why do I care", a section that assumes context the note never gives, a spot begging for a predict-first [!question].

WHAT NOT TO REPORT
- Style/formatting nits, link hygiene, frontmatter — the linter owns those.
- Rewording that is merely different, not clearer.
- Additions that would bloat the note: it should stay right-sized; prefer sharpening over expanding.

PROPOSALS
- Be selective: the 2–6 changes with the highest learner payoff, not an exhaustive list.
- For each, give location_quote VERBATIM from the file, the learner's problem, and concrete proposal_text.
- fix_class = "low_risk_autofix" ONLY if the change is a self-contained textual replacement that cannot change technical meaning ambiguously, with old_string a VERBATIM unique substring of the file and new_string the full replacement. Anything structural (reorder, new section, new example) = "judgment_call" with old_string="" and new_string="".
- If the note already teaches well, return { "clarity_ok": true, "proposals": [] }.

Return ONLY the structured object.`

const studentPrompt = (abs, rel) => `You are reviewing ONE study note as a CS student who has TAKEN a compilers course and has some LLVM background (you know SSA, CFGs, basic passes; you read IR fine). You are studying from this vault and want it to teach you FASTER.

Note file (read it with Read): ${abs}
(vault-relative note id: ${rel})

CONTEXT
- This vault is a "living book" on LLVM. House rules (do not propose violating them): note arc definition → theory/algorithm → in-LLVM worked example → uses → limits; house callouts per _meta/callout-legend.md; Mermaid for static structure; animated GIFs (via _meta/anim storyboards) for step-by-step processes; worked examples reuse application/running-example.md.
- Several notes already carry an animation in a [!figure] callout — treat those as load-bearing, not decoration.

YOUR REVIEW BIAS — this is the whole point:
- The default failure mode of study notes is TOO MANY WORDS. Prefer proposals that make the note SHORTER or shift weight from prose to a visual. The note's net word count should go DOWN or stay flat after your proposals; only add text when something is genuinely missing for a reader at YOUR level (not a beginner's level — the beginner pass already ran).
- kind=tighten: cut redundancy, throat-clearing, repeated framing, over-hedged sentences, explanations of things any compilers student knows (what a CFG is, what a pass is). Give exact old_string → shorter new_string.
- kind=add_diagram: a paragraph that narrates structure or a step sequence in prose is a candidate to be REPLACED (not supplemented) by a Mermaid diagram or an animated GIF. Describe precisely what the visual should show and WHICH sentences it replaces or shortens. Do not draw it yourself.
- kind=clarify/reorder: only when a sentence is confusing at your level, or information is ordered so you must jump around. Rewrites must not be longer than the original.
- Also flag (kind=add_worked_step, sparingly): a spot where you, as a student, would want ONE reproduce-it-yourself command (clang/opt one-liner) instead of three sentences of description.
- Compress with Obsidian affordances, not prose: parallel facts → a table; contrasts → a two-column table; asides → a collapsed callout ([!info]- / [!example]-); use ==highlight==, inline \`code\`, and arrows/symbols (→, ⇒, ≤) instead of connective sentences. Raw HTML (<details>, <sub>) only when markdown genuinely can't do it.
- Video (rare, max 1 per note): if a well-known, high-quality talk/lecture exists for exactly this topic (e.g. an LLVM Developers' Meeting tutorial on YouTube), propose adding ONE link in the [!quote] footer — verify the exact title + URL with WebSearch first (load it via ToolSearch if needed) and put the URL in proposal_text. Never propose a link you did not verify.

WHAT NOT TO REPORT
- Style/formatting/links/frontmatter (the linter owns those); factual review (a separate pass owns that).
- Cuts that would remove a correctness qualifier, a version caveat, a citation, or a [!danger] marker.
- Rewording that is merely different, not shorter or clearer.

PROPOSALS
- 2–6 with the highest payoff. For each: location_quote VERBATIM, the problem AT YOUR LEVEL, concrete proposal_text.
- fix_class = "low_risk_autofix" ONLY for a self-contained textual replacement with a VERBATIM unique old_string and complete new_string. Structural moves and visual replacements = "judgment_call" (old_string="", new_string="").
- If the note is already tight and well-illustrated, return { "clarity_ok": true, "proposals": [] }.

Return ONLY the structured object.`

const expertPrompt = (abs, rel, proposals) => `You are a skeptical expert in LLVM and compiler theory. A pedagogy reviewer proposed changes to ONE study note; you must verify them TECHNICALLY before they can be applied.

Note file (read it with Read): ${abs}
(vault-relative note id: ${rel})

The proposals (JSON array; judge each by its 0-based index):
${JSON.stringify(proposals, null, 2)}

CONTEXT
- The vault tracks LLVM 22.1.x (release tag llvmorg-22.1.8). Judge version-specific claims against that.
- The pedagogy reviewer optimizes for learnability and may have introduced technically wrong, misleading, or imprecise statements. Your job is to catch that.

VERIFY (this is a web-verified pass):
- For every proposal whose text makes or changes an LLVM/compiler-theory claim, CHECK the claim against a PRIMARY source before approving: llvm.org/docs (LangRef, pass docs, release notes) and the source at github.com/llvm/llvm-project (use the llvmorg-22.1.8 tag, not main). Use WebSearch/WebFetch (load them via ToolSearch if needed).
- Put the source URL (+ one line) in 'evidence'. A proposal that adds a technical claim you cannot verify must NOT be approved as-is — revise it to a verifiable statement or reject it.

VERDICTS
- approve: technically sound as written (evidence attached where a claim was checked).
- revise: right idea, wrong or imprecise details — supply revised_new_string (a full corrected replacement for the proposal's new_string/proposal_text; keep the pedagogical intent).
- reject: technically wrong, would mislead, or pedagogically negative (say why in reason).
- Judge EVERY proposal by index. BE CONSERVATIVE — an unverified technical claim is a reason to revise or reject, not to approve.

Return ONLY the structured object.`

let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { throw new Error('args string was not valid JSON: ' + e.message) } }
const BASE = A && A.base
const NOTES = A && A.notes
if (!BASE || !Array.isArray(NOTES)) throw new Error('args must be { base, notes: [...] }; got: ' + typeof args)
if (NOTES.length > 3) throw new Error('max 3 notes per run (small batches — see _meta/improvement-ledger.md); got ' + NOTES.length)
const PERSONA = (A && A.persona) === 'student' ? studentPrompt : pedagogyPrompt

const perNote = (await pipeline(
  NOTES,
  (rel) => agent(PERSONA(`${BASE}/${rel}`, rel), { label: `pedagogy:${rel}`, phase: 'Pedagogy', schema: PROPOSALS }),
  async (review, rel) => {
    if (!review) return null
    const proposals = review.proposals || []
    if (proposals.length === 0) return { note: rel, clarity_ok: !!review.clarity_ok, proposals: [] }
    const judged = await agent(expertPrompt(`${BASE}/${rel}`, rel, proposals), { label: `expert:${rel}`, phase: 'Expert verify', schema: VERDICTS })
    const byIndex = {}
    for (const v of (judged && judged.verdicts) || []) byIndex[v.index] = v
    return {
      note: rel,
      clarity_ok: !!review.clarity_ok,
      proposals: proposals.map((p, i) => ({
        ...p,
        note: rel,
        verdict: byIndex[i] ? byIndex[i].verdict : 'unjudged',
        verdict_reason: byIndex[i] ? byIndex[i].reason : 'expert agent did not return a verdict for this index',
        evidence: byIndex[i] ? byIndex[i].evidence : '',
        revised_new_string: byIndex[i] ? byIndex[i].revised_new_string : '',
      })),
    }
  }
)).filter(Boolean)

const all = perNote.flatMap((r) => r.proposals)
const approved = all.filter((p) => p.verdict === 'approve')
const revised = all.filter((p) => p.verdict === 'revise')
const autofixable = approved.filter((p) => p.fix_class === 'low_risk_autofix' && p.old_string)

log(`Reviewed ${perNote.length}/${NOTES.length} notes; ${all.length} proposals — ${approved.length} approved (${autofixable.length} autofixable), ${revised.length} revised, ${all.filter((p) => p.verdict === 'reject').length} rejected`)

return {
  reviewed: perNote.length,
  total: NOTES.length,
  counts: {
    proposals: all.length,
    approved: approved.length,
    revised: revised.length,
    rejected: all.filter((p) => p.verdict === 'reject').length,
    unjudged: all.filter((p) => p.verdict === 'unjudged').length,
    autofixable: autofixable.length,
  },
  perNote,
}
