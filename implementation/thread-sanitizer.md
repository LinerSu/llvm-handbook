---
title: ThreadSanitizer (TSan)
facet: implementation
stage: runtime
ecosystem: [llvm]
concepts: [memory-safety]
implements:
  - { ecosystem: llvm, src: "llvm/lib/Transforms/Instrumentation/ThreadSanitizer.cpp" }
src: "llvm/lib/Transforms/Instrumentation/ThreadSanitizer.cpp"
docs: "Clang — ThreadSanitizer ↗ https://clang.llvm.org/docs/ThreadSanitizer.html"
prereqs: [sanitizers, llvm-basics]
related: [sanitizers, address-sanitizer, memory-sanitizer, debug-info]
tags: [kind/pass, status/unverified]
status: unverified
verified_on: ""
---

# ThreadSanitizer (TSan)

> 🧭 **Implementation** · `implementation · runtime · llvm` · Index [[LLVM.MOC]]
> **Realizes:** [[sanitizers|the sanitizer architecture]] for **data races** · **Prerequisites:** [[sanitizers]] · **Related:** [[address-sanitizer]], [[memory-sanitizer]]

> [!abstract] What this note adds
> `ThreadSanitizer.cpp` — *"a race detector."* The striking thing about it is how little the **compiler** does: the file's own header says the instrumentation is *"quite simple: Insert calls to run-time library before every memory access … Insert calls at function entry/exit. The rest is handled by the run-time library."* So the pass's job is to make every read, write, atomic and function boundary visible to compiler-rt — *inserting* a hook before plain loads and stores, and **replacing** atomics, fences and memory intrinsics with the corresponding runtime call outright. **All** the race-detection intelligence — the happens-before reasoning that decides whether two accesses are actually concurrent — lives in the runtime. That split is the note's lesson: the interesting algorithm is not in LLVM at all.

---

## 1. The pass

`ThreadSanitizer.cpp` instruments a function so that the runtime observes its memory behaviour, then leaves the analysis to compiler-rt. It detects **data races** — two threads accessing the same location concurrently, at least one writing, with no synchronisation ordering them.

## 2. What it realizes (and why promoted)

It is the [[sanitizers|shared architecture]] taken to its extreme: unlike [[address-sanitizer|ASan]], whose shadow encoding is legible in the pass itself, TSan's pass mostly *hands operations to the runtime* — inserting hooks around plain accesses and swapping atomics/fences/intrinsics for runtime calls. Understanding it means understanding a division of labour between compile time and run time.

## 3. Where it runs — what the pass inserts

Verbatim from the file header, the instrumentation phase is:

> [!info] `ThreadSanitizer.cpp` header (pinned LLVM [[llvm-version]])
>
> - *"Insert calls to run-time library before every memory access."*
> - *"Optimizations may apply to avoid instrumenting some of the accesses."*
> - *"Insert calls at function entry/exit."*
> - *"The rest is handled by the run-time library."*

Concretely the pass emits:

| Runtime call | For | Mechanism |
|---|---|---|
| `__tsan_read1/2/4/8/16`, `__tsan_write1/…/16` | plain loads and stores (`kNumberOfAccessSizes = 5`) | **inserted before** — the access itself survives |
| `__tsan_func_entry`, `__tsan_func_exit` | function boundaries (so the runtime can build stacks) | inserted |
| `__tsan_atomic{N}_load` / `_store` / RMW / `_compare_exchange_val` | atomics — these *establish* ordering | **replaces** the instruction (`I->eraseFromParent()`) |
| `__tsan_atomic_thread_fence` / `_signal_fence`, `__tsan_memcpy` / `__tsan_memset` | fences and mem-intrinsics | **replaces** the instruction |

Atomics matter more than they look: a race detector must know which operations create happens-before edges, which is exactly what the `__tsan_atomic*` hooks report.

## 4. How it's built — which accesses are skipped

`chooseInstructionsToInstrument` implements the "optimizations may apply" line — TSan does not blindly instrument everything. The source calls out, among others, that it will *"not instrument known races/'benign races' that come from compiler instrumentation"* and *"not instrument accesses from different address spaces."* Skipping provably-uninteresting accesses is what keeps an already expensive tool merely expensive.

## 5. Textbook → LLVM (where the algorithm lives)

> [!info]+ Compile time vs run time
>
> | Question | Answered by |
> |---|---|
> | Which operations touch memory / synchronise? | **the pass** (this note) — it inserts the hooks |
> | Were two accesses actually *concurrent*? | **the runtime** (compiler-rt) — happens-before over per-thread clocks and shadow cells |
> | Where did each access come from? | the runtime's stacks + [[debug-info\|debug info]] |

