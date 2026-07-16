---
title: Dependence Testing (GCD, SIV, Banerjee)
facet: algorithm
stage: analysis
ecosystem: [general]
concepts: [dependence-analysis, loop-optimization]
book: "Dragon Book (Aho/Lam/Sethi/Ullman, 2e) §11.6"
docs: "doxygen — DependenceInfo ↗ https://llvm.org/doxygen/classllvm_1_1DependenceInfo.html"
prereqs: [loop-info]
related: [dependence-analysis, scalar-evolution, loop-transformations, polyhedral-model]
tags: [kind/algorithm, status/verified, version-sensitive]
status: verified
verified_on: 2026-07-16
---

# Dependence Testing (GCD, SIV, Banerjee)

> 🧭 **Algorithm** · `algorithm · analysis · general` · Index [[LLVM.MOC]] · see also [[dragon-book-ch11.MOC|Dragon Ch.11]]
> **Powers:** [[dependence-analysis|DependenceAnalysis]] — and through it every loop transform whose legality is "can I reorder these two accesses?"
> **Prerequisites:** [[loop-info]]

> [!abstract] Chapter map
> `A[i]` and `A[2*j + 1]` — can they ever be the same element? That's an **integer linear equation with bounds**, and the classic answer is a cascade of cheap tests that try to prove *no solution exists*. LLVM implements the Goff–Kennedy–Tseng cascade and says in its own header that it's **incomplete**. The two things worth knowing: SCEV's loop normalization visibly *simplifies the textbook equations*, and the shipped default **assumes a precondition it doesn't check**.

---

## 1. The problem

> [!note] Definition
> Two array accesses in a loop nest are **dependent** if some pair of iterations touches the same memory. For affine subscripts, "is there a dependence?" is: does the equation $a_1 i_1 + \cdots + a_n i_n + c_1 = b_1 j_1 + \cdots + b_n j_n + c_2$ have an **integer** solution **inside the loop bounds**?

Two properties make this tractable and useful:
- Answering **"no"** is what unlocks transformation ([[loop-transformations|vectorization, interchange, parallelization]]). Answering "yes, maybe" costs nothing but blocks the transform. So every test is a **disproof attempt**, and "I don't know" is always a safe answer.
- The equation is Diophantine (integer-valued) *and* bounded, so two independent classic attacks apply: **divisibility** (GCD) and **range** (Banerjee).

> [!info] The classification — by counting loops, not by algebra
> The cascade dispatches on how many distinct loop indices appear in the subscript pair:
>
> | Kind | Meaning | Test |
> |---|---|---|
> | **ZIV** | Zero Index Variables — both subscripts loop-invariant | compare the two values |
> | **SIV** | Single Index Variable | strong / weak-crossing / weak-zero / exact SIV |
> | **RDIV** | Restricted Double Index Variable | exact RDIV, symbolic RDIV |
> | **MIV** | Multiple Index Variables | **GCD and Banerjee — that's all** |
>
> The precision gradient is the point: ZIV is a comparison, SIV can give an exact **distance and direction**, and MIV mostly just says yes/no. Everything upstream of MIV exists to *avoid* MIV.

## 2. The GCD test

> [!info] The classic
> $\gcd(a_1, \ldots, a_n, b_1, \ldots, b_n)$ must divide $c_2 - c_1$. If it doesn't, **no integer solution exists**, anywhere — no bounds reasoning needed. Cheap, sound, and completely ignores loop limits (which is also why it's weak: it disproves less often than it could).

> [!tip] What LLVM actually computes — and why it isn't quite a *greatest* common divisor
> There are no "coefficients" to collect: LLVM walks the [[scalar-evolution|SCEV]] `AddRec` chain, taking each **step recurrence** as a coefficient and each **start** as the constant. If any coefficient isn't a constant, the test gives up outright.
>
> And when loop-invariant *symbols* are in play, the source concedes the test changes character:
> > *"It occurs to me that the presence of loop-invariant variables changes the nature of the test from "greatest common divisor" to "a common divisor"."*
>
> That's a real weakening, admitted in-tree: with symbols like `[10*i + 5*N*j + 15*M + 6]`, LLVM can only use the constant parts, so it computes *a* common divisor, not *the* greatest one — and a smaller divisor disproves less.

