export const meta = {
  name: 'note-correctness-review',
  description: 'Enumerate every falsifiable claim in a note and check EACH against LLVM source at the pinned tag; report verdicts + low-risk fixes + an error rate',
  whenToUse: 'Correctness audit of the LLVM vault (the "verify pass" from _meta/note-checklist + chapter-bridge-pipeline). This pass defines what `status: verified` means. args: { base: "<abs repo root>", notes: ["<relpath>", ...], tag?: "llvmorg-22.1.8" }',
  phases: [{ title: 'Verify', detail: 'one claim-enumerating source-verifier per note' }],
}

// ---- structured output every reviewer must return ----
// Counts are REQUIRED: they give the caller a denominator, hence an error rate,
// hence a basis to choose between patching and downgrading a cohort.
// A pass that reports only findings is unfalsifiable — silence looks like success.
const FINDINGS = {
  type: 'object',
  additionalProperties: false,
  required: ['claims_examined', 'confirmed', 'findings'],
  properties: {
    claims_examined: {
      type: 'integer',
      description: 'Total falsifiable claims extracted from the note (the denominator). A claim naming no LLVM entity is not falsifiable and is not counted.',
    },
    confirmed: {
      type: 'integer',
      description: 'Claims checked against source at the tag and supported by it.',
    },
    findings: {
      type: 'array',
      description: 'One entry per REFUTED or UNVERIFIABLE claim. Confirmed claims are counted, not listed.',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['verdict', 'severity', 'type', 'quote', 'problem', 'correction', 'evidence', 'fix_class', 'old_string', 'new_string'],
        properties: {
          verdict: {
            type: 'string',
            enum: ['REFUTED', 'UNVERIFIABLE'],
            description: 'REFUTED = source contradicts it. UNVERIFIABLE = could not reach source, or judgment call. Never guess; when unsure, UNVERIFIABLE.',
          },
          severity: {
            type: 'string',
            enum: ['high', 'medium', 'low'],
            description: 'Rate by READER IMPACT, not by how wrong it is. Wrong default that sends a learner to the wrong pass = high. Acronym typo = low.',
          },
          type: { type: 'string', enum: ['incorrect', 'misleading', 'outdated', 'imprecise', 'unverifiable'] },
          quote: { type: 'string', description: 'exact text from the note that is problematic' },
          problem: { type: 'string', description: 'what is wrong and why a learner would be misled' },
          correction: { type: 'string', description: 'what it should say' },
          evidence: {
            type: 'string',
            description: 'REQUIRED for REFUTED: source path + line + verbatim quote, AT THE PINNED TAG. For UNVERIFIABLE: state exactly what would settle it.',
          },
          fix_class: { type: 'string', enum: ['low_risk_autofix', 'judgment_call'] },
          old_string: { type: 'string', description: 'VERBATIM substring of the file to replace (low_risk_autofix only; else "")' },
          new_string: { type: 'string', description: 'replacement text (low_risk_autofix only; else "")' },
        },
      },
    },
  },
}

