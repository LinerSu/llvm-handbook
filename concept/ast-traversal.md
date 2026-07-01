---
title: AST Traversal (RecursiveASTVisitor & AST Matchers)
facet: concept
stage: analysis
ecosystem: [clang]
concepts: [visitor-pattern, source-level-analysis]
src: "clang/include/clang/AST/RecursiveASTVisitor.h"
docs: "Clang — How to write RecursiveASTVisitor ↗ https://clang.llvm.org/docs/RAVFrontendAction.html"
prereqs: [clang-ast]
related: [visitor-pattern, clang-ast, safe-buffers, lifetime-safety]
tags: [kind/concept, status/verified]
status: verified
verified_on: 2026-07-01
---

# AST Traversal (RecursiveASTVisitor & AST Matchers)

> 🧭 **Concept** · `concept · analysis · clang` · Index [[LLVM.MOC]]
> **Prerequisites:** [[clang-ast]] · **Related:** [[visitor-pattern]], [[safe-buffers]], [[lifetime-safety]]

> [!abstract] Chapter map
> How you actually *consume* the [[clang-ast|Clang AST]]: not by chasing raw `Decl*`/`Stmt*` pointers, but through three standard tools — **`RecursiveASTVisitor`** (the CRTP workhorse), **`StmtVisitor`/`ConstStmtVisitor`** (single-node dispatch), and **AST Matchers** (a declarative pattern DSL). This is the AST-side counterpart of IR-side [[visitor-pattern|`InstVisitor`]]: same CRTP idea, but tuned for a deeper, richer tree.

---

## 1. Definition

> [!note] The idea
> The Clang AST is three cooperating hierarchies (`Decl` / `Stmt` — with `Expr` a `Stmt` — / `Type`), all owned by one `ASTContext` (see [[clang-ast]]). You almost never hand-walk it with raw pointers and `dyn_cast` ladders. Instead you pick one of **three traversal/matching mechanisms** that supply the walk and let you plug in *what to do at each node*. This is the [[visitor-pattern|Visitor pattern]] applied to a syntax tree.

## 2. Contrast with the IR visitor

Both the IR and AST visitors are **CRTP** (compile-time static dispatch, no vtable cost). The difference is the shape of what they walk: LLVM IR is a **flat, enumerable opcode set**, so [[visitor-pattern|`InstVisitor`]] is essentially one `switch` (from `Instruction.def`). The AST is a **deep, heterogeneous tree** across three hierarchies, so `RecursiveASTVisitor` must split the recursive *walk* from the *action* and add a class-hierarchy fallback.

> [!info]+ IR `InstVisitor` vs AST `RecursiveASTVisitor`
>
> | | IR [[visitor-pattern\|`InstVisitor`]] | AST `RecursiveASTVisitor` |
> |---|---|---|
> | Dispatch mechanism | **CRTP** static dispatch | **CRTP** static dispatch |
> | Structure walked | flat opcode set (`Instruction.def`) | deep tree: `Decl` / `Stmt` / `Type` |
> | Walk vs. act | fused — one `switch` per instruction | **separated**: `TraverseX` (walk) vs `VisitX` (act) |
> | Class-hierarchy fallback | `visitAdd → visitBinaryOperator → visitInstruction` (delegation) | `WalkUpFromX` climbs `X → parent → …` calling each `VisitX` |
> | You override | the `visitXXX` you care about | the `VisitX` you care about (e.g. `VisitCallExpr`) |
> | Default order | straight-line over containers | **pre-order** over the tree |

The three overridable levels of `RecursiveASTVisitor` are worth naming, because that is exactly what the split buys you:

- **`TraverseDecl` / `TraverseStmt` / `TraverseType`** — the *recursion*: descend into children. Override these only to change *how the tree is walked* (skip a subtree, reorder).
- **`WalkUpFromX`** — the *class-hierarchy climb*: for a concrete node, call `VisitX` for it and each of its base classes. This is the AST analogue of `InstVisitor`'s upward delegation.
- **`VisitX`** — the *hook you normally override* (e.g. `VisitCallExpr`, `VisitFunctionDecl`). Do your work, return `true` to keep going. The default is a no-op returning `true`.

