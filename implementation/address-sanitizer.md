---
title: AddressSanitizer (ASan)
facet: implementation
stage: runtime
ecosystem: [llvm]
concepts: [memory-safety]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/Instrumentation/AddressSanitizer.cpp" }
src: "llvm/lib/Transforms/Instrumentation/AddressSanitizer.cpp"
docs: "Clang — AddressSanitizer ↗ https://clang.llvm.org/docs/AddressSanitizer.html"
prereqs: [sanitizers, llvm-basics]
related: [sanitizers, memory-sanitizer, thread-sanitizer, fbounds-safety, safe-buffers, debug-info]
tags: [kind/pass, status/verified]
status: verified
verified_on: 2026-07-20
---

# AddressSanitizer (ASan)

> 🧭 **Implementation** · `implementation · runtime · llvm` · Index [[LLVM.MOC]]
> **Realizes:** [[sanitizers|the sanitizer architecture]] for *addressability* bugs · **Prerequisites:** [[sanitizers]], [[llvm-basics]] · **Related:** [[memory-sanitizer]], [[fbounds-safety]]

> [!abstract] What this note adds
> The engineering of the most-used sanitizer: `AddressSanitizer.cpp`, *"an address basic correctness checker."* Its defining trick is a **1-shadow-byte-per-8-application-bytes** map (`kDefaultShadowScale = 3`) in which each shadow byte says *how many of those 8 bytes are addressable* — or, if negative-valued, **which kind of poison** they are (heap redzone, freed region, stack redzone…). Around every allocation the compiler and runtime place **redzones**, so an off-by-one walks straight into poisoned shadow and is caught at the exact instruction. This is what turns "some memory corruption, somewhere" into a report naming your source line.

---

## 1. The pass

**`AddressSanitizer.cpp`** (`llvm/lib/Transforms/Instrumentation`) instruments every memory access with a shadow check, and cooperates with the compiler-rt runtime that intercepts `malloc`/`free` and owns the shadow region. It detects **heap and stack and global buffer overflow, use-after-free, use-after-return, use-after-scope, and double-free**.

## 2. What it realizes (and why promoted)

It is the concrete instance of the [[sanitizers|shared sanitizer architecture]] worth knowing in detail, because the shadow encoding is legible and directly explains both what ASan catches and what it costs. It is also the *dynamic* counterpart to the static bounds guarantees in [[fbounds-safety]] and [[safe-buffers]].

## 3. Where it runs