> [!danger] Unverified
> The runtime's detection algorithm (shadow cells per memory word, vector-clock / happens-before bookkeeping) lives in **compiler-rt**, which is outside this vault's pinned sparse checkout. It is described here only at the level the instrumentation pass and the tool's own output support; treat specifics of the runtime representation as unconfirmed against source.

## 6. Run it yourself

> [!example]+ A real data-race report
> ```c
> #include <pthread.h>
> int g;
> void *t(void *_) { g++; return 0; }
> int main(){ pthread_t a,b; pthread_create(&a,0,t,0); pthread_create(&b,0,t,0);
>             pthread_join(a,0); pthread_join(b,0); return g; }
> ```
> ```bash
> clang -fsanitize=thread -g -O1 tsan.c -o tsan_bin && ./tsan_bin
> ```
> ```text
> WARNING: ThreadSanitizer: data race (pid=82587)
>   Location is global 'g' at 0x00010429c000 (tsan_bin+0x100008000)
> SUMMARY: ThreadSanitizer: data race tsan.c:3 in t
> ```
> `g++` is a read-modify-write with no synchronisation; two threads run it, and TSan names the racing **line** and identifies the location as the global `g`. Note it found the race on *this* interleaving — see the limitation below.

## 7. Flags & knobs

`-fsanitize=thread` (enable); `-g` for line numbers; `TSAN_OPTIONS=` at runtime (e.g. `halt_on_error=1`, `history_size=`). Cannot be combined with `-fsanitize=address` or `memory` in one binary.

## 8. Siblings & variants

- **[[address-sanitizer|ASan]]** — addressability, not concurrency.
- **[[memory-sanitizer|MSan]]** — uninitialised reads.
- Static/annotation approaches to concurrency (Clang's thread-safety analysis, `-Wthread-safety`) catch lock-discipline violations at compile time, over all paths, without running the program.

## 9. Limitations & notes

> [!warning] What TSan won't do
> - **Only the interleavings you actually ran.** A race is reported when the runtime observes two unordered accesses; a schedule that never occurs is never reported. This is the sharp edge of dynamic analysis — run tests repeatedly, under load, and with fuzzing.
> - **Expensive.** Every memory access becomes a runtime call plus bookkeeping, with substantial memory overhead; a test-time tool.
> - **Needs to see the synchronisation.** Custom synchronisation the runtime doesn't understand (hand-rolled spinlocks via inline asm, some lock-free idioms) can produce reports for races that are ordered by a mechanism TSan can't observe.
> - **Mutually exclusive** with the other shadow-heavy sanitizers.

> [!summary] The one thing to remember
> TSan's **pass** is deliberately thin: it *inserts* `__tsan_read*`/`__tsan_write*` before plain accesses and `__tsan_func_entry`/`_exit` at boundaries, and **replaces** atomics, fences and mem-intrinsics with `__tsan_atomic*` etc. (`I->eraseFromParent()`) — *"the rest is handled by the run-time library."* The happens-before analysis that decides "concurrent?" lives in compiler-rt, and it can only judge the interleavings you actually execute.

> [!quote] Sources & confidence
> Claims were enumerated and checked against the pinned LLVM source ([[llvm-version]], `llvmorg-22.1.8`) by `note-correctness-review` on 2026-07-20, and refutations corrected. **Status stays `unverified` deliberately**: this note carries a `> [!danger] Unverified` block for material outside the pinned checkout (compiler-rt runtime internals / an example not reproducible on this platform), and [[note-checklist]] §8 says a note with unconfirmed content stays `unverified`. GitHub links track `main`; the checked revision is the pinned tag.
> - [llvm/lib/Transforms/Instrumentation/ThreadSanitizer.cpp](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Instrumentation/ThreadSanitizer.cpp) — *"a race detector"*; the four-bullet instrumentation summary; `kNumberOfAccessSizes = 5`; `__tsan_read*`/`__tsan_write*`, `__tsan_func_entry`/`__tsan_func_exit`, `__tsan_atomic{N}_load`/`_store`/RMW; `chooseInstructionsToInstrument`; the "benign races" and "different address spaces" exclusions.
> - Report transcript is **verbatim runtime output** (Apple clang 17 / arm64 — Apple's own versioning, not an upstream release number, and not the pinned tag).
> - Runtime internals live in **compiler-rt**, outside the pinned sparse checkout — flagged `Unverified` above rather than asserted.
> - [Clang — ThreadSanitizer](https://clang.llvm.org/docs/ThreadSanitizer.html) — primary doc.
