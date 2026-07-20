---
title: MemorySanitizer (MSan)
facet: implementation
stage: runtime
ecosystem: [llvm]
concepts: [memory-safety]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/Instrumentation/MemorySanitizer.cpp" }
src: "llvm/lib/Transforms/Instrumentation/MemorySanitizer.cpp"
docs: "Clang — MemorySanitizer ↗ https://clang.llvm.org/docs/MemorySanitizer.html"
prereqs: [sanitizers, llvm-basics]
related: [sanitizers, address-sanitizer, thread-sanitizer, debug-info]
tags: [kind/pass, status/unverified]
status: unverified
verified_on: ""
---

# MemorySanitizer (MSan)

> 🧭 **Implementation** · `implementation · runtime · llvm` · Index [[LLVM.MOC]]
> **Realizes:** [[sanitizers|the sanitizer architecture]] for **uninitialised reads** · **Prerequisites:** [[sanitizers]] · **Related:** [[address-sanitizer]]

> [!abstract] What this note adds
> `MemorySanitizer.cpp` — *"a detector of uninitialized reads."* Where [[address-sanitizer|ASan]] asks *"may I touch this byte?"* (1 shadow byte per 8), MSan asks the harder question *"is this **bit** defined?"*, and pays for it with a **1:1, bit-for-bit shadow**: the source says *"we use 8 shadow bits per byte of application memory and use a direct shadow mapping,"* with *"the default value of shadow … 0, which means 'clean' (not poisoned)."* Shadow must then **propagate through arithmetic**, so undefinedness follows the data. The practical consequence dominates everything else about the tool: MSan *"needs to see all program events"*, so **you must compile everything with MSan** — libc++ included — or you get false positives from uninstrumented code.

---

## 1. The pass

`MemorySanitizer.cpp` instruments loads, stores and arithmetic so that every value carries a parallel *shadow* value recording which of its bits are undefined, and reports when an undefined value is used in a way that matters (a branch, a syscall argument, a dereference). Its lineage is explicit: the header notes the algorithm is *"similar to Memcheck"* (Valgrind), with the major difference being **compiler** instrumentation instead of binary instrumentation, which *"gives us much better register allocation, possible compiler optimizations and a fast start-up."*

## 2. What it realizes (and why promoted)

It is the sharpest contrast in the [[sanitizers|sanitizer family]] — same architecture, radically different shadow, because the *question* is different:

> [!info] ASan vs MSan — the shadow tells you the question
>
> | | [[address-sanitizer\|ASan]] | **MSan** |
> |---|---|---|
> | Question | is this address legal to touch? | is this **bit** initialised? |
> | Shadow ratio | 1 byte : **8** app bytes | 1 byte : **1** app byte (*"8 shadow bits per byte"*) |
> | Propagates through arithmetic? | no — addressability is a property of the allocation | **yes** — undefinedness flows with the data |
> | Clean value | `00` = addressable | `0` = clean / not poisoned |

## 3. Where it runs

An IR instrumentation pass plus the MSan runtime. Newly allocated memory (`malloc`, `alloca`) is **poisoned**; a store propagates the source value's shadow; a load reads both value and shadow; using an undefined value where it becomes observable calls the MSan report callback — **`__msan_warning_noreturn`** by default, `__msan_warning_with_origin_noreturn` with origins on, and the non-`noreturn` variants under `-fsanitize-recover=memory`.

## 4. How it's built — shadow, and then origins

**Shadow.** Direct mapping, one shadow byte per application byte, `0` meaning clean. Because the shadow is bit-precise, arithmetic must combine operand shadows — this is why MSan's pass is far more intrusive than TSan's call-inserting.

**Origins.** A bare "you used an undefined value here" is often useless; you want *where it came from*. MSan can track **origins** — allocation sites of poisoned memory — as 4-byte values (`kOriginSize = 4`) held in a second mapping alongside the shadow. With origin tracking enabled the userspace report callback becomes **`__msan_warning_with_origin_noreturn`** (or `__msan_warning_with_origin` under `-fsanitize-recover=memory`), which carries the 32-bit origin.

> [!info] Don't confuse userspace MSan with KMSAN
> The file header's *"`__msan_warning()` takes a 32-bit origin parameter"* line and the `__msan_metadata_ptr_for_load_n(ptr, size)` helper family belong to **KMSAN** (`-fsanitize=kernel-memory`), which allocates metadata per page and therefore reaches shadow/origin through runtime helpers. Userspace MSan does the opposite — it *computes* shadow addresses from a direct mapping inline.

> [!warning] Origin tracking is **off by default** — check the `cl::opt`
> `ClTrackOrigins` is declared `cl::init(0)`, i.e. **disabled** unless you ask for it (`-fsanitize-memory-track-origins`). Enabling it costs additional time and memory but converts "an undefined value reached here" into "…and it was born at *that* allocation." This is the standing [[note-checklist|`cl::opt` default check]]: the feature exists, so it *reads* as though it is on — it is not.