An instrumentation pass over IR (so after the front end and the optimizer's main work), plus a link against the ASan runtime. You opt in with `-fsanitize=address`; the pass inserts:

- a shadow check before each load/store,
- **redzone** creation and poisoning around stack objects — via *inline* shadow stores, or `__asan_set_shadow_*` callbacks (`kAsanSetShadowPrefix`) when a run of shadow bytes is large; `__asan_poison_stack_memory` / `__asan_unpoison_stack_memory` are reserved for **dynamic** allocas under use-after-scope,
- global registration so globals get redzones too — `__asan_register_elf_globals` on ELF, `__asan_register_image_globals` on Mach-O, with plain `__asan_register_globals` as the non-GC fallback (the runtime funnels all three into the same registration),
- a call to `__asan_report_*` on failure (the pass builds the name from `kAsanReportErrorTemplate = "__asan_report_"` plus the access type and size).

## 4. How it's built — the shadow map

The core constants are in the pass:

> [!info] Shadow mapping (confirmed, pinned LLVM [[llvm-version]])
>
> | Constant | Value | Meaning |
> |---|---|---|
> | `kDefaultShadowScale` | **3** | `2^3 = 8` application bytes per shadow byte |
> | `kDefaultShadowOffset64` | `1ULL << 44` | the **fall-through** 64-bit offset — most targets override it: Linux/x86-64 uses `0x7fff8000`, AArch64 `1ULL << 36`, and macOS/arm64, iOS, RISCV64 and Windows/x86-64 resolve it **dynamically at runtime** (`kDynamicShadowSentinel`) |
>
> Shadow address = `(addr >> 3) + offset`, where the offset is target-specific (see the row above). The runtime confirms the ratio in its own report legend: *"one shadow byte represents 8 application bytes."*

**The encoding.** For an 8-byte granule, a non-negative shadow byte counts how many leading bytes are addressable (`0` = all 8 usable, `1`–`7` = partially addressable tail); a "negative" (high-bit) value is a **poison class**. From the runtime's legend:

> [!info]+ Shadow byte legend (verbatim from a real ASan report)
>
> | Byte | Meaning |
> |---|---|
> | `00` | addressable |
> | `01`–`07` | partially addressable (that many bytes usable) |
> | `fa` | heap **left redzone** |
> | `fd` | **freed** heap region (use-after-free) |
> | `f1` / `f2` / `f3` | stack left / mid / right redzone |
> | `f5` | stack after return (use-after-return) |
> | `f8` | stack use-after-scope |
> | `f9` | global redzone |

That table *is* the tool: every bug class ASan reports is "the shadow byte for this access was one of the poison values."

## 5. Textbook → LLVM (why redzones, not bounds)

> [!info]+ How ASan differs from a bounds checker
>
> | A bounds checker | AddressSanitizer |
> |---|---|
> | Needs to know the intended object and its extent | Needs only *"is this byte poisoned?"* — no object model |
> | Catches out-of-bounds *within* the correct object too | Misses intra-object overflow unless it crosses into a redzone |
> | Type/​source-directed ([[fbounds-safety]], [[safe-buffers]]) | Allocation-directed, language-agnostic |

The redzone design is why ASan is cheap enough to be practical and also why a stride that *jumps over* the redzone into another live object can slip through.

## 6. Run it yourself

> [!example]+ A real heap-buffer-overflow report
> ```c
> #include <stdlib.h>
> int main(void){ int *a = malloc(4*sizeof(int)); a[4] = 1; free(a); return 0; }
> ```
> ```bash
> clang -fsanitize=address -g -O0 asan.c -o asan_bin && ./asan_bin
> ```
> ```text
> ==82467==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x602000000100 …
> WRITE of size 4 at 0x602000000100 thread T0
>     #0 … in main asan.c:2
> 0x602000000100 is located 0 bytes after 16-byte region [0x6020000000f0,0x602000000100)
> allocated by thread T0 here:
>     #0 … in malloc
>     #1 … in main asan.c:2
> =>0x602000000100:[fa]fa fa fa fa fa fa fa …
> Shadow byte legend (one shadow byte represents 8 application bytes):
>   Addressable:           00
>   Heap left redzone:     fa
>   Freed heap region:     fd
> ```
> Read it end to end: the write landed **0 bytes after** a 16-byte allocation, the shadow byte there is **`fa`** (heap redzone), and both the faulting line and the *allocation* line are named — the latter courtesy of [[debug-info|debug info]], which is why `-g` matters.

## 7. Flags & knobs

`-fsanitize=address` (enable); `-fno-omit-frame-pointer` and `-g` for readable traces; `ASAN_OPTIONS=` at runtime (e.g. `detect_leaks=1`, `halt_on_error=0`); `-fsanitize-address-use-after-scope`. `-fsanitize=address,undefined` is the usual CI pairing.

## 8. Siblings & variants

- **[[memory-sanitizer|MSan]]** — uninitialised reads (a *different* question; needs 1:1 shadow).
- **[[thread-sanitizer|TSan]]** — data races.
- **HWAddressSanitizer** — the same *"address basic correctness checker"* goal via **pointer tagging** rather than dense redzone shadow; far cheaper in memory, AArch64-oriented, and the realistic candidate for always-on hardening.
- **LeakSanitizer** — leak detection, commonly enabled alongside ASan.

## 9. Limitations & notes

> [!warning] What ASan won't catch
> - **Uninitialised reads** — that is [[memory-sanitizer|MSan]]'s job; ASan only knows *addressability*, not *initialisedness*.
> - **Intra-object overflow** — writing past a struct field into the next field of the *same* object stays inside addressable memory, so no redzone is touched.
> - **Not free.** Roughly a small-integer-factor slowdown plus substantial extra memory for shadow and redzones; a debugging/CI tool, not a production hardening mode.
> - **Can't be combined** with TSan/MSan in one binary — each wants its own shadow layout.

> [!summary] The one thing to remember
> ASan maps **8 application bytes to 1 shadow byte** (`kDefaultShadowScale = 3`), where the byte counts addressable bytes or names a **poison class** (`fa` heap redzone, `fd` freed, `f1`–`f3` stack redzones). **Redzones** around allocations turn an overflow into a poisoned-shadow hit at the exact instruction, reported with the faulting *and* allocating source lines.

> [!quote] Sources & confidence
> **Verified 2026-07-20** — every falsifiable claim was enumerated and checked against the pinned LLVM source ([[llvm-version]], `llvmorg-22.1.8`) by `note-correctness-review`; refuted claims were corrected (batch error rate 7.3%, 9/123). GitHub links track `main`; the checked revision is the pinned tag.
> - [llvm/lib/Transforms/Instrumentation/AddressSanitizer.cpp](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Instrumentation/AddressSanitizer.cpp) — *"an address basic correctness checker"*; `kDefaultShadowScale = 3`; `kDefaultShadowOffset64 = 1ULL << 44`; `kAsanReportErrorTemplate`, `kAsanRegisterGlobalsName`, `kAsanPoisonStackMemoryName`; `getRedzoneSizeForScale`.
> - The shadow-byte legend and the report transcript are **verbatim runtime output** from the tool itself (Apple clang 17 / arm64 — Apple's own versioning, not an upstream release number, and not the pinned tag). Runtime internals (quarantine, interception) live in **compiler-rt**, outside the pinned sparse checkout.
> - [Clang — AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html) — primary doc.
