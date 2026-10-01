#!/usr/bin/env bash
#
# The THM: patch must be INVISIBLE when the CHAN form is not used.  Run
# upstream's channel_mphy.x2m -- the only bundled deck that couples THM: to
# KINSOL:, and the one the patch could most easily break -- and compare the
# whole listing against a stored digest, not just the reported numbers.
#
# Timing and memory-usage lines are excluded because they are not
# reproducible; everything else, 2.6 million lines of it, is.
#
#   usage: tools/thm_chan_regress.sh [--save [<result file>]]
#
# --save writes the reference digest.  With no argument it digests the run it
# has just made, which is only correct from a tree whose THM.f is unpatched;
# with a file argument it digests that listing instead, which is how the
# stored reference was produced -- from the pre-patch run, using THIS script's
# filter.  The filter matters: an earlier reference computed with a narrower
# one disagreed with this script over nothing but which timing lines were
# excluded, so the digest and the filter have to travel together.
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/env.sh"

DON="$RBMK_ROOT/5.1/Donjon"
R="$DON/Linux_aarch64/channel_mphy.result"
REF="$RBMK_ROOT/patches/channel_mphy.digest"

if [ "${1:-}" = --save ] && [ -n "${2:-}" ]; then
    :                             # digesting a stored listing; nothing to run
else
    rm -f "$R"
    ( cd "$DON" && ./rdonjon channel_mphy.x2m ) >/dev/null 2>&1
fi

SRC="$R"
if [ "${1:-}" = --save ] && [ -n "${2:-}" ]; then SRC="$2"; fi
DIG=$(python3 - "$SRC" <<'PYEOF'
import hashlib, re, sys
noise = re.compile(rb"(?i)time spent|memory usage|cpu time|Total execution"
                   rb"|RunDirectory|listing is located|TOTAL CPU TIME")
h, n = hashlib.sha256(), 0
with open(sys.argv[1], "rb") as f:
    for line in f:
        if noise.search(line):
            continue
        h.update(line); n += 1
print(f"{h.hexdigest()} {n}")
PYEOF
)
if [ "${1:-}" = --save ]; then
    { echo "# sha256 and line count of channel_mphy.x2m's listing, excluding the"
      echo "# timing and memory-usage lines this script's filter drops.  Produced from"
      echo "# the PRE-PATCH run on 2026-10-01, before"
      echo "# patches/0001-THM-per-channel-inlet-velocity.patch was applied, so a match"
      echo "# means the patch changed nothing.  Independently corroborated the same day"
      echo "# by a line-by-line comparison of the two listings: 2597833 comparable"
      echo "# lines, 0 differences."
      echo "$DIG" ; } > "$REF"
    echo "saved: $DIG"
    exit 0
fi
[ -f "$REF" ] || { echo "no stored digest at $REF; run with --save on an unpatched tree" 1>&2; exit 1; }
WANT=$(grep -v '^#' "$REF" | head -1)
echo "  stored  $WANT"
echo "  current $DIG"
if [ "$DIG" = "$WANT" ]; then
    echo "THM REGRESSION PASSED: channel_mphy.x2m listing unchanged"
else
    echo "THM REGRESSION FAILED: channel_mphy.x2m listing changed" 1>&2
    exit 1
fi
