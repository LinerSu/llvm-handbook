export const meta = {
  name: 'note-correctness-review',
  description: 'Skeptically read each vault note and web-verify dubious LLVM claims against primary sources; report findings + proposed low-risk fixes',
  whenToUse: 'Periodic correctness audit of the LLVM vault (the "verify pass" from _meta/note-checklist + chapter-bridge-pipeline). args: { base: "<abs repo root>", notes: ["<relpath>", ...] }',
  phases: [{ title: 'Review', detail: 'one skeptical reader-verifier per note' }],
}

// ---- structured output every reviewer must return ----
const FINDINGS = {
  type: 'object',
  additionalProperties: false,
  required: ['notes_ok', 'findings'],
  properties: {
    notes_ok: { type: 'boolean', description: 'true if the note has no correctness problems' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['severity', 'type', 'quote', 'problem', 'correction', 'evidence', 'fix_class', 'old_string', 'new_string'],
        properties: {
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          type: { type: 'string', enum: ['incorrect', 'misleading', 'outdated', 'imprecise', 'unverifiable'] },
          quote: { type: 'string', description: 'exact text from the note that is problematic' },
          problem: { type: 'string', description: 'what is wrong and why a learner would be misled' },
          correction: { type: 'string', description: 'what it should say' },
          evidence: { type: 'string', description: 'primary-source URL + one line; required for incorrect/outdated' },
          fix_class: { type: 'string', enum: ['low_risk_autofix', 'judgment_call'] },
          old_string: { type: 'string', description: 'VERBATIM substring of the file to replace (low_risk_autofix only; else "")' },
          new_string: { type: 'string', description: 'replacement text (low_risk_autofix only; else "")' },
        },
      },
    },
  },
}

const prompt = (abs, rel) => `You are a skeptical expert in LLVM and compiler theory, reviewing ONE study note for CORRECTNESS as a careful reader.

Note file (read it with Read): ${abs}
(vault-relative path, use this as the note id: ${rel})

CONTEXT
- This is an LLM-drafted study-notes vault; it WILL contain some wrong or misleading claims. Your job is to find them.
- The vault tracks LLVM 22.1.x (release tag llvmorg-22.1.8). Judge version-specific claims against that.
- Notes in _moc/ are short index/summary "maps"; they have few substantive claims — check those, skip structural prose.

WHAT COUNTS AS A FINDING (technical substance only — IGNORE style/formatting/links):
- incorrect: a factually wrong statement about LLVM or compiler theory.
- misleading: technically defensible but likely to give a learner a wrong mental model.
- outdated: was true for older LLVM but not for 22.x (defaults, pass availability, API/class names, SelectionDAG vs GlobalISel, regalloc, etc.).
- imprecise: vague enough to be wrong in common cases.
- unverifiable: a specific claim you cannot confirm against a primary source.

VERIFY (this is a web-verified pass):
- For every suspected issue, CHECK IT against a PRIMARY source before reporting: llvm.org/docs (LangRef, pass docs, release notes) and the source at github.com/llvm/llvm-project (use the llvmorg-22.1.8 tag, not main). Use WebSearch/WebFetch (load them via ToolSearch if needed).
- Put the source URL (+ one line) in 'evidence'. 'incorrect' and 'outdated' findings MUST have a primary-source URL or be downgraded to severity low / type unverifiable.

BE CONSERVATIVE — false positives waste the user's time:
- If the note is correct, return { "notes_ok": true, "findings": [] }.
- Only report what you can substantiate or that is plainly wrong. Do not nitpick wording that is fine.

FIXES:
- fix_class = "low_risk_autofix" ONLY for an unambiguous factual correction (wrong pass/class name, wrong default, wrong year, wrong API) where you can give old_string as a VERBATIM substring copied exactly from the file (enough surrounding text to be unique) and a correct new_string. Anything needing rewording or judgment = "judgment_call" with old_string="" and new_string="".

Return ONLY the structured object.`

let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { throw new Error('args string was not valid JSON: ' + e.message) } }
const BASE = A && A.base
const NOTES = A && A.notes
if (!BASE || !Array.isArray(NOTES)) throw new Error('args must be { base, notes: [...] }; got: ' + typeof args)

phase('Review')
const raw = await parallel(
  NOTES.map((rel) => () => agent(prompt(`${BASE}/${rel}`, rel), { label: rel, phase: 'Review', schema: FINDINGS }))
)

// reattach note path by index (parallel preserves order); drop dead agents
const perNote = raw.map((r, i) => (r ? { note: NOTES[i], notes_ok: !!r.notes_ok, findings: r.findings || [] } : null)).filter(Boolean)
const withFindings = perNote.filter((r) => r.findings.length > 0)
const findings = withFindings.flatMap((r) => r.findings.map((f) => ({ ...f, note: r.note })))
const autofixes = findings.filter((f) => f.fix_class === 'low_risk_autofix' && f.old_string)

log(`Reviewed ${perNote.length}/${NOTES.length} notes; ${findings.length} findings (${autofixes.length} low-risk autofixable) across ${withFindings.length} notes`)

return {
  reviewed: perNote.length,
  total: NOTES.length,
  notesWithFindings: withFindings.length,
  counts: {
    high: findings.filter((f) => f.severity === 'high').length,
    medium: findings.filter((f) => f.severity === 'medium').length,
    low: findings.filter((f) => f.severity === 'low').length,
    autofix: autofixes.length,
  },
  findings,
}