## 3. The three tools

> [!info] Pick the mechanism to fit the job
>
> | Tool | Header | Dispatch | Typical use |
> |---|---|---|---|
> | **`RecursiveASTVisitor`** | `AST/RecursiveASTVisitor.h` | CRTP, `VisitX` hooks | walk the *whole* TU, act on chosen node kinds |
> | **`StmtVisitor` / `ConstStmtVisitor`** | `AST/StmtVisitor.h` | dispatch on one `Stmt`'s class | classify a *single* node (no built-in recursion) |
> | **AST Matchers** | `ASTMatchers/ASTMatchers.h` | declarative predicate DSL | *find* subtrees matching a shape |

- **`RecursiveASTVisitor`** — the workhorse. `template <typename Derived> class RecursiveASTVisitor`: CRTP, pre-order by default. Subclass it, override the `VisitX` you care about. It supplies the full recursive descent over `Decl`/`Stmt`/`Type`.
- **`StmtVisitor` / `ConstStmtVisitor`** — dispatches on a **single** statement's dynamic class to a `Visit...` method; it does *not* recurse on its own (you drive it node-by-node). [[lifetime-safety]]'s `FactsGenerator` is a `ConstStmtVisitor` — it lowers each CFG statement to lifetime facts.
- **AST Matchers** — a **declarative DSL**: you describe the shape you want (`callExpr(callee(functionDecl(hasName("malloc"))))`), register a callback, and a `MatchFinder` (internally an `ASTMatchFinder`) runs it over the AST. Node matchers (`callExpr`, `functionDecl`), narrowing matchers (`hasName`), and traversal matchers (`callee`, `has`, `hasDescendant`) compose. This is what **clang-tidy** checks are built from. [[safe-buffers|`-Wunsafe-buffer-usage`]] uses a *hand-written* fast variant (`FastMatcher`, `gadget.matches(...)` + `forEachDescendantEvaluatedStmt`) rather than the classic `MatchFinder`, tuned for running on every compile.

## 4. Two small examples

A `RecursiveASTVisitor` that flags every direct call — override **one** `VisitX`, let the base class do the walk:

> [!example]+ RecursiveASTVisitor subclass
> ```cpp
> #include "clang/AST/RecursiveASTVisitor.h"
> using namespace clang;
>
> class CallFinder : public RecursiveASTVisitor<CallFinder> {
> public:
>   bool VisitCallExpr(CallExpr *CE) {      // the hook; called pre-order
>     if (auto *FD = CE->getDirectCallee())
>       llvm::errs() << "call to " << FD->getName() << "\n";
>     return true;                          // false would halt traversal
>   }
> };
>
> // Drive it from an ASTConsumer/FrontendAction:
> CallFinder V;
> V.TraverseDecl(Context.getTranslationUnitDecl());   // walk the whole TU
> ```
> You override `VisitCallExpr` only; `RecursiveASTVisitor` provides `TraverseDecl`/`TraverseStmt`/… and the `WalkUpFrom*` climb for free.

The **same intent** as a matcher — declarative, no subclass, this is the clang-tidy style:

> [!example] The equivalent AST-matcher expression
> ```cpp
> // matches a call whose callee is a function named "malloc"
> callExpr(callee(functionDecl(hasName("malloc")))).bind("call")
> ```
> `callExpr` / `functionDecl` are **node** matchers, `hasName` **narrows**, `callee` is a **traversal** matcher into the child. Register it on a `MatchFinder` with a `MatchCallback` and it fires per match.

## 5. When to use which

