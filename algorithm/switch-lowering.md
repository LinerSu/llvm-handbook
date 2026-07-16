---
title: Switch Lowering (binary search, jump tables, and a DP)
facet: algorithm
stage: codegen
ecosystem: [general]
concepts: [control-flow, code-generation]
book: "Dragon Book (Aho/Lam/Sethi/Ullman, 2e) §6.8"
docs: "doxygen — SwitchLoweringUtils ↗ https://llvm.org/doxygen/SwitchLoweringUtils_8h_source.html"
prereqs: [control-flow-graph]
related: [simplifycfg, instruction-selection, code-generation-overview]
tags: [kind/algorithm, status/verified, version-sensitive]
status: verified
verified_on: 2026-07-16
---

# Switch Lowering (binary search, jump tables, and a DP)

> 🧭 **Algorithm** · `algorithm · codegen · general` · Index [[LLVM.MOC]] · see also [[dragon-book-ch6.MOC|Dragon Ch.6]]
> **Powers:** `LowerSwitch`, SelectionDAG switch lowering, and the lookup-table half of [[simplifycfg|SimplifyCFG]]
> **Prerequisites:** [[control-flow-graph]]

> [!abstract] Chapter map
> `switch (x)` has no hardware instruction behind it. Someone has to turn it into branches — and that someone reaches for **binary search trees**, **dynamic programming**, **prefix sums**, and **bit masks**, all in one file. This is the densest concentration of undergraduate data structures anywhere in LLVM, and the punchline is that **the same sorted array becomes three different structures depending on what you're optimizing**.

---

## 1. The problem

> [!note] Definition
> Given `switch (v) { case k₁: …; case k₂: …; default: … }`, emit code selecting the right target. The candidate lowerings:
>
> | Lowering | Shape | Good when |
> |---|---|---|
> | **Linear compares** | `if (v==k₁) … else if (v==k₂) …` | very few cases |
> | **Binary search tree** | compare against a pivot, recurse | cases are sparse |
> | **Jump table** | `goto tbl[v - lo]` | cases are **dense** |
> | **Bit test** | `(mask >> (v-lo)) & 1` | few destinations, range ≤ one word |

Everything downstream follows from one preprocessing step: **sort the cases, then merge adjacent cases that share a destination into ranges**. LLVM does this with the standard two-cursor compaction idiom — a read cursor and a write cursor over one array, merging when `next == current + 1 && sameDest`. After that, the switch *is* a sorted array of clusters, and the rest is a question of what structure to impose on it.

## 2. Binary search — and the pivot that isn't optimal

> [!info] `LowerSwitch`: median by count
> The utility pass that exists for targets which can't select `switch` at all builds a **balanced BST over the sorted clusters**, recursing on index ranges (the sorted array *is* the tree — no nodes are allocated). Its entire pivot heuristic is:
> ```cpp
> unsigned Mid = Size / 2;
> ```
> Split by **number of clusters**. Not by probability. Branch weights are discarded outright — the merge loop carries a bare `// FIXME: Combine branch weights.`

> [!tip] Two refinements the textbook BST doesn't have
> - **Bound threading.** Textbook BST emits a comparison per leaf. LLVM threads the known `[LowerBound, UpperBound]` down the recursion, and when a cluster exactly fills its bounds it emits **zero** comparisons and jumps straight to the destination. A two-sided range check degrades to one-sided whenever a bound is already known.
> - **The unsigned-bias trick.** A range check `lo <= v && v <= hi` becomes the single unsigned compare `(v - lo) <=u (hi - lo)` — one subtract, one branch. Worth internalizing; it shows up far outside compilers.

> [!warning] The same tree, built two different ways
> SelectionDAG — the path you actually get at `-O1+` — builds its BST by **probability bisection**, citing:
> > *"Compute information to balance the tree based on branch probabilities to create a near-optimal (in terms of search time given key frequency) binary search tree. See e.g. Kurt **Mehlhorn** 'Nearly Optimal Binary Search Trees' (1975)."*
>
> Two pointers walk toward each other, each step extending the lighter side, so the split lands where the *weight* is balanced rather than where the *count* is. Zero-probability clusters are distributed by parity so they don't all pile onto one side.
>
> So: `Mid = Size / 2` and Mehlhorn weight-balancing sit in the same codebase, over the same sorted array, building the same data structure. **The data structure isn't what differs — the objective function is.** `LowerSwitch` is a correctness utility and doesn't care; SelectionDAG is the performance path and does.

## 3. The dynamic program

Which spans of the sorted array should become jump tables? That's a partitioning problem, and LLVM solves it **exactly**, with a textbook DP:

> [!info] The recurrence
> > *"Split Clusters into minimum number of dense partitions. The algorithm uses the same idea as **Kannan & Proebsting** 'Correction to "Producing Good Code for the Case Statement"' (1994), but builds the MinPartitions array in **reverse order** to make it easier to reconstruct the partitions in ascending order."*
>
> `MinPartitions[i]` = the fewest dense partitions covering `Clusters[i..N-1]`. Baseline: put `Clusters[i]` alone. Then for each `j > i`, if `Clusters[i..j]` is dense enough to be a jump table, try `1 + MinPartitions[j+1]`. `LastElement[]` holds the standard DP back-pointers for reconstruction.

> [!tip] Why it's O(n²) and not O(n³)
> The inner probe asks "how many cases are in `Clusters[i..j]`?" — which would be an O(n) scan, making the whole thing cubic. LLVM precomputes a **prefix-sum array**, so the probe is a single subtraction. Prefix sums are what keep the DP quadratic. This is the most transferable idea in the file.

