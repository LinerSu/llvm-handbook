---
title: Loop Transformations
facet: concept
stage: optimization
ecosystem: [llvm]
concepts: [loop-optimization]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/Scalar/ (LICM, LoopUnroll, LoopDistribute, LoopFuse)" }
  - { ecosystem: llvm, src: "llvm/lib/Transforms/Vectorize/" }
docs: "Passes ↗ https://llvm.org/docs/Passes.html"
prereqs: [loop-info, ssa-form]
related: [pointer-alias-analysis, memory-ssa, loop-invariant-code-motion]
tags: [kind/transform, status/verified]
status: verified
verified_on: 2026-06-28
---

# Loop Transformations

> 🧭 **Concept** · `concept · optimization · llvm` · Index [[LLVM.MOC]]
> **Prerequisites:** [[loop-info]], [[ssa-form]] · **Enabled by:** [[pointer-alias-analysis]], [[memory-ssa]] · **Hoisting:** [[loop-invariant-code-motion]] · Chapter: [[Loop-Optimization.MOC]]

> [!abstract] Chapter map
> The transforms that rewrite loops once they're in canonical form ([[loop-info]]): **unrolling, peeling/splitting, LICM, vectorization, fission, fusion** — each a *legality test* (dependence analysis) plus a *rewrite*.

> [!info] The golden rule (carried from [[loop-info]])
> A loop transform is legal **iff** it preserves the original data dependences. Every transform below is really a dependence-analysis legality check plus a mechanical rewrite.

---

### 4. Loop transformation

> [!info] What "transform" means here
> Rewrite loops into a cheaper-to-execute shape while **preserving observable behavior** (correctness). Two payoffs:
> - **High level (code):** reduce to simpler expressions — e.g. $\sum_{i=10}^{20} i = \dfrac{(10+20)\cdot 11}{2}$ closes the loop entirely.
> - **Low level (hardware):** improve locality / reduce cache misses.
>
> > [!warning] The golden rule
> > A loop transform is legal **iff** it preserves the original data dependences. Every transform below is really a *legality test* (dependence analysis) plus a *rewrite*.

---

### 5. Unrolling (unwinding)

> [!note] Definition
> Replicate the loop body $K$ times (a user-controllable factor):
> - repeat the body $K$ times per new iteration;
> - if iterations remain, keep a loop but reduce its trip count by $K$.
> - If **fully** unrolled, the loop disappears entirely.
>
> LLVM pass: `-loop-unroll` (and runtime/partial variants).

> [!example]+ Full unroll by 4
> **Before:**
> ```c
> for (i = 0; i < 4; i++) { c[i] = a[i] + b[i]; }
> ```
> **After (loop eliminated):**
> ```c
> c[0] = a[0] + b[0];
> c[1] = a[1] + b[1];
> c[2] = a[2] + b[2];
> c[3] = a[3] + b[3];
> ```

> [!example]+ Partial unroll by 5 (trip count not statically divisible)
> **Before:**
> ```c
> for (int x = 0; x < 100; x++) { remove(x); }
> ```
> **After:**
> ```c
> for (int x = 0; x < 100; x += 5) {
>   remove(x);     remove(x + 1); remove(x + 2);
>   remove(x + 3); remove(x + 4);
> }
> ```

> [!info] Why unroll?
> - **Verification (e.g. BMC):** bounded model checking needs finite, unrolled loops since unbounded loops can't be bit-blasted directly.
> - **Performance:** fewer branches/increments; fixed iteration counts expose constant folding and enable *other* passes downstream.

> [!example]- Algorithm sketch — `UnrollLoop(L, K)` (click to expand)
> ```text
>   # ensure L is in LoopSimplify form (preheader/header/latch) and LCSSA
>   Blocks = getLoopBlocksInOrder(L)      # header first, latch last
>   Header = L.header ; Latch = L.latch
>   VMap = array of maps size K           # VMap[iter][origValue] = clone
>   # iteration 0 is the original; clones are 1..K-1
>   for i in range(1, K):
>     for B in Blocks:
>       B_clone = cloneBasicBlock(B); add to function
>       for inst in B:
>         inst_clone = cloneInstruction(inst); put into B_clone
>         VMap[i][inst] = inst_clone
>     for B in Blocks:                    # remap operands to same-iter clones
>       for inst in cloneOf(B, i): remapOperands(inst, VMap[i])
>   # chain bodies: latch_i -> header_{i+1}; last latch -> original header
>   for i in range(0, K-1):
>     latch_i    = (i == 0) ? Latch : cloneOf(Latch, i)
>     header_ip1 = cloneOf(Header, i+1)
>     redirectBackedge(latch_i, Header, header_ip1)
>   redirectBackedge(cloneOf(Latch, K-1), Header, Header)
>   # fix header PHIs (induction chain across clones) and exit/LCSSA PHIs
>   ...
>   # simplifyCFG / instcombine cleanup
> ```

