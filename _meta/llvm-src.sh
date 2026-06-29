#!/usr/bin/env bash
# llvm-src.sh — populate / free / bump the .llvm-project source submodule.
#
# The submodule is registered as a tiny committed pointer; the working tree is
# opt-in. This helper populates it SHALLOW + SPARSE (only the dirs the vault
# cites) at the tag pinned in _meta/llvm-version.md, so a tier-1 source check is
# cheap. See CLAUDE.md "Inspecting LLVM source" and _meta/llvm-version.md.
#
# WARNING: this vault lives in iCloud. Populating lands source files in the
# synced folder — prefer running on a non-iCloud clone, or `free` when done.
#
# Usage:
#   _meta/llvm-src.sh init   # shallow+sparse checkout at the pinned tag
#   _meta/llvm-src.sh free   # deinit (reclaim disk; pointer stays committed)
#   _meta/llvm-src.sh bump <llvmorg-XX.Y.Z>   # move pointer to a new release
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SUB=".llvm-project"
SPARSE=(llvm/lib llvm/include mlir/lib mlir/include clang/lib)
cd "$ROOT"

tag() { grep -E '^llvm_git_tag:' _meta/llvm-version.md | head -1 | sed -E 's/.*"(.*)".*/\1/'; }

case "${1:-}" in
  init)
    echo "Populating $SUB (shallow + sparse) at $(tag) ..."
    git submodule update --init --depth 1 "$SUB"
    git -C "$SUB" sparse-checkout init --cone
    git -C "$SUB" sparse-checkout set "${SPARSE[@]}"
    echo "Done. Sparse dirs: ${SPARSE[*]}"
    ;;
  free)
    git submodule deinit -f "$SUB"
    echo "Deinitialized $SUB (committed pointer unchanged)."
    ;;
  bump)
    NEW="${2:?usage: llvm-src.sh bump <llvmorg-XX.Y.Z>}"
    git submodule update --init --depth 1 "$SUB"
    git -C "$SUB" fetch --depth 1 origin "tag" "$NEW"
    git -C "$SUB" checkout "$NEW"
    echo "Moved $SUB to $NEW. Now update _meta/llvm-version.md (llvm_stable,"
    echo "llvm_git_tag, as_of), re-verify its table, and commit pointer + note together."
    ;;
  *)
    echo "usage: $0 {init|free|bump <tag>}"; exit 2 ;;
esac
