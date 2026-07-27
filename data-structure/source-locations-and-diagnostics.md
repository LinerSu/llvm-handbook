---
title: Source Locations & Diagnostics (SourceManager, DiagnosticsEngine)
facet: data-structure
stage: frontend
ecosystem: [clang]
concepts: [source-level-analysis]
implements:
  - { ecosystem: clang, src: "clang/lib/Basic" }
src: "clang/lib/Basic"
docs: "Clang Internals Manual — The SourceLocation and SourceManager classes ↗ https://clang.llvm.org/docs/InternalsManual.html#the-sourcelocation-and-sourcemanager-classes"
prereqs: [clang-frontend-pipeline]
related: [clang-preprocessor, clang-ast, clang-frontend-pipeline, clang-static-analyzer]
tags: [kind/data-structure, status/verified]
status: verified
verified_on: 2026-07-20
---

# Source Locations & Diagnostics (SourceManager, DiagnosticsEngine)

> 🧭 **Data structure** · `data-structure · frontend · clang` · Index [[LLVM.MOC]]
> **Prerequisites:** [[clang-frontend-pipeline]] · **Related:** [[clang-preprocessor]], [[clang-ast]], [[clang-static-analyzer]]

> [!abstract] Chapter map
> The front end's **positioning backbone**: every `Token` and every [[clang-ast|AST]] node carries a `SourceLocation`, and the **`SourceManager`** turns that compact handle back into a file/line/column — crucially resolving the *spelling vs expansion* split that macros create. On top of it, the **`DiagnosticsEngine`** produces every error and warning, located precisely and optionally carrying a machine-applicable **`FixItHint`**. This is why a Clang diagnostic can underline the exact characters you wrote — and why the interview question *"is a security finding actionable?"* reduces to *"did a precise source location survive?"*

---

## 1. Definition

> [!note] Two data structures + one engine
> - **`SourceLocation`** — a tiny opaque handle (*"currently 32 bits wide"*, with *"one bit … for quick access to … whether the location is in a file or a macro expansion"*). It is **not** a `(file, line, col)` triple; it is an offset into the `SourceManager`'s tables, decoded on demand.
> - **`SourceManager`** — owns the loaded buffers and the include/expansion structure; it *"can be queried for information about SourceLocation objects, turning them into either spelling or expansion locations."*
> - **`DiagnosticsEngine`** — consumes locations to emit located messages; *"tied to one translation unit and one SourceManager."*

## 2. The representation — why locations are compact

Keeping `SourceLocation` at 32 bits matters because there is one on *every* token and *every* AST node; a fat location type would blow up memory on large translation units. So the type is a bare offset, and all the structure (which file, which line, which macro expansion) lives once in the `SourceManager`, keyed by a `FileID`. Decoding is lazy: you only pay to compute line/column when you actually print a diagnostic.

## 3. The key operation — spelling vs expansion

The one idea this note exists for. A token produced by a macro has **two** meaningful positions, and the `SourceManager` header states the contract exactly:

> [!info] SourceManager, verbatim (pinned Clang [[llvm-version]])
> *"Spelling locations represent where the bytes corresponding to a token came from and expansion locations represent where the location is in the user's view. In the case of a macro expansion … the spelling location indicates where the expanded token came from and the expansion location specifies where it was expanded."*

So `getSpellingLoc()` points *inside the `#define`* (where the characters live), while `getExpansionLoc()` points at the *call site* (what the user sees). This is the resolution of the ambiguity [[clang-preprocessor]] creates: the preprocessor flattens macros into the token stream, and the `SourceManager` is what lets a diagnostic still say *"expanded from macro …"* and point at both places.

Note that `-ast-dump` will **not** show you this split: `TextNodeDumper` maps every location through `getSpellingLoc` before printing, so a macro-expanded node dumps with *spelling* locations at **both** ends. For `#define SQ(x) ((x)*(x))` used on the next line, the expanded `BinaryOperator` dumps as `<col:16, col:22>` — both inside the macro definition. The expansion location surfaces in **diagnostics** ("expanded from macro …"), not in the AST dump.

## 4. In Clang — the DiagnosticsEngine

`DiagnosticsEngine` (`clang/include/clang/Basic/Diagnostic.h`) is where the front end's errors are born. It:

- classifies each diagnostic by an `enum Level` (Ignored / Note / **Remark** / Warning / Error / Fatal — six levels; `Remark` is what `-Rpass=` uses),
- *"massages the diagnostics (e.g. handling things like 'report warnings as errors')"* — this is where `-Werror` lives,
- *"passes them off to the `DiagnosticConsumer`"* (the text terminal printer, or an IDE, or `-serialize-diagnostics`),
- and can attach a **`FixItHint`**: a source *range + replacement text* the compiler is confident enough to apply automatically (clang-tidy and IDEs consume these to auto-fix).

## 5. Worked example — a located warning with fix-its

> [!example]+ `clang -fsyntax-only fixit.c` on `if (x = 5)`
> ```text
> fixit.c:1:22: warning: using the result of an assignment as a condition without parentheses [-Wparentheses]
>     1 | int h(int x) { if (x = 5) return 1; return 0; }
>       |                    ~~^~~
> fixit.c:1:22: note: place parentheses around the assignment to silence this warning
>     1 | int h(int x) { if (x = 5) return 1; return 0; }
>       |                      ^
>       |                    (    )
> fixit.c:1:22: note: use '==' to turn this assignment into an equality comparison
>     1 | int h(int x) { if (x = 5) return 1; return 0; }
>       |                      ^
>       |                      ==
> ```
> Everything visible here is the machinery of this note: the precise `1:22` comes from the `SourceManager`; the `~~^~~` caret range is the diagnostic's `SourceRange`; the inserted `(    )` and the `==` suggestion are **`FixItHint`s**. The message-vs-note structure and the `[-Wparentheses]` group are the `DiagnosticsEngine`'s classification.

## 6. Where it's used — the actionable/unusable line

Every source-level tool leans on this: [[clang-static-analyzer|the Static Analyzer]], clang-tidy, and Sema's own warnings all report *at source* because they run before lowering and hold real `SourceLocation`s. Lowering to IR keeps only what **debug info** (`!dbg` / `DILocation`) carries, and optimization can drop or merge it — so an IR-level finding is only as actionable as the location that survives. That is the concrete reason type- and location-directed security checks favor the AST (see [[source-level-analysis]]).

## 7. Limitations

> [!warning] What the location model costs
> - **Locations become a stack under macros.** Deeply nested macro expansions produce long spelling/expansion chains; untangling *"expanded from"* notes is the price of the flattening in [[clang-preprocessor]].
> - **32 bits is a budget.** Extremely large translation units (or many loaded modules) press against the offset space; the type is kept small precisely because it is everywhere.
> - **A location is only as good as what preserves it.** Across AST → IR the fidelity depends on debug-info propagation, not on `SourceLocation` — a different, lossier mechanism.

> [!summary] The one thing to remember
> `SourceLocation` is a **32-bit handle**, not a triple; the **`SourceManager`** decodes it and, for macro tokens, resolves **spelling** (inside the `#define`) vs **expansion** (the call site). The **`DiagnosticsEngine`** rides on those locations to emit every error/warning — with `-Werror` handling and machine-applicable `FixItHint`s. Precise, surviving locations are what make a diagnostic (or a security finding) actionable.

> [!quote] Sources & confidence
> **Verified 2026-07-20** — every falsifiable claim in this note was enumerated and checked against the pinned Clang source ([[llvm-version]], `llvmorg-22.1.8`) by the `note-correctness-review` pass; refuted claims were corrected (batch error rate 8.6%, 23/269). GitHub links track `main`; the checked revision is the pinned tag.
> - [clang/include/clang/Basic/SourceManager.h](https://github.com/llvm/llvm-project/blob/main/clang/include/clang/Basic/SourceManager.h) — spelling vs expansion contract; `getSpellingLoc` / `getExpansionLoc`.
> - [clang/include/clang/Basic/SourceLocation.h](https://github.com/llvm/llvm-project/blob/main/clang/include/clang/Basic/SourceLocation.h) — *"currently 32 bits wide";* file-vs-macro bit.
> - [clang/include/clang/Basic/Diagnostic.h](https://github.com/llvm/llvm-project/blob/main/clang/include/clang/Basic/Diagnostic.h) — `DiagnosticsEngine` *"tied to one translation unit and one SourceManager";* `enum Level`; `FixItHint`.
> - Example output produced locally with **Apple clang 17** (Apple's own versioning — *not* an upstream LLVM release number, and not the pinned tag; cosmetics track the clang version — see [[llvm-version]]). The model is version-stable.
> - [Clang Internals Manual — SourceLocation and SourceManager](https://clang.llvm.org/docs/InternalsManual.html#the-sourcelocation-and-sourcemanager-classes) — primary doc.