> [!note] It also refines directions
> Beyond the classic disproof, LLVM re-runs the GCD per loop level to kill the `=` direction — the Wolfe extension. Given `[3*i + 2*j]` vs `[i' + 2*j' - 1]` the plain GCD is 1 and proves nothing, but *assuming* `i = i'` yields an infeasible subscript, so the `=` direction at level `i` is impossible and the vector becomes `[<>, *]`. This path only ever **refines**; it never disproves.

## 3. Banerjee — the range attack

> [!info] The Extreme Value Test
> Where GCD asks "is a solution divisible?", Banerjee asks **"can the difference even reach zero within the loop bounds?"** Compute the minimum and maximum values the expression can take over the iteration space; if $0$ falls outside $[\text{LB}, \text{UB}]$, there is no dependence. The bounds are built from **positive and negative parts**, $X^+ = \max(X, 0)$ and $X^- = \min(X, 0)$, which LLVM implements exactly as `getSMaxExpr` / `getSMinExpr` against zero.

> [!tip] The delta you can *see* — SCEV simplifies the textbook equation
> This is the best exhibit in the file, because LLVM prints both forms side by side. Wolfe's published bound is:
> $$LB^<_k = (A^-_k - B_k)^- (U_k - L_k - N_k) + (A_k - B_k)L_k - B_k N_k$$
> and LLVM's own comment then says:
> > *"Since all loops are normalized by the SCEV package, $N_k = 1$ and $L_k = 0$, allowing us to simplify the equation to* $LB^<_k = (A^-_k - B_k)^- (U_k - 1) - B_k$*."*
>
> The lower bound and the stride **vanish from the algebra** — not because anyone improved Banerjee, but because an upstream analysis already canonicalized every loop to start at 0 and step by 1. This is the cleanest example in the vault of a *neighbouring component* changing what an algorithm has to do. The same simplification is documented on all four bound helpers (`ALL`, `EQ`, `LT`, `GT`).

> [!warning] And it's capped
> Exploring direction vectors is $O(3^n)$ in the number of common loop levels. LLVM bails past **7** levels and marks every direction `*` — safe, and useless. Textbook Banerjee has no such cap because it isn't paying a compile-time budget.

## 4. What is *not* there

> [!warning] The Omega test is absent — and not deferred
> The classic exact method (Fourier–Motzkin / integer programming, Pugh 1991) is **not implemented**. Verified: zero case-insensitive matches for "omega" in `DependenceAnalysis.cpp` or its header. It is not a TODO, not future work, not mentioned at all — `testMIV` is two lines and calls exactly `gcdMIVtest` and `banerjeeMIVtest`. Don't say LLVM "plans to add" it; the source supports only "LLVM doesn't have it."

> [!danger] The shipped default assumes a precondition it does not check
> Every SIV/MIV test assumes subscripts are **monotonic**. The source is explicit about both the requirement and the consequence of violating it:
> > *"Since dependence tests (SIV, MIV, etc.) assume that subscript expressions are (multivariate) monotonic, we need to verify this property before applying those tests. **Violating this assumption may cause them to produce incorrect results.**"*
>
> And the checker is **off by default**:
> ```cpp
> // TODO: This flag is disabled by default because it is still under development.
> // Enable it or delete this flag when the feature is ready.
> static cl::opt<bool> EnableMonotonicityCheck(
>     "da-enable-monotonicity-check", cl::init(false), cl::Hidden, ...);
> ```
> So as shipped, `DependenceAnalysis` applies tests whose stated precondition goes unverified. Read that as *"this analysis is honest about being under construction"* — its header opens by calling itself an **"(incomplete) implementation"** and closes with *"this is work in progress and the interface is subject to change."* Delinearization carries a comparable caveat: recovered subscripts can't generally be proven in-range at compile time, so it's guarded by a validity check that some C usage can defeat.

