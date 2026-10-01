#!/usr/bin/env bash
#
# Verify the THM: per-channel inlet velocity patch
# (patches/0001-THM-per-channel-inlet-velocity.patch).
#
# Three things have to hold, and the deck can only assert the first two:
#
#   1. a scalar SPEED and the same number given through CHAN agree exactly
#      -- the patch is transparent when the new form is not used;
#   2. a graded CHAN list changes the answer at all;
#   3. and the ORDER is right: with velocities 4 / 6 / 10 / 12 m/s the fuel
#      temperature must fall monotonically from channel 1 to channel 4.
#
# (3) is what distinguishes "the vector reached the per-channel driver" from
# "the vector was averaged somewhere and the mean happened to move", and it
# needs the per-channel P-VALUE block out of the listing, so it lives here.
#
# The separate regression -- that upstream's channel_mphy.x2m is byte-for-byte
# unchanged outside timing lines -- is run by tools/thm_chan_regress.sh.
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/env.sh"

DON="$RBMK_ROOT/5.1/Donjon"
R="$DON/Linux_aarch64/rbmk_thm_chan.result"

"$RBMK_ROOT/tools/link_decks.sh" >/dev/null 2>&1
rm -f "$R"
( cd "$DON" && ./rdonjon rbmk_thm_chan.x2m ) >/dev/null 2>&1

python3 - "$R" <<'PYEOF'
import re, sys
t = open(sys.argv[1], "rb").read().decode("latin1").splitlines()

echo = [l for l in t if l.startswith(">|") and "CHANTEST" in l]
for l in echo:
    # CLE-2000 pads its echo lines to a fixed width and appends |>NNNN
    print("  " + re.sub(r"\s*\|>\d*\s*$", "", l[2:]).rstrip())
fails = [l for l in echo if "FAIL" in l]

# per-channel fuel temperature, as the fuel map carries it back: 48 values =
# 4 channels x 12 bundles, channel-major in the order RESPFM.f:74-82 finds them
blocks = []
for n, l in enumerate(t):
    if "CONTENT OF BLOCK 'P-VALUE" not in l:
        continue
    vals = []
    for m in t[n + 1:n + 20]:
        if "CONTENT OF BLOCK" in m or "DRVUTL" in m:
            break
        vals += [x for x in m.split() if re.match(r"^[-+0-9.]+E[-+]\d+$", x)]
    if len(vals) == 48:
        v = [float(x) for x in vals]
        blocks.append([sum(v[c::4]) / 12.0 for c in range(4)])

if len(blocks) != 2:
    print(f"  FAIL: expected 2 per-channel P-VALUE blocks, found {len(blocks)}")
    sys.exit(1)
flat, grad = blocks
print(f"\n  scalar SPEED        mean fuel T per channel: "
      + "  ".join(f"{x:8.3f}" for x in flat))
print(f"  CHAN 4 6 10 12 m/s  mean fuel T per channel: "
      + "  ".join(f"{x:8.3f}" for x in grad))

spread = max(flat) - min(flat)
if spread > 0.05:
    print(f"  FAIL: scalar case is not uniform across channels, spread {spread:.4f} K")
    fails.append("spread")
else:
    print(f"  PASS: scalar case uniform across channels to {spread:.4f} K")

if all(a > b for a, b in zip(grad, grad[1:])):
    print(f"  PASS: graded case falls monotonically, "
          f"{grad[0] - grad[-1]:.2f} K from slowest channel to fastest")
else:
    print("  FAIL: graded case is not monotonic in velocity")
    fails.append("monotonic")

print("\n" + ("THM CHAN CHECK FAILED" if fails else "THM CHAN CHECK PASSED"))
sys.exit(1 if fails else 0)
PYEOF
