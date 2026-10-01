#!/usr/bin/env bash
#
# Apply our local changes to the vendored DRAGON5/DONJON5 tree.
#
# WHY THIS EXISTS.  `5.1/` is a submodule pinned to an upstream commit we
# cannot push to, and it is gitignored here, so a source change made directly
# in it is invisible to this repo and is lost by a fresh clone or a
# `git submodule update --force`.  The patches in patches/ are the canonical
# copy; this script puts them back, and `tools/bootstrap.sh` calls it.
#
# Idempotent: a patch already applied is detected and skipped, not reversed.
# Rebuilding afterwards is the caller's job (./build_monorepo.sh, or just
# `make` in 5.1/Donjon/src, which is incremental).
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/env.sh"

SUB="$RBMK_ROOT/5.1"
[ -d "$SUB/Donjon/src" ] || { echo "ERROR: $SUB is not checked out." 1>&2; exit 1; }

applied=0 already=0
for p in "$RBMK_ROOT"/patches/*.patch ; do
    [ -e "$p" ] || continue
    name=$(basename "$p")
    if patch -p1 -d "$SUB" --dry-run --silent -R < "$p" >/dev/null 2>&1 ; then
        echo "already applied: $name"
        already=$((already + 1))
    elif patch -p1 -d "$SUB" --dry-run --silent < "$p" >/dev/null 2>&1 ; then
        patch -p1 -d "$SUB" --silent < "$p"
        echo "applied:         $name"
        applied=$((applied + 1))
    else
        echo "ERROR: $name applies cleanly neither forward nor in reverse." 1>&2
        echo "       The upstream file has moved under it; re-derive the patch." 1>&2
        exit 1
    fi
done
echo "patches: $applied applied, $already already present"
