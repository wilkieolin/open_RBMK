"""Round-trip and off-grid interpolation check for the A5b MULTICOMPO.

Compares DONJON's k-inf, interpolated from _ACompo with NCR: LINEAR and
solved on a reflective homogeneous cube (rbmk_a5b_sweep.don), against DRAGON's
172-group transport k-inf at the same state:

  grid nodes   A5BSWEEP      vs  A5BTAB  (rbmk_a5b_compo.x2m)
  off-grid     A5BSWEEPOFF   vs  A5BOFF  (rbmk_a5b_offgrid.x2m)
  off-grid     A5BSWEEPCUB   vs  A5BOFF  -- the same states with NCR: CUBIC
  axis decomp  A5BSWEEPAXIS  vs  A5BAXIS (states off-grid in ONE axis only)
  burnup       A5BSWEEPBURN  vs  A5BBURN (off-grid in BURNUP, the rest on grid)

The last three were added 2026-10-02 because LINEAR came out at 30.4 pcm
against a 30 pcm gate.  CUBIC answers "is a better interpolator the fix";
the decomposition answers "which axis is paying", which is the question that
decides whether a grid is widened and where; and the burnup set closes a hole
in the gate itself -- every off-grid point before it held burnup on a node, on
the grounds that burnup does not move on transient timescales, which is true
and beside the point, because the steady state the transient starts FROM is at
10 900 MWd/t, between nodes.  That axis is interpolated in every core
calculation and had never been tested.  It is the largest error of the four.

Nothing here holds an expected value; every number is read from a .result.
"""
import os
import platform
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCH = os.environ.get("DRAGON_ARCH", f"Linux_{platform.machine()}")
DRA = os.path.join(ROOT, "5.1", "Dragon", ARCH)
DON = os.path.join(ROOT, "5.1", "Donjon", ARCH)
NUM = r"([-+]?\d+\.\d+[eE][-+]\d+)"


def rows(path, tag):
    pat = re.compile(rf"{tag}\s+" + r"\s+".join([NUM] * 5))
    out = {}
    with open(path, errors="ignore") as f:
        for line in f:
            m = pat.search(line)
            if m:
                bu, dca, tf, tg, k = (float(x) for x in m.groups())
                out[(round(bu), round(dca, 4), round(tf), round(tg))] = k
    return out


def report(title, don, dra):
    print(title)
    print(f"  {'BU':>6} {'dca':>6} {'TF':>5} {'TG':>4} {'DRAGON':>10} "
          f"{'DONJON':>10} {'delta pcm':>10}")
    worst = 0.0
    for key in sorted(don):
        if key not in dra:
            sys.exit(f"ERROR: no DRAGON reference for {key}")
        kd, kn = dra[key], don[key]
        dp = 1e5 * (1 / kd - 1 / kn)          # reactivity difference
        worst = max(worst, abs(dp))
        print(f"  {key[0]:>6} {key[1]:>6} {key[2]:>5} {key[3]:>4} "
              f"{kd:>10.6f} {kn:>10.6f} {dp:>+10.1f}")
    print(f"  worst |delta| = {worst:.1f} pcm over {len(don)} points\n")
    return worst


sweep = os.path.join(DON, "rbmk_a5b_sweep.don.result")
node = report("GRID NODES (round trip)", rows(sweep, "A5BSWEEP"),
              rows(os.path.join(DRA, "rbmk_a5b_compo.result"), "A5BTAB"))
off = report("OFF-GRID (LINEAR interpolation)", rows(sweep, "A5BSWEEPOFF"),
             rows(os.path.join(DRA, "rbmk_a5b_offgrid.result"), "A5BOFF"))

cub = report("OFF-GRID (CUBIC interpolation)", rows(sweep, "A5BSWEEPCUB"),
             rows(os.path.join(DRA, "rbmk_a5b_offgrid.result"), "A5BOFF"))

# ---- axis decomposition -------------------------------------------------
# Five states at BU 0, each off-grid in at most one axis, so the off-grid
# error can be attributed instead of guessed.  Printed as a table of which
# axes are off the grid rather than as raw coordinates.
# Read from the deck that BUILT the COMPO, never restated here -- a second
# copy of the axis values is a copy that can go stale against a rebuild.
COMPO_DECK = os.path.join(ROOT, "decks", "Dragon", "data", "rbmk_a5b_compo.x2m")
GRID = {}
with open(COMPO_DECK, errors="ignore") as f:
    txt = f.read()
for axis in ("dca", "tf", "tg"):
    m = re.search(rf"CREA '{axis}'\s+<<n\w+>>\s*=([^;]*);", txt)
    if not m:
        sys.exit(f"ERROR: no '{axis}' axis found in {COMPO_DECK}")
    GRID[axis] = [float(v) for v in m.group(1).split()]


def ongrid(axis, v):
    return any(abs(v - g) < 1e-6 for g in GRID[axis])


ax_don = rows(sweep, "A5BSWEEPAXIS")
ax_dra = rows(os.path.join(DRA, "rbmk_a5b_offgrid.result"), "A5BAXIS")
if ax_don and ax_dra:
    print("AXIS DECOMPOSITION at BU 0 (which axis pays for the off-grid error)")
    print(f"  {'dca':>6} {'TF':>6} {'TG':>5}  {'off-grid in':<16} "
          f"{'DRAGON':>10} {'DONJON':>10} {'delta pcm':>10}")
    for key in sorted(ax_don, key=lambda k: (-k[1], -k[2], -k[3])):
        if key not in ax_dra:
            sys.exit(f"ERROR: no DRAGON reference for {key}")
        kd, kn = ax_dra[key], ax_don[key]
        dp = 1e5 * (1 / kd - 1 / kn)
        offs = [n.upper() for n, v in (("dca", key[1]), ("tf", float(key[2])),
                                       ("tg", float(key[3])))
                if not ongrid(n, v)]
        print(f"  {key[1]:>6} {key[2]:>6} {key[3]:>5}  "
              f"{(', '.join(offs) or 'nothing -- on grid'):<16} "
              f"{kd:>10.6f} {kn:>10.6f} {dp:>+10.1f}")
    print()

# ---- burnup off-grid ----------------------------------------------------
# Three depletion points the COMPO did not store as nodes, with DCA/TF/TG on
# the grid, so the whole error belongs to the burnup axis -- the one axis the
# core interpolates in EVERY calculation (10 900 MWd/t) and the one the
# original gate never tested.
bu_don = rows(sweep, "A5BSWEEPBURN")
bu_dra = rows(os.path.join(DRA, "rbmk_a5b_offgrid.result"), "A5BBURN")
bur = 0.0
if bu_don and bu_dra:
    bur = report("BURNUP OFF-GRID (DCA, TF, TG all on the grid)", bu_don, bu_dra)

print(f"GATES: round trip {node:.1f} pcm (<= 10)   "
      f"off-grid LINEAR {off:.1f} pcm (<= 30)   CUBIC {cub:.1f} pcm"
      + (f"   burnup axis {bur:.1f} pcm" if bur else ""))