const prompt = (abs, rel, tag) => `You are verifying ONE study note against LLVM source. Not proofreading it — verifying it.

Note file (read it with Read): ${abs}
(vault-relative path, use this as the note id: ${rel})

## Why this pass exists — read this, it is the whole design

An earlier version of this pass told reviewers: "for every SUSPECTED issue, check it against a primary source." That pass FAILED, and understanding how is the point of the rewrite.

\`data-structure/dominator-tree.md\` claimed LLVM builds dominator trees with "the near-linear **Lengauer-Tarjan** algorithm". Nothing about that sentence looks suspicious — it is what most papers and blogs say. So nobody suspected it, so nobody checked, so it passed as verified. It is **false**: \`GenericDomTreeConstruction.h\` says it implements **Semi-NCA** (O(n^2) worst case) and explicitly contrasts it *against* "Simple Lengauer-Tarjan". The old pass literally edited that file and left the error in.

Two lessons, both load-bearing:

1. **Verification triggered by suspicion is not verification.** It is a plausibility filter. It catches only claims that *look* wrong — the exact complement of the dangerous set. So: **enumerate every falsifiable claim and check each one, including the ones you are sure about.** Especially those.
2. **Web search cannot catch an error the web shares.** Measured: in the 2026-07-16 audit, 10/10 refuted claims were ones search would have CONFIRMED. Search is not evidence here.

Worse, LLVM's own comments lie. \`GVN.cpp\` says \`// Top-down walk of the dominator tree.\` directly above \`ReversePostOrderTraversal<Function *> RPOT(&F);\`. A vault note copied that comment and was wrong for it. **The code is the source of truth; the comment beside it is not.**

## Method — non-negotiable

- **Verify ONLY against LLVM source at the pinned tag \`${tag}\`.** Fetch:
  \`https://raw.githubusercontent.com/llvm/llvm-project/${tag}/llvm/...\`
  via WebFetch or \`gh api\` (load them with ToolSearch if needed).
- **NOT \`main\`** — it drifts from the tag the vault documents.
- **NOT blogs, NOT doxygen prose, NOT LLVM docs prose.** Per \`_meta/source-hierarchy.md\`, docs are tier-3 and "can lag the code"; blogs are tier-4, "never the sole citation". **LangRef IS tier-1** for IR semantics — fetch it at the tag (\`llvm/docs/LangRef.rst\`).
- **NOT your memory.** LLVM ${tag} may postdate your training. If you "know" the answer without looking, that is precisely the Lengauer-Tarjan failure. Go read the file.
- Cannot reach the source for a claim? The verdict is **UNVERIFIABLE**. Never CONFIRMED.

## The standing check: \`cl::opt\` defaults

For ANY claim of the form "pass X uses/enables Y" or "Y is on/off by default" — **find the \`cl::init(...)\` and read it.** This one check refuted two claims in the last audit:
- \`memory-ssa.md\` said MemorySSA powers GVN → \`GVNEnableMemorySSA("enable-gvn-memoryssa", cl::init(false))\`. Off by default.
- \`early-cse.md\` said MemorySSA handles memory ops → a generation counter does the work; MemorySSA only adds precision.

The pattern is always the same: **the feature exists, so the claim reads true — but it is off by default, or it is an enhancement rather than the mechanism.** Existence is not the claim. Check the default.

## Traps that produce FALSE findings — a wrong REFUTED is as bad as the original error

Before writing REFUTED, rule these out, and state which config you assumed:

1. **\`cl::opt\` flags** — a path may be live/dead only under a non-default config.
2. **Virtual dispatch** (\`InlineAdvisor\`, \`InstVisitor\`, the AA interface) — you cannot see the real callee from the call site.
3. **Templates** — one body serves several instantiations (forward/reverse domtree; call/ref edges).
4. **Level-of-description** — the note may describe SEMANTICS ("an edge A->B means B initializes A") while the code shows a different PROCEDURE ("built from use-lists"). **Not a contradiction. This is the most common false positive.**
5. **Register** — a note in classic-theory register (Dragon Book examples, textbook conditions) is not refuted by LLVM doing something stronger. Refute only if it *names* an LLVM entity.
6. **Target overrides** — generic \`TargetLoweringBase\` defaults differ per target.
7. **Incomplete != contradicted** — a list missing an item is imprecise; REFUTED only if presented as exhaustive AND the omission is load-bearing.
8. **Out-of-tree** — the vault knowingly documents things outside \`llvm/\` (e.g. DSA in \`poolalloc\`). Absence from upstream may be the note's own claim.

Discarding your own draft refutation after checking a trap is a **success**, not wasted work.

## What to do

1. Read the note. Its \`src:\` / \`implements:\` frontmatter names what it claims to describe.
2. **Enumerate every falsifiable claim** — one naming an LLVM pass, class, file, function, flag, default, algorithm, complexity, or version. Skip general compiler theory naming no LLVM entity: not falsifiable, not counted.
3. For EACH — including ones you believe — fetch the source at the tag and decide CONFIRMED / REFUTED / UNVERIFIABLE.
4. Set \`claims_examined\` to the total and \`confirmed\` to the count that checked out. List only REFUTED/UNVERIFIABLE in \`findings\`. **The counts are as much the deliverable as the findings** — they are how the caller measures whether \`status: verified\` means anything.
5. Rate \`severity\` by reader impact.

FIXES:
- \`fix_class = "low_risk_autofix"\` ONLY for an unambiguous factual correction where \`old_string\` is a VERBATIM substring copied exactly from the file (enough surrounding text to be unique) and \`new_string\` is correct. Anything needing rewording or judgment = \`"judgment_call"\` with both fields "".

Return ONLY the structured object.`

let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { throw new Error('args string was not valid JSON: ' + e.message) } }
const BASE = A && A.base
const NOTES = A && A.notes
const TAG = (A && A.tag) || 'llvmorg-22.1.8'
if (!BASE || !Array.isArray(NOTES)) throw new Error('args must be { base, notes: [...] }; got: ' + typeof args)

phase('Verify')
const raw = await parallel(
  NOTES.map((rel) => () => agent(prompt(`${BASE}/${rel}`, rel, TAG), { label: rel, phase: 'Verify', schema: FINDINGS }))
)

// reattach note path by index (parallel preserves order); drop dead agents
const perNote = raw
  .map((r, i) => (r ? { note: NOTES[i], claims_examined: r.claims_examined || 0, confirmed: r.confirmed || 0, findings: r.findings || [] } : null))
  .filter(Boolean)

const findings = perNote.flatMap((r) => r.findings.map((f) => ({ ...f, note: r.note })))
const refuted = findings.filter((f) => f.verdict === 'REFUTED')
const unverifiable = findings.filter((f) => f.verdict === 'UNVERIFIABLE')
const autofixes = refuted.filter((f) => f.fix_class === 'low_risk_autofix' && f.old_string)

const examined = perNote.reduce((a, r) => a + r.claims_examined, 0)
const clean = perNote.filter((r) => r.findings.every((f) => f.verdict !== 'REFUTED'))
const rate = examined ? ((refuted.length / examined) * 100).toFixed(1) : '0.0'

log(`Verified ${perNote.length}/${NOTES.length} notes against ${TAG}: ${examined} claims examined, ${refuted.length} refuted (${rate}%), ${unverifiable.length} unverifiable. ${clean.length}/${perNote.length} notes clean; ${autofixes.length} low-risk autofixable.`)

return {
  tag: TAG,
  reviewed: perNote.length,
  total: NOTES.length,
  // The error rate is the headline: it is the evidence for whether `status: verified`
  // means anything across a cohort. A per-note pass with no rate cannot answer that.
  claimsExamined: examined,
  refutedCount: refuted.length,
  refutedRatePct: Number(rate),
  unverifiableCount: unverifiable.length,
  // Only notes with zero REFUTED claims may be promoted to `status: verified` with
  // today's date. Everything else stays `unverified` until its findings are applied.
  notesClean: clean.map((r) => r.note),
  notesWithRefutations: [...new Set(refuted.map((f) => f.note))],
  counts: {
    high: refuted.filter((f) => f.severity === 'high').length,
    medium: refuted.filter((f) => f.severity === 'medium').length,
    low: refuted.filter((f) => f.severity === 'low').length,
    autofix: autofixes.length,
  },
  findings,
}