> [!note] The density test — actual constants
> ```cpp
> return (OptForSize || Range <= MaxJumpTableSize) &&
>        (NumCases * 100 >= Range * MinDensity);
> ```
> A **density ratio**, integer-scaled by 100 to avoid floating point: a span qualifies when `NumCases / Range ≥ MinDensity%`. `MinDensity` defaults to **10** normally and **40** under `-Os`/`-Oz` — a sparse table is fast but costs bytes, so optimizing for size demands four times the density. Minimum **4** entries before a table is considered at all. `Range` is clamped so that `* 100` cannot overflow.

> [!example]- Two deviations from Kannan–Proebsting (click to expand)
> - **Transposed for convenience.** K&P index prefixes; LLVM indexes **suffixes**, purely so that walking the back-pointers emits partitions in ascending order. Same recurrence, flipped.
> - **Tie-breaking is a pure LLVM addition.** K&P minimizes partition count and stops. LLVM adds a lexicographic second key — among equally-optimal partitionings, prefer the one yielding more jump tables — with the twist that a single comparison scores *better* than a table. Textbook optimality has no opinion here; a real compiler must.

> [!info] The bit-test DP — where a domain fact collapses the complexity
> Bit tests get a **second** DP with the same suffix recurrence, but the inner loop is clamped:
> ```cpp
> // Note: the search is limited by BitWidth, reducing time complexity.
> for (int64_t j = std::min(N - 1, i + BitWidth - 1); j > i; --j)
> ```
> A partition wider than a machine word can never fit in a mask, so searching further is pointless. **O(N · BitWidth) — effectively linear.** A hardware constraint turns a quadratic DP into a linear one, which is the kind of move only a domain-specific implementation gets to make.

## 4. The pipeline — it's not a choice, it's a sequence

> [!warning] There is no "pick JT vs bit test vs BST" function
> The lowering is a **pipeline that rewrites the cluster array in place**, each phase compacting it so the next sees a smaller problem:
>
> 1. **sort + rangeify** — merge adjacent same-destination cases
> 2. **peel** the dominant case if its probability ≥ **66%**
> 3. **jump-table DP** — collapse qualifying spans into single `CC_JumpTable` clusters
> 4. **bit-test DP** — fill gaps in what's left
> 5. **BST** over whatever clusters survive (Mehlhorn-split, if more than 3 remain)
>
> So the **BST is the residual structure**, built over a mix of ordinary ranges, jump tables, and bit tests as leaves. A jump table isn't an alternative to the tree — it's a *node in* it.

## 5. The delta

> [!summary] The one thing to remember
> One sorted array of case clusters, three structures, and the choice is driven entirely by the **objective**, not the data:
>
> | | `LowerSwitch` | SelectionDAG | [[simplifycfg|SimplifyCFG]] |
> |---|---|---|---|
> | Partition | — | **exact O(n²) DP** | greedy density test |
> | Tree | BST, **median by count** | BST, **Mehlhorn weight-balanced** | — |
> | Recursion | true recursion | explicit LIFO worklist | — |
> | Density | — | 10% / 40%, target-tunable | **40% hardcoded** |
>
> And note the pleasing inconsistency: LLVM pays for an **exact** DP to partition jump tables, but takes Mehlhorn's linear-time **approximation** for the BST — even though Knuth's exact optimal-BST DP is also O(n²) and would have been affordable. The partitioning decision is discrete and structural (get it wrong, emit a whole extra table); the tree shape only costs you an average compare or two. Effort follows consequence, not tractability.

> [!quote] Sources & confidence
> - **Source (tier 1, verified at the version in [[llvm-version]]):** [`llvm/lib/Transforms/Utils/LowerSwitch.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Utils/LowerSwitch.cpp) (`Clusterify`, `SwitchConvert`, the `Mid = Size / 2` pivot, bound threading) · [`llvm/lib/CodeGen/SwitchLoweringUtils.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/CodeGen/SwitchLoweringUtils.cpp) (`findJumpTables` DP + prefix sums, `findBitTestClusters`, `computeSplitWorkItemInfo`) · [`llvm/include/llvm/CodeGen/SwitchLoweringUtils.h`](https://github.com/llvm/llvm-project/blob/main/llvm/include/llvm/CodeGen/SwitchLoweringUtils.h) (the Mehlhorn comment) · [`llvm/lib/CodeGen/TargetLoweringBase.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/CodeGen/TargetLoweringBase.cpp) (`isSuitableForJumpTable`, the density constants). Code and comments quoted above are verbatim.
> - Kannan & Proebsting, *Correction to "Producing Good Code for the Case Statement"*, SP&E 1994 — cited by name in LLVM's DP comment.
> - Mehlhorn, *Nearly Optimal Binary Search Trees*, Acta Informatica 1975 — cited by name in LLVM's BST-split comment.
> - Bentley & Sedgewick / Hennessy, *Producing Good Code for the Case Statement* — the lineage the above corrects.
>
> > [!danger] Unverified — citations confirmed, papers not read
> > What is verified is that **LLVM cites** Kannan–Proebsting and Mehlhorn at these exact places, and what the shipped code does. Whether each implementation faithfully matches its cited paper's variant has **not** been checked against the papers themselves. LLVM's DP comment also points at `arxiv.org/pdf/1910.02351v2`; the existence of that reference in the comment is verified, its contents are not. Treat the attributions as LLVM's claims, not as this vault's independent confirmation.
>
> > [!warning] Target overrides not surveyed
> > The density/entry constants above are the **generic `TargetLoweringBase` defaults**. Individual targets override them (`setMinimumJumpTableEntries`, `setMaximumJumpTableSize`, …), so the effective numbers on AArch64 or X86 may differ. Tagged `version-sensitive` accordingly.