## 5. The delta

> [!summary] The one thing to remember
> | Textbook | LLVM ships |
> |---|---|
> | Goff–Kennedy–Tseng cascade | the same cascade, self-described **"(incomplete)"** |
> | GCD over integer coefficients | GCD over **SCEV AddRec steps**; degrades to *"a common divisor"* with symbols; bails on any non-constant coefficient |
> | Banerjee with $L_k$, $U_k$, $N_k$ | the same inequalities **simplified to $L_k=0$, $N_k=1$** because SCEV normalized the loops; capped at 7 levels |
> | Omega test (exact) | **absent, and unmentioned** |
> | Tests assume monotonic subscripts | assumption **unverified by default** |
>
> The through-line: this analysis is a **cascade of cheap disproofs**, and its real interface with LLVM is [[scalar-evolution|SCEV]] — which supplies the coefficients, the bounds, *and*, by normalizing loops, quietly deletes two terms from Banerjee's published equation.

> [!tip] Isolating one test
> `-da-enable-dependence-test=<strong-siv|weak-crossing-siv|exact-siv|weak-zero-siv|exact-rdiv|symbolic-rdiv|gcd-miv|banerjee-miv>` runs exactly **one** test and disables the rest — it exists for regression tests, but it's the best learning tool here: run `opt -passes='print<da>'` twice and watch precisely which classic algorithm made the call.

> [!quote] Sources & confidence
> - **Source (tier 1):** Quoted text was verified against the **tag** in [[llvm-version]]. The links below track `main` for navigation — this vault deliberately does not hardcode release numbers in content notes — so `main` may since have drifted from what is quoted here; re-verify against the tag, not `main`. [`llvm/lib/Analysis/DependenceAnalysis.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Analysis/DependenceAnalysis.cpp) (file header, `classifyPair`, `testZIV`/`testSIV`/`testRDIV`/`testMIV`, `gcdMIVtest`, `banerjeeMIVtest` and its four bound helpers, `EnableMonotonicityCheck`, `MIVMaxLevelThreshold`) · [`llvm/include/llvm/Analysis/DependenceAnalysis.h`](https://github.com/llvm/llvm-project/blob/main/llvm/include/llvm/Analysis/DependenceAnalysis.h). All quotes above are verbatim from these files.
> - Goff, Kennedy & Tseng, *Practical Dependence Testing*, PLDI 1991 — **named in LLVM's file header** as the approach implemented.
> - Wolfe, *Optimizing Supercompilers for Supercomputers*, MIT Press 1989 — §2.5.2 p.25 (the Banerjee inequalities LLVM simplifies) and Program 2.1 p.29 (Kirch's extended-Euclid, used by the exact tests); Wolfe, *High Performance Compilers for Parallel Computing*, p.235 (the GCD direction refinement). All three cited **at the corresponding test sites** in-tree.
> - Banerjee, *Dependence Analysis for Supercomputing*, Kluwer 1988 — Algorithm 6.2.1, cited at `exactSIVtest`, which LLVM notes it **modified**: the original only tested whether Dst depends on Src; LLVM's returns all dependences in both directions.
> - Pugh, *The Omega Test*, Supercomputing 1991 — for contrast only; **not implemented** (§4).
>
> > [!danger] Unverified
> > Citations are confirmed as **LLVM's claims** (the papers are named at those exact lines); whether each implementation faithfully matches its cited paper's variant has not been checked against the papers themselves. The absence of the Omega test is verified for `DependenceAnalysis.{cpp,h}` specifically, not proven for the whole tree by mechanical search.
