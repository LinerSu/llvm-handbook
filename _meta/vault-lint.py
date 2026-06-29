#!/usr/bin/env python3
"""vault-lint — mechanical consistency checks for the LLVM Obsidian vault.

This is the implementation of the `vault-lint` job specified in
_meta/chapter-bridge-pipeline.md (§Automation) and _meta/note-checklist.md
(§Automation). It enforces the mechanical half of the definition of done so the
vault stays consistent across many (often LLM-driven) sessions.

Single source of truth for axis values is _meta/controlled-vocabulary.md — this
script *reads* it, so humans and the linter never disagree.

Usage:  python3 _meta/vault-lint.py [--quiet]
Exit:   0 if no ERRORs, 1 otherwise. (WARNs never fail the build.)

Stdlib only — no pip install, so it runs on any surface (CLI, cloud, cowork).
"""
from __future__ import annotations
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACETS = ["theory", "concept", "algorithm", "data-structure", "implementation", "application"]
SKIP_DIRS = {".git", ".obsidian"}
# repo-level docs that are intentionally plain Markdown (not vault notes)
ROOT_DOC_IGNORE = {"README", "CLAUDE", "LICENSE"}
REQUIRED_KEYS = ["title", "facet", "stage", "ecosystem", "concepts", "status", "tags"]

errors: list[str] = []
warns: list[str] = []
def err(p, m): errors.append(f"{p}: {m}")
def warn(p, m): warns.append(f"{p}: {m}")

def rel(path): return os.path.relpath(path, ROOT)

def walk_md():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            if fn.endswith(".md"):
                yield os.path.join(dirpath, fn)