## 5. Textbook → LLVM (the whole-program requirement)

> [!info]+ Why MSan is harder to adopt than ASan
>
> | | ASan | MSan |
> |---|---|---|
> | Uninstrumented library code | fine — it still uses the intercepted allocator | **a problem** — its writes leave shadow unset, so later reads look undefined |
> | What you must rebuild | your code | *everything*, including the C++ standard library |

The source states the constraint directly: MSan *"needs to see all program events, including system calls and reads/writes in system libraries, so we either need to compile **everything** with msan or use a binary translation component (e.g. DynamoRIO) to instrument pre-built libraries."* In practice this means an MSan-instrumented libc++ (`-fsanitize=memory` plus a rebuilt standard library); skip it and you drown in false positives.

## 6. Run it yourself

> [!example]+ The canonical uninitialised read
> ```c
> int main(void) { int x; return x; }   // x is never initialised
> ```
> ```bash
> clang -fsanitize=memory -fsanitize-memory-track-origins -g -O1 msan.c -o msan_bin && ./msan_bin
> # WARNING: MemorySanitizer: use-of-uninitialized-value ... (plus, with origins, the allocation site)
> ```
>
> > [!danger] Unverified — not reproduced on this machine
> > MSan is **not available on Darwin/arm64**: `clang -fsanitize=memory` on this host fails with *"unsupported option '-fsanitize=memory' for target 'arm64-apple-darwin24.6.0'"*. It is primarily a Linux/x86-64 tool. Unlike the [[address-sanitizer|ASan]] and [[thread-sanitizer|TSan]] notes, the output above is **not** a captured transcript — it is the documented shape, and is marked unverified rather than presented as real output.

## 7. Flags & knobs

`-fsanitize=memory` (enable); `-fsanitize-memory-track-origins[=2]` (origins — off by default, see §4); `-fno-omit-frame-pointer` and `-g` for readable traces; `MSAN_OPTIONS=` at runtime. Requires an MSan-instrumented standard library for clean results.

## 8. Siblings & variants

- **[[address-sanitizer|ASan]]** — addressability; cheaper, adoptable incrementally.
- **[[thread-sanitizer|TSan]]** — races.
- **Valgrind/Memcheck** — the ancestor: same idea via binary instrumentation, so no rebuild required, but much slower and with worse register/optimization behaviour.
- **`-ftrivial-auto-var-init=`** — a *mitigation* rather than a detector: initialise automatics so uninitialised reads become deterministic instead of undefined.

## 9. Limitations & notes

> [!warning] What makes MSan hard
> - **All-or-nothing instrumentation.** Any uninstrumented code that writes memory can cause false positives; you need an instrumented libc++.
> - **Platform-limited.** Linux/x86-64-centric; not supported on Darwin/arm64 (verified above).
> - **Expensive**, and mutually exclusive with ASan/TSan (each wants its own shadow layout).
> - **It reports *use*, not birth** — unless origins are enabled, and they are `cl::init(0)`.

> [!summary] The one thing to remember
> MSan detects **uninitialised reads** with a **1:1, bit-precise shadow** (*"8 shadow bits per byte"*, `0` = clean) that **propagates through arithmetic** — the opposite trade from [[address-sanitizer|ASan]]'s 1:8 addressability map. Its defining practical constraint is that it *"needs to see all program events"*, so **everything must be compiled with MSan**; and **origin tracking is off by default** (`ClTrackOrigins`, `cl::init(0)`).

> [!quote] Sources & confidence
> Claims were enumerated and checked against the pinned LLVM source ([[llvm-version]], `llvmorg-22.1.8`) by `note-correctness-review` on 2026-07-20, and refutations corrected. **Status stays `unverified` deliberately**: this note carries a `> [!danger] Unverified` block for material outside the pinned checkout (compiler-rt runtime internals / an example not reproducible on this platform), and [[note-checklist]] §8 says a note with unconfirmed content stays `unverified`. GitHub links track `main`; the checked revision is the pinned tag.
> - [llvm/lib/Transforms/Instrumentation/MemorySanitizer.cpp](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Instrumentation/MemorySanitizer.cpp) — *"a detector of uninitialized reads"*; *"similar to Memcheck"*; *"we use 8 shadow bits per byte of application memory and use a direct shadow mapping"*; *"The default value of shadow is 0, which means 'clean'"*; *"needs to see all program events … compile everything with msan"*; `Recover ? "__msan_warning" : "__msan_warning_noreturn"` and the `__msan_warning_with_origin[_noreturn]` pair; `kOriginSize = 4`; `__msan_metadata_ptr_for_load_n` (**KMSAN-only**); **`ClTrackOrigins` … `cl::init(0)`**.
> - **No runtime transcript**: MSan is unsupported on this host (Darwin/arm64), so no output was captured — the example is marked `Unverified` rather than fabricated.
> - [Clang — MemorySanitizer](https://clang.llvm.org/docs/MemorySanitizer.html) — primary doc.
