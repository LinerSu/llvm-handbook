---
title: The Running Example — one program through the pipeline
facet: application
stage: optimization
ecosystem: [llvm]
concepts: [llvm-ir, ssa, memory-optimization, loop-optimization, induction-variables, redundancy-elimination, constant-propagation, interprocedural, inlining, code-generation]
prereqs: [llvm-basics]
related: [ssa-form, mem2reg, loop-info, getelementptr, scalar-evolution, induction-variables-and-strength-reduction, inlining, instruction-combining]
docs: "Produced locally with `clang -emit-llvm` (Apple clang 17 ≈ LLVM 19); cosmetics track the clang version — see [[llvm-version]]"
tags: [kind/concept, status/verified, version-sensitive]
status: verified
verified_on: 2026-06-29
---

# The Running Example — one program through the pipeline

> 🧭 **Application** · `application · optimization · llvm` · Index [[LLVM.MOC]] · v [[llvm-version]]
> **Prerequisites:** [[llvm-basics]]

> [!abstract] Why this note exists
> **One** small program, carried through the whole pipeline, so the vault doesn't mint a fresh example per concept. Every IR block below is **real `clang` output**, not hand-written. Other notes link to the anchors here (e.g. `[[running-example#3-after-mem2reg--loop-opts--o1]]`) and show only the slice they need. *Convention: reuse this example; extend it only when a concept genuinely needs more — and add that extension [below](#7-sanctioned-extensions), not in scattered notes.*

> [!tip] Reproduce it yourself
> ```bash
> clang -O0 -emit-llvm -S -fno-discard-value-names -Xclang -disable-O0-optnone runex.c -o -   # front-end IR
> clang -O1 -emit-llvm -S -fno-discard-value-names runex.c -o -                                # optimized SSA
> clang -O1 -S runex.c -o -                                                                     # target assembly
> ```
> Install `opt`/`llc` (`brew install llvm`) to step **one pass at a time** (`opt -passes=mem2reg -S`).

---

## 1. The program

```c
// runex.c
int accumulate(int *a, int n, int k) {
    int sum = 0;
    for (int i = 0; i < n; i++)
        sum += a[i] * k;
    return sum;
}

int caller(int *a, int n) {
    return accumulate(a, n, 4);   // constant argument
}
```

A scaled array reduction plus a caller that pins `k = 4`. Small, but it exercises stack slots, a loop, array addressing, arithmetic, a reduction, and an interprocedural constant.

## 2. Front-end IR (`-O0`) — everything is a stack slot

> [!example]+ `accumulate` at `-O0` (before mem2reg)
> ```llvm
> define i32 @accumulate(ptr %a, i32 %n, i32 %k) {
> entry:
>   %a.addr = alloca ptr ; %n.addr = alloca i32 ; %k.addr = alloca i32
>   %sum = alloca i32 ; %i = alloca i32           ; every local is memory
>   store ... ; store i32 0, ptr %sum ; store i32 0, ptr %i
>   br label %for.cond
> for.cond:                          ; loop header test
>   %0 = load i32, ptr %i
>   %1 = load i32, ptr %n.addr
>   %cmp = icmp slt i32 %0, %1
>   br i1 %cmp, label %for.body, label %for.end
> for.body:
>   %2 = load ptr, ptr %a.addr
>   %3 = load i32, ptr %i
>   %idxprom = sext i32 %3 to i64
>   %arrayidx = getelementptr inbounds i32, ptr %2, i64 %idxprom   ; &a[i]
>   %4 = load i32, ptr %arrayidx
>   %5 = load i32, ptr %k.addr
>   %mul = mul nsw i32 %4, %5
>   %6 = load i32, ptr %sum
>   %add = add nsw i32 %6, %mul
>   store i32 %add, ptr %sum
>   br label %for.inc
> for.inc:
>   %7 = load i32, ptr %i ; %inc = add nsw i32 %7, 1 ; store i32 %inc, ptr %i
>   br label %for.cond
> for.end:
>   %8 = load i32, ptr %sum ; ret i32 %8
> }
> ```

This stage grounds: the **object model** (Module→Function→BasicBlock→Instruction, [[llvm-basics]]); the **CFG** `entry→for.cond→for.body→for.inc→for.cond` with the back-edge ([[control-flow-graph]], [[loop-info]]); **GEP** for `a[i]` ([[getelementptr]]); and the *input* to mem2reg — every variable is an `alloca` with explicit `load`/`store`.

## 3. After mem2reg + loop opts (`-O1`)

> [!example]+ `accumulate` at `-O1` (SSA, no allocas)
> ```llvm
> define i32 @accumulate(ptr nocapture readonly %a, i32 %n, i32 %k) {
> entry:
>   %cmp4 = icmp sgt i32 %n, 0
>   br i1 %cmp4, label %for.body.preheader, label %for.cond.cleanup
> for.body.preheader:
>   %wide.trip.count = zext nneg i32 %n to i64           ; trip count exposed (SCEV)
>   br label %for.body
> for.cond.cleanup:
>   %sum.0.lcssa = phi i32 [ 0, %entry ], [ %add, %for.body ]   ; LCSSA exit φ
>   ret i32 %sum.0.lcssa
> for.body:
>   %indvars.iv = phi i64 [ 0, %for.body.preheader ], [ %indvars.iv.next, %for.body ]  ; IV {0,+,1}, widened to i64
>   %sum.05    = phi i32 [ 0, %for.body.preheader ], [ %add, %for.body ]               ; reduction φ
>   %arrayidx  = getelementptr inbounds i32, ptr %a, i64 %indvars.iv
>   %0   = load i32, ptr %arrayidx, align 4, !tbaa !6
>   %mul = mul nsw i32 %0, %k
>   %add = add nsw i32 %mul, %sum.05
>   %indvars.iv.next = add nuw nsw i64 %indvars.iv, 1
>   %exitcond.not    = icmp eq i64 %indvars.iv.next, %wide.trip.count   ; LFTR exit test
>   br i1 %exitcond.not, label %for.cond.cleanup, label %for.body
> }
> ```

