#!/usr/bin/env bash
#
# Link the RBMK decks into the DRAGON/DONJON submodule.
#
# The decks are ours; the 5.1 tree is upstream's.  Keeping our files in the
# submodule meant a fresh clone got none of them (the parent pins upstream's
# commit, and a local branch cannot be pushed to the NEA remote).  So decks/ in
# this repo is canonical and this script points the submodule at it.
#
# They are symlinks, not copies.  rdragon does `cp "$CodeDir"/data/<deck> .`
# into its scratch directory, which follows symlinks, so a linked deck runs
# exactly like a real one -- and there is only ever one file to edit.
#
# Idempotent.  Refuses to replace a real file, so it can never eat upstream's
# tree or an uncommitted edit made in the wrong place.
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/env.sh"

SUB="$RBMK_ROOT/5.1"
[ -d "$SUB/Dragon/data" ] || { echo "ERROR: $SUB is not checked out. Run: git submodule update --init" 1>&2; exit 1; }

linked=0 kept=0 stale=0
declare -a excludes=()

link_tree() {                       # link_tree <decks subdir> <submodule subdir>
    local src="$RBMK_ROOT/decks/$1" dst="$SUB/$2"
    local f name target
    mkdir -p "$dst"
    while IFS= read -r -d '' f; do
        name="${f#"$src"/}"
        target="$dst/$name"
        mkdir -p "$(dirname "$target")"
        if [ -L "$target" ]; then
            [ "$(readlink -f "$target")" = "$(readlink -f "$f")" ] || { rm "$target"; ln -s "$f" "$target"; stale=$((stale+1)); continue; }
            kept=$((kept+1))
        elif [ -e "$target" ]; then
            echo "SKIP (real file, not ours): $2/$name" 1>&2
            continue
        else
            ln -s "$f" "$target"; linked=$((linked+1))
        fi
        excludes+=("/$2/$name")
    done < <(find "$src" \( -type f -o -type l \) -print0)
}

link_tree Dragon/data Dragon/data
link_tree Donjon/data Donjon/data

# Keep the submodule's `git status` clean.  .git/info/exclude is not cloned, so
# it has to be written here rather than committed anywhere.
EXCL="$(git -C "$SUB" rev-parse --absolute-git-dir)/info/exclude"
mkdir -p "$(dirname "$EXCL")"
MARK='# >>> rbmk link_decks.sh'
python3 - "$EXCL" "$MARK" <<'PY' "${excludes[@]}"
import sys
path, mark = sys.argv[1], sys.argv[2]
entries = sys.argv[3:]
try:
    body = open(path).read()
except FileNotFoundError:
    body = ""
head, sep, rest = body.partition(mark)
if sep:
    _, _, tail = rest.partition("# <<< rbmk link_decks.sh\n")
    body = head + tail
extra = ["/Njoy2016/", "/libraries/", "/Trivac/_main001", "/Dragon/tmp/",
         "/Dragon/compo/", "/Dragon/macrolib/", "/Dragon/DLIB_99", "/Donjon/_DUMMY", "_DUMMY",
         "__pycache__/", "*.pyc", "*.result", "/Dragon/Linux_*/", "/Donjon/Linux_*/"]
block = mark + "\n" + "\n".join(extra + sorted(entries)) + "\n# <<< rbmk link_decks.sh\n"
open(path, "w").write(body.rstrip("\n") + ("\n" if body.strip() else "") + block)
PY

echo "decks linked: $linked new, $kept already correct, $stale repointed"
echo "submodule status:"
git -C "$SUB" status --porcelain | head || true