> [!tip] Choosing
> - **`RecursiveASTVisitor`** — you need to visit *many* nodes across a whole TU and accumulate state (build a table, emit per-node output). The default full-tree walk is the point.
> - **AST Matchers** — you are *searching* for a specific structural pattern (an anti-pattern to lint, a call to rewrite). Declarative, composable, and the basis of clang-tidy; a fast hand-written variant powers [[safe-buffers]].
> - **`StmtVisitor` / `ConstStmtVisitor`** — you already hold *one* node and want to branch on its exact class, with no recursion — e.g. [[lifetime-safety]]'s `FactsGenerator` handling one CFG statement at a time.

## 6. Limitations

> [!warning] Traversal caveats
> - **Pre-order by default.** `RecursiveASTVisitor` is pre-order; post-order (and other reorderings) require overriding the `TraverseX` methods or opting into the visitor's post-order mode.
> - **Template instantiations are opt-in.** `shouldVisitTemplateInstantiations()` defaults to `false`, as does `shouldVisitImplicitCode()` — instantiated template bodies and compiler-synthesized code are *skipped* unless you say otherwise.
> - **Per-TU.** Like the [[clang-ast|AST]] itself, every traversal is one translation unit at a time; whole-program facts need cross-TU indexing, not a single walk.
> - **Verbose to write by hand.** A matcher expression is often a fraction of the code of the equivalent visitor — hence clang-tidy's preference for the DSL.

> [!summary] Remember
> Consuming the [[clang-ast|Clang AST]] means picking one of three tools: **`RecursiveASTVisitor`** (CRTP, override `VisitX`, walks the whole tree), **`StmtVisitor`/`ConstStmtVisitor`** (dispatch on one node's class), or **AST Matchers** (declarative `callExpr(callee(functionDecl(hasName(...))))` DSL, powering clang-tidy). It is the AST counterpart of IR's [[visitor-pattern|`InstVisitor`]] — same CRTP dispatch, but with the *walk* (`Traverse`) split from the *action* (`Visit`) because the tree is far richer than a flat opcode list.

> [!quote] Sources & confidence
> Tier-1, confirmed against the pinned Clang source ([[llvm-version]]):
> - [clang/include/clang/AST/RecursiveASTVisitor.h](https://github.com/llvm/llvm-project/blob/llvmorg-22.1.8/clang/include/clang/AST/RecursiveASTVisitor.h) — `template <typename Derived> class RecursiveASTVisitor` (CRTP, `getDerived()`); pre-order default; `TraverseDecl`/`TraverseStmt`/`TraverseType`; the `WalkUpFromX → VisitX` macro chain; `VisitX` default no-op; `shouldVisitTemplateInstantiations()` / `shouldVisitImplicitCode()` both default `false`.
> - [clang/include/clang/AST/StmtVisitor.h](https://github.com/llvm/llvm-project/blob/llvmorg-22.1.8/clang/include/clang/AST/StmtVisitor.h) — `StmtVisitor` / `ConstStmtVisitor` on `StmtVisitorBase` (dispatch on a `Stmt`'s class).
> - [clang/include/clang/ASTMatchers/ASTMatchers.h](https://github.com/llvm/llvm-project/blob/llvmorg-22.1.8/clang/include/clang/ASTMatchers/ASTMatchers.h) — the matcher DSL: `callExpr` (`VariadicDynCastAllOfMatcher<Stmt, CallExpr>`), `functionDecl`, `hasName`; `MatchFinder`/`MatchCallback` in [ASTMatchFinder.h](https://github.com/llvm/llvm-project/blob/llvmorg-22.1.8/clang/include/clang/ASTMatchers/ASTMatchFinder.h).
> - [Clang — How to write RecursiveASTVisitor based ASTFrontendActions](https://clang.llvm.org/docs/RAVFrontendAction.html) (the RAV tutorial).
> - Cross-links: [[lifetime-safety]]'s `FactsGenerator` is a `ConstStmtVisitor`; [[safe-buffers]] uses a `FastMatcher` variant, not the classic `MatchFinder` — both confirmed in those notes' tier-1 citations.
