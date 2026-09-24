#!/usr/bin/env bash
#
# Take the decompressed draglibs out of the `libraries` submodule.
#
# DRAGON's stock .access scripts gunzip a draglib IN PLACE, inside the
# submodule.  The result is that the submodule dirties itself on the first run
# of any deck -- the .gz disappears and a multi-hundred-MB uncompressed file
# appears in its place -- so `git submodule update` then fights the working
# tree and a clean clone stops being clean the moment you use it.
#
# decks/common/dlib99.access decompresses into $DRAGLIB_CACHE instead.  This
# script migrates a tree that was already dirtied by the old behaviour: it
# moves each decompressed library into the cache and restores the tracked .gz
# from the object store (an exact restore -- the blob is unchanged, so this is
# not a re-gzip).
#
# Idempotent; safe to run on a clean clone, where it finds nothing to do.
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/env.sh"

LIB="$RBMK_ROOT/libraries"
[ -d "$LIB/l_endian" ] || { echo "ERROR: $LIB is not checked out. Run: git submodule update --init" 1>&2; exit 1; }
mkdir -p "$DRAGLIB_CACHE"

moved=0 quarantined=0
QDIR="$DRAGLIB_CACHE/unprovenanced"

for d in l_endian b_endian; do
    [ -d "$LIB/$d" ] || continue
    for f in "$LIB/$d"/*; do
        case "$f" in *.gz) continue ;; esac
        [ -f "$f" ] || continue
        name=$(basename "$f")
        # Only touch files that are a decompressed form of something the
        # submodule tracks; anything else is the user's own and stays put.
        git -C "$LIB" ls-files --error-unmatch "$d/$name.gz" >/dev/null 2>&1 || continue

        # Restore the .gz first so we have something to compare against.
        git -C "$LIB" checkout -- "$d/$name.gz" 2>/dev/null || true

        if [ -f "$LIB/$d/$name.gz" ] && gunzip -c "$LIB/$d/$name.gz" | cmp -s - "$f"; then
            # Identical to the pinned library: redundant, and the content-addressed
            # cache will regenerate it on demand.
            echo "matches the pinned .gz, removing: $d/$name"
            rm -f "$f"
            moved=$((moved+1))
        else
            # NOT the pinned library.  This is how 87 pcm went unnoticed: a
            # decompressed leftover from an earlier `libraries` revision sat in
            # the submodule and every .access run picked it up in preference to
            # the .gz beside it.  Keep it -- earlier results were produced with
            # it and may need reproducing -- but somewhere it can never be
            # mistaken for the pinned data.
            mkdir -p "$QDIR"
            echo "!! $d/$name does NOT match the pinned .gz -- quarantining" 1>&2
            mv "$f" "$QDIR/$name.$(md5sum "$f" | cut -c1-12)"
            quarantined=$((quarantined+1))
        fi
    done
done

# Restore any .gz the in-place gunzip deleted.  These come straight back out of
# the submodule's object store, so they are byte-identical to what was cloned.
deleted=$(git -C "$LIB" diff --name-only --diff-filter=D -- '*.gz' || true)
if [ -n "$deleted" ]; then
    echo "restoring $(echo "$deleted" | wc -l) deleted .gz from the object store"
    # shellcheck disable=SC2086
    git -C "$LIB" checkout -- $deleted
fi

# Leftovers from upstream decks that decompress their own HDF5 inputs in place.
# Harmless, but they should not show up as submodule changes.
EXCL="$(git -C "$LIB" rev-parse --absolute-git-dir)/info/exclude"
mkdir -p "$(dirname "$EXCL")"
MARK='# >>> rbmk tidy_libraries.sh'
python3 - "$EXCL" "$MARK" <<'PY'
import sys
path, mark = sys.argv[1], sys.argv[2]
try:
    body = open(path).read()
except FileNotFoundError:
    body = ""
head, sep, rest = body.partition(mark)
if sep:
    _, _, tail = rest.partition("# <<< rbmk tidy_libraries.sh\n")
    body = head + tail
block = mark + "\n" + "\n".join([
    "/hdf5/*.h5",
    "/l_endian/draglib*_v5p1",
    "/b_endian/draglib*_v5p1",
]) + "\n# <<< rbmk tidy_libraries.sh\n"
open(path, "w").write(body.rstrip("\n") + ("\n" if body.strip() else "") + block)
PY

echo
echo "$moved decompressed librar$([ "$moved" = 1 ] && echo y || echo ies) removed as redundant"
if [ "$quarantined" != 0 ]; then
    echo "$quarantined MOVED TO $QDIR -- these are not the pinned data:"
    ls -la "$QDIR"
    echo
    echo "Results produced against a quarantined library are not reproducible from"
    echo "a clean clone.  See the draglib note in PROGRESS.md."
fi
echo "submodule status:"
git -C "$LIB" status --porcelain | head || true