---

### 6. Splitting

> [!note] Definition
> Partition one loop into several smaller loops, each handling part of the iteration range. **Peeling** is the special case of pulling out the first (or last) few iterations. LLVM: peeling lives in the unroller (`LoopPeel`).

> [!example]+ Peel the first iteration
> **Before:**
> ```c
> int sum = 0;
> for (i = 0; i < N; i++) { sum += A[i]; }
> ```
> **After:**
> ```c
> int sum = 0;
> sum += A[0];                 // peeled first iteration
> for (i = 1; i < N; i++) { sum += A[i]; }
> ```

---

### 7. Loop-invariant code motion (LICM)

> [!note] Definition
> Move code that computes the **same value on every iteration** out of the loop (to the preheader), if doing so is legal. LLVM pass: `-licm`.

> [!example]+ Hoisting an invariant
> **Before** (`x = y+z` and `x*x` don't depend on `i`):
> ```c
> for (int i = 0; i < n; i++) {
>   x = y + z;             // invariant w.r.t. i
>   a[i] = 6 * i + x * x;  // x*x also invariant
> }
> ```
> **After** (hoisted to the preheader):
> ```c
> x  = y + z;
> t1 = x * x;
> for (int i = 0; i < n; i++) {
>   a[i] = 6 * i + t1;
> }
> ```

> [!note]- Loop-invariant — the recursive definition (click to expand)
> An instruction is **loop-invariant** iff, for every operand $x$, **either**
> - all reaching definitions of $x$ are *outside* the loop, **or**
> - there is exactly one definition of $x$ and it is *itself* already marked invariant.
>
> Compute by iterating to a fixed point over the loop body in dominator-tree (DFS) order so definitions are seen before uses — the classic monotone data-flow fixpoint.

> [!warning] Legality — three conditions before moving code
> 1. **Dominance:** the (single) definition must dominate all uses; the instruction's block must dominate all loop exits (else you'd compute something that the original didn't on some path).
>    ```c
>    while (cond) {
>      if (...) { x = 42; }   // does NOT dominate the use
>      y = x + 1;             // ⇒ cannot hoist x
>    }
>    ```
> 2. **Used only outside?** then **sink** it instead — move the assignment *after* the loop:
>    ```c
>    int s = 0, t;
>    for (int i = 0; i < n; i++) { s += arr[i]; t = expensive(); }
>    int result = s + t;      // t recomputed each iter but constant ⇒ sink after loop
>    ```
> 3. **No side effects / aliasing:** calls or memory ops must not interact with memory in a way that changes meaning — checked by [[pointer-alias-analysis|alias analysis]].

> [!tip] Rotation enables LICM (`-loop-rotate`)
> `LoopRotate` turns a `for`-style (test-first) loop into a `do/while` (test-last) loop, which gives a clean preheader to hoist into — *especially loads*. It is an **enabling** transform: it doesn't hoist by itself, it makes LICM safe and effective.
> ```c
> for (int i = 0; i < n; ++i) body(i);   // test-first
> // ⇒ rotated:
> int i = 0;
> if (i < n) { do { body(i); ++i; } while (i < n); }  // guard + do/while
> ```
> The guard matters: without proving the body runs at least once, hoisting a load `v = *p` out of a zero-trip loop could fault where the original wouldn't. *(Source: LLVM LoopTerminology — Rotated Loops.)*

---

### 8. Vectorization

> [!info] Quick primer (not in your original notes)
> Replace scalar iterations with **SIMD** operations that process several elements at once. LLVM has two vectorizers:
> - **Loop vectorizer** `-loop-vectorize` — widens a loop so each iteration handles a vector of $w$ elements (plus a scalar *remainder/epilogue* loop).
> - **SLP vectorizer** `-slp-vectorizer` — packs independent straight-line scalar ops into vectors.
>
> Legality again reduces to [[dependence-analysis|dependence analysis]]: a loop is vectorizable when iterations carry no dependence that vectorizing would violate (or such dependences are handled by runtime checks).

---

### 9. Fission (distribution)

> [!note] Definition
> Break one loop into multiple loops over the **same index range**, each holding a subset of the statements. LLVM: `LoopDistribute` (`-loop-distribute`); enabled at `-O2/-O3` or via `#pragma clang loop distribute(enable)`.

> [!example]+ Distribute by dependence class
> **Before:**
> ```c
> for (int i = 1; i < n; i += 1) {
>   A[i] = i;
>   B[i] = 2 + B[i];
>   C[i] = 3 + C[i - 1];   // loop-carried: needs C[i-1]
> }
> ```
> **After** (runtime check `rtc` guards the fast path):
> ```c
> if (rtc) {
>   for (int i = 1; i < n; i++) A[i] = i;          // coincident (independent)
>   for (int i = 1; i < n; i++) B[i] = 2 + B[i];   // coincident
>   for (int i = 1; i < n; i++) C[i] = 3 + C[i-1]; // sequential (carried dep)
> } else {
>   for (int i = 1; i < n; i++) { A[i]=i; B[i]=2+B[i]; C[i]=3+C[i-1]; } // fallback
> }
> ```
> Statements with no loop-carried dependence become **coincident** loops; those with one stay **sequential**. Fission is sound **only** when the original data dependences are preserved.

> [!warning] When fission does *not* apply
> Interdependent statements (a true cycle of dependences) can't be separated:
> ```c
> for (int i = 1; i < N; i++) {
>   A[i] = A[i-1] + B[i];  // needs A[i-1]
>   B[i] = A[i] * 2;       // needs A[i] just computed
> }
> ```

> [!info] Why & how
> - **Why:** improve cache locality / reduce misses, and **expose parallelism** (each split loop can run independently).
> - **How** (`LoopDistributeLegacy`): partition instructions by walking the body backward; unsafe-dependence instructions go to *cyclic* partitions, the rest to *non-cyclic* ones. Memory dependence of loads/stores is classified via [[memory-ssa|Memory SSA]] as **Def** / **Clobber** / **Unknown**. Only innermost, single-exit loops are considered.

---

### 10. Fusion

> [!note] Definition
> The inverse of fission: **merge adjacent loops** with the same iteration space into one body (a.k.a. jamming/merging). LLVM: `LoopFuse` (`-loop-fusion`).

> [!example]+ Fuse two element-wise loops
> **Before:**
> ```c
> for (j = 0; j < 300; j++) a[j] = a[j] + 3;
> for (k = 0; k < 300; k++) b[k] = b[k] + 4;
> ```
> **After:**
> ```c
> for (f = 0; f < 300; f++) { a[f] = a[f] + 3; b[f] = b[f] + 4; }
> ```

> [!warning] Legality — when fusion is unsafe
> - **Not adjacent** — an intervening side-effecting statement blocks it:
>   ```c
>   for (…) { … }  someSideEffectFunction();  for (…) { … }  // ✗
>   ```
> - **Different trip counts** — iteration spaces must match.
> - **Negative (backward) dependence** — the second loop must not read data a *future* iteration of the first would produce:
>   ```c
>   for (i=0;i<N;i++) A[i] = B[i] + 1;
>   for (i=0;i<N;i++) C[i] = A[i+1] * 2;   // reads A[i+1] ⇒ cannot fuse
>   ```
> - Typically only single-entry/single-exit loops qualify.

> [!info] Why fuse?
> Better **data locality** (touch `a[f]`/`b[f]` together → fewer cache misses) and less **loop-control overhead** (one set of compares/increments/branches). Combined with scalar replacement of array temporaries it can raise memory-bandwidth utilization.

> [!quote] Sources (official LLVM docs)
> - **Also in:** Muchnick *Advanced Compiler Design & Impl.* §13.2 (LICM) and §14 (loop optimizations).
> - **Source:** [`Transforms/Scalar/`](https://github.com/llvm/llvm-project/tree/main/llvm/lib/Transforms/Scalar) (LICM, LoopUnroll, LoopDistribute, LoopFuse) · [`Transforms/Vectorize/`](https://github.com/llvm/llvm-project/tree/main/llvm/lib/Transforms/Vectorize)
> - [LLVM Loop Terminology (and Canonical Forms)](https://llvm.org/docs/LoopTerminology.html)
> - [LLVM Language Reference — `phi`](https://llvm.org/docs/LangRef.html#phi-instruction)
> - [LLVM Passes](https://llvm.org/docs/Passes.html) — `-licm`, `-loop-unroll`, `-loop-rotate`, `-lcssa`, `-loop-simplify`, `-loop-distribute`, `-loop-vectorize`.