def split_frontmatter(text):
    """Return (frontmatter_dict_of_raw_strings, body). Shallow YAML — values kept raw."""
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    fm_block = text[3:end].strip("\n")
    body = text[end + 4:]
    fm = {}
    for line in fm_block.splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s?(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return fm, body

def fm_list(val):
    """Parse a frontmatter scalar that may be a [a, b] list or bare token."""
    if val is None:
        return []
    val = val.strip()
    if val.startswith("[") and val.endswith("]"):
        val = val[1:-1]
    return [t.strip().strip('"').strip("'") for t in val.split(",") if t.strip()]

# ---- load controlled vocabulary (single source of truth) -------------------
def load_vocab():
    path = os.path.join(ROOT, "_meta", "controlled-vocabulary.md")
    vocab = {"facet": set(), "stage": set(), "status": set(), "ecosystem": set(), "concepts": set()}
    if not os.path.isfile(path):
        err(rel(path), "controlled-vocabulary.md missing — cannot validate axis values")
        return vocab
    text = open(path, encoding="utf-8").read()
    # map a heading to the vocab key it defines
    head_to_key = {"facet": "facet", "stage": "stage", "status": "status",
                   "ecosystem": "ecosystem", "concepts": "concepts"}
    cur = None
    for line in text.splitlines():
        h = re.match(r"^##\s+(\w[\w-]*)", line)
        if h:
            word = h.group(1).lower()
            cur = head_to_key.get(word)
            continue
        if cur and not line.startswith(">"):  # skip blockquote (synonym notes)
            toks = re.findall(r"`([^`]+)`", line)
            for t in toks:
                if "→" not in t and " " not in t:  # skip "torch→pytorch", prose
                    vocab[cur].add(t)
    return vocab

VOCAB = load_vocab()

# ---- first pass: collect every note name for link resolution ----------------
note_names = set()      # basename without .md, e.g. "loop-info", "LLVM.MOC"
files = list(walk_md())
for path in files:
    note_names.add(os.path.basename(path)[:-3])

LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
FENCE_RE = re.compile(r"^\s*```")

# ---- per-file checks --------------------------------------------------------
facet_dirs_seen = set()
concepts_in_use: dict[str, int] = {}     # concept-key -> count of content notes using it
moc_concept_keys = set()                  # concept keys claimed by a concept-MOC

for path in files:
    r = rel(path)
    text = open(path, encoding="utf-8").read()
    fm, body = split_frontmatter(text)
    parts = r.split(os.sep)
    top = parts[0]
    base = os.path.basename(path)[:-3]
    is_about = base == "_about"
    is_moc = "_moc" in parts or base.endswith(".MOC")
    is_content = top in FACETS and not is_about

    # templates are scaffolding (placeholder links, <Title> stubs) — skip checks
    if top == "_templates":
        continue
    # repo-level plain-Markdown docs are not vault notes
    if len(parts) == 1 and base in ROOT_DOC_IGNORE:
        continue

    # --- frontmatter presence ---
    if fm is None:
        if base != "MEMORY":
            err(r, "missing YAML frontmatter")
        continue

    # --- content-note frontmatter contract ---
    if is_content:
        for k in REQUIRED_KEYS:
            if k not in fm or fm[k] == "":
                err(r, f"frontmatter missing required key '{k}'")
        # facet must equal folder
        if fm.get("facet") and fm["facet"] != top:
            err(r, f"facet '{fm['facet']}' != folder '{top}'")
        # finite-axis validation against vocab
        if fm.get("facet") and VOCAB["facet"] and fm["facet"] not in VOCAB["facet"]:
            err(r, f"facet '{fm['facet']}' not in controlled-vocabulary")
        if fm.get("stage") and VOCAB["stage"] and fm["stage"] not in VOCAB["stage"]:
            err(r, f"stage '{fm['stage']}' not in controlled-vocabulary")
        if fm.get("status") and VOCAB["status"] and fm["status"] not in VOCAB["status"]:
            err(r, f"status '{fm['status']}' not in controlled-vocabulary")
        for e in fm_list(fm.get("ecosystem")):
            if VOCAB["ecosystem"] and e not in VOCAB["ecosystem"]:
                warn(r, f"ecosystem '{e}' not in controlled-vocabulary (mint deliberately)")
        for c in fm_list(fm.get("concepts")):
            concepts_in_use[c] = concepts_in_use.get(c, 0) + 1
            if VOCAB["concepts"] and c not in VOCAB["concepts"]:
                warn(r, f"concepts key '{c}' not in controlled-vocabulary")

    # --- track concept-MOC coverage ---
    if is_moc and fm.get("type", "").strip() == "concept-moc":
        for c in fm_list(fm.get("concepts")):
            moc_concept_keys.add(c)

    if is_content:
        facet_dirs_seen.add(top)

    # --- wikilink resolution (whole file) ---
    for m in LINK_RE.finditer(text):
        raw = m.group(1).replace("\\|", "|")  # Obsidian escapes | as \| inside tables
        target = raw.split("|")[0].split("#")[0].strip().rstrip("\\")
        if not target:
            continue
        # allow path-style links by matching trailing basename
        tbase = target.split("/")[-1]
        if tbase not in note_names and target not in note_names:
            err(r, f"broken wikilink [[{target}]]")

    # --- code-fence parity ---
    fences = sum(1 for ln in text.splitlines() if FENCE_RE.match(ln))
    if fences % 2 != 0:
        err(r, f"unbalanced code fences (found {fences} ``` lines)")

    # --- mermaid label traps (lightweight) ---
    in_mermaid = False
    for i, ln in enumerate(text.splitlines(), 1):
        if FENCE_RE.match(ln):
            in_mermaid = ln.strip().lower().startswith("```mermaid") and not in_mermaid
            continue
        if in_mermaid:
            for lab in re.findall(r'"([^"]*)"', ln):
                if lab[:1] in "-+*":
                    warn(r, f"line {i}: mermaid label starts with '{lab[0]}' (markdown-list trap) — use ({lab[0]})")
                if "<" in lab or ">" in lab:
                    warn(r, f"line {i}: mermaid label contains '<'/'>' (treated as HTML)")

# ---- vault-level checks -----------------------------------------------------
# every facet folder that holds content should have an _about.md
for d in FACETS:
    folder = os.path.join(ROOT, d)
    if os.path.isdir(folder):
        has_md = any(f.endswith(".md") and f != "_about.md" for f in os.listdir(folder))
        if has_md and not os.path.isfile(os.path.join(folder, "_about.md")):
            warn(f"{d}/", "facet folder has notes but no _about.md (other facets have one)")

# MOC coverage advisory: concept keys with >=3 notes but no concept-MOC
COVERAGE_THRESHOLD = 3
for c, n in sorted(concepts_in_use.items()):
    if n >= COVERAGE_THRESHOLD and c not in moc_concept_keys:
        warn("_moc/concept/", f"concept key '{c}' has {n} notes but no concept-MOC (navigation gap)")

# stray temp files
for path in files:
    pass
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
    for fn in filenames:
        if fn.endswith(".tmp") or fn.endswith("~"):
            warn(rel(os.path.join(dirpath, fn)), "stray temp file — remove it")

# ---- report -----------------------------------------------------------------
quiet = "--quiet" in sys.argv
def section(title, items):
    print(f"\n{title} ({len(items)})")
    for it in items:
        print(f"  {it}")

print(f"vault-lint: {len(files)} notes scanned")
if errors:
    section("ERRORS — must fix", errors)
if warns and not quiet:
    section("WARN — triage", warns)
print(f"\n=> {len(errors)} error(s), {len(warns)} warning(s)")
sys.exit(1 if errors else 0)
