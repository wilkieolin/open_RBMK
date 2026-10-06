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
# HOW IT DECIDES WHAT IS APPLIED.  It used to dry-run each patch in reverse,
# one at a time.  That breaks as soon as two patches touch neighbouring lines
# of one file (0004 and 0005 both edit THM.f near 0001's hunks): a later
# patch changes an earlier one's context, the earlier one no longer reverses,
# and a fully patched tree is reported as damaged.  So instead, for every file
# any patch touches, it rebuilds the whole chain of states from upstream's
# pristine copy (`git -C 5.1 show HEAD:<file>`) -- pristine, after patch 1,
# after patch 2, ... -- and matches the working file against that chain.
# A match says exactly which prefix of the patches is present; the file is
# then brought to the end of the chain.  A file that matches NO state has been
# edited outside the patches, and the script stops rather than overwrite it.
#
# Idempotent.  Rebuilding afterwards is the caller's job (./build_monorepo.sh,
# or just `make` in 5.1/Donjon/src, which is incremental).
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/env.sh"

SUB="$RBMK_ROOT/5.1"
[ -d "$SUB/Donjon/src" ] || { echo "ERROR: $SUB is not checked out." 1>&2; exit 1; }

python3 - "$SUB" "$RBMK_ROOT/patches" <<'PYEOF'
import glob, os, re, shutil, subprocess, sys, tempfile
sub, pdir = sys.argv[1], sys.argv[2]
patches = sorted(glob.glob(os.path.join(pdir, "*.patch")))
touched = {}                       # file -> [patches that touch it, in order]
for p in patches:
    for f in re.findall(r"^\+\+\+ b/(\S+)", open(p).read(), re.M):
        touched.setdefault(f, []).append(p)

def pristine(f):
    return subprocess.run(["git", "-C", sub, "show", f"HEAD:{f}"],
                          capture_output=True, check=True).stdout

work = tempfile.mkdtemp()
try:
    changed = 0
    for f, plist in touched.items():
        # the chain of states this file passes through
        chain = [pristine(f)]
        for p in plist:
            d = os.path.join(work, "t")
            shutil.rmtree(d, ignore_errors=True)
            os.makedirs(os.path.dirname(os.path.join(d, f)))
            open(os.path.join(d, f), "wb").write(chain[-1])
            # filter the patch down to this one file's sections
            txt = open(p).read()
            parts = re.split(r"(?m)^(?=--- a/)", txt)
            mine = "".join(x for x in parts if x.startswith(f"--- a/{f}\n"))
            r = subprocess.run(["patch", "-s", "-p1", "-d", d],
                               input=mine.encode(), capture_output=True)
            if r.returncode:
                sys.exit(f"ERROR: {os.path.basename(p)} does not apply to {f} "
                         f"after its predecessors; re-derive it.\n{r.stdout.decode()}")
            chain.append(open(os.path.join(d, f), "rb").read())
        cur = open(os.path.join(sub, f), "rb").read()
        if cur not in chain:
            sys.exit(f"ERROR: {f} matches no state of the patch chain -- it has "
                     "been edited outside patches/.  Not touching it.")
        k = chain.index(cur)
        if k == len(chain) - 1:
            print(f"up to date:      {f}  ({len(plist)} patch(es))")
        else:
            open(os.path.join(sub, f), "wb").write(chain[-1])
            changed += 1
            print(f"patched:         {f}  ("
                  + ", ".join(os.path.basename(p)[:4] for p in plist[k:]) + ")")
    print(f"patches: {len(patches)} in patches/, {len(touched)} files, "
          f"{changed} brought up to date")
finally:
    shutil.rmtree(work)
PYEOF
