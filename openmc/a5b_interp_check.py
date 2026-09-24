"""Round-trip and off-grid interpolation check for the A5b MULTICOMPO.

Compares DONJON's k-inf, interpolated from _ACompo with NCR: LINEAR and
solved on a reflective homogeneous cube (rbmk_a5b_sweep.don), against DRAGON's
172-group transport k-inf at the same state:

  grid nodes   A5BSWEEP     vs  A5BTAB  (rbmk_a5b_compo.x2m)
  off-grid     A5BSWEEPOFF  vs  A5BOFF  (rbmk_a5b_offgrid.x2m)

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


sweep = os.path.join(DON, "rbmk_a5b_sweep.result")
node = report("GRID NODES (round trip)", rows(sweep, "A5BSWEEP"),
              rows(os.path.join(DRA, "rbmk_a5b_compo.result"), "A5BTAB"))
off = report("OFF-GRID (LINEAR interpolation)", rows(sweep, "A5BSWEEPOFF"),
             rows(os.path.join(DRA, "rbmk_a5b_offgrid.result"), "A5BOFF"))