The single most important before/after in the vault. Compare with §2:
- **mem2reg** ([[mem2reg]], [[ssa-form]]): the five `alloca`s are gone; `sum` and `i` are now **φ-nodes** at the loop header — `%sum.05` (the reduction) and `%indvars.iv` (the IV).
- **Loop canonical form** ([[loop-info]]): a real `for.body.preheader`; `%sum.0.lcssa` is the **loop-closing (LCSSA) φ** at the exit.
- **SCEV + IndVarSimplify** ([[scalar-evolution]], [[induction-variables-and-strength-reduction]]): the IV is **widened to i64**, the **trip count** `%wide.trip.count` is materialized, and the exit test is canonicalized to `icmp eq …, trip_count` (**LFTR**).
- **Inferred facts** ([[extending-llvm-ir]], [[pointer-alias-analysis]]): `%a` gained `nocapture readonly`; the load carries `!tbaa`.

## 4. Interprocedural (`caller` at `-O1`)

> [!example]+ `caller` — `accumulate` inlined, `k = 4` propagated
> ```llvm
> define i32 @caller(ptr nocapture readonly %a, i32 %n) {
>   ; ... same loop, but inlined (blocks suffixed .i, exit block accumulate.exit) ...
>   %mul.i = shl nsw i32 %0, 2          ; was `mul %0, %k` — k=4 folded, then mul→shl
>   %add.i = add nsw i32 %mul.i, %sum.05.i
>   ; ...
> }
> ```

Two transforms visible at once: **[[inlining]]** pulled `accumulate`'s body into `caller` (hence `accumulate.exit` and the `.i` suffixes), and with `k` now the constant `4`, **constant propagation + [[instruction-combining|InstCombine]]** turned `mul %0, %k` into `shl %0, 2`. This is the seed for [[ipsccp|IPSCCP]] and [[function-specialization]] too.

## 5. Stage → concept map

| What you see | Where (stage) | Note |
|---|---|---|
| Module/Function/BB/Instruction, SSA values | §2 | [[llvm-basics]] |
| `alloca`+`load`/`store` per variable | §2 | [[mem2reg]] (input) |
| CFG blocks + back-edge | §2 | [[control-flow-graph]], [[loop-info]] |
| `getelementptr … a[i]` | §2/§3 | [[getelementptr]] |
| `alloca`s gone; `phi` for `sum`,`i` | §3 | [[mem2reg]], [[ssa-form]] |
| preheader, `%sum.0.lcssa` | §3 | [[loop-info]] |
| `%indvars.iv` `{0,+,1}`, widened, trip count, LFTR | §3 | [[scalar-evolution]], [[induction-variables-and-strength-reduction]] |
| `nocapture readonly`, `!tbaa` | §3 | [[extending-llvm-ir]], [[pointer-alias-analysis]] |
| inlined body, `k=4`, `mul`→`shl` | §4 | [[inlining]], [[instruction-combining]] |

## 6. Where the data lives

The loop's reduction (`%sum`) and counter (`%i`) are the things that become φ-nodes; the array `a` stays in memory and is read through GEP+load. Keep this picture — most later notes are a zoom into one row of the table above.

## 7. Sanctioned extensions

Mint these *here* (named), never as new standalone examples, when a concept needs more than the base shows:

- **`ext-licm`** — change the body to `sum += a[i] * (k + n);`. `k + n` is loop-invariant → **LICM** hoists it to the preheader. ([[loop-invariant-code-motion]])
- **`ext-gvn`** — `sum += a[i]*k + a[i];`. The second `a[i]` is a redundant load → **GVN/CSE** removes it. ([[value-numbering]], [[early-cse]])
- **`ext-if`** — wrap the body in `if (a[i] > 0)`. Gives a branch for **SimplifyCFG / JumpThreading / if-conversion**. ([[simplifycfg]], [[jump-threading]], [[if-conversion]])
- **`ext-struct`** — pass `struct {int*p; int n;} *s` instead of `a, n`. Exercises **SROA** on the aggregate and `!tbaa` field disambiguation. ([[scalar-replacement-of-aggregates]])
- **`ext-vec`** — compile at `-O2`: the loop **vectorizes** (NEON/AVX) with a scalar remainder. ([[loop-transformations]])
- **`ext-asm`** — `clang -O1 -S runex.c`: target assembly, register-allocated loop. ([[code-generation-overview]], [[register-allocation]], [[instruction-scheduling]])

> [!quote] Source & confidence
> All IR is real `clang -emit-llvm` output (Apple clang 17, ≈ LLVM 19). Cosmetic spellings (e.g. `nocapture` → `captures(none)` in LLVM 21+, `nneg`/attribute lists) track the producing compiler — the *shapes* (φ placement, LCSSA, LFTR, inline+fold) are version-stable. Version anchor: [[llvm-version]].
