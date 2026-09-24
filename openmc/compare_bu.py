"""
Void coefficient vs burnup: OpenMC depletion against the DRAGON A5 deck.

DRAGON values are read off the run log of rbmk_a5_void.x2m (172-group
ENDF/B-VIII.1).  OpenMC is continuous energy on the same evaluation with bound
c_H_in_H2O.

NOTE (2026-09-23): the DRAGON numbers below are the PRE-FIX ones, taken while
rbmk_proc/RbmkLib.c2m still declared free-gas H1.  That bug is fixed
(H1_H2O), and the current DRAGON void curve -- on a 7-point density axis, not
2 -- lives in the A5b COMPO run and is tabulated in PROGRESS.md.  This script
is kept for the historical comparison; do not read the DRAGON column here as
the current model.
"""
import json
import os

rho = lambda k: 1 - 1 / k

# DRAGON, from /tmp/a5.log  -- BU in MWd/t
DRAGON = {
    0:     (1.312816, 1.314234),
    2000:  (1.236771, 1.238341),
    5000:  (1.185538, 1.185391),
    10000: (1.098654, 1.102323),
    15000: (1.011790, 1.021979),
    20000: (0.9282272, 0.9453484),
}
# Delayed-neutron fraction, MEASURED from DLIB_99 NDEL 6 via the A5b COMPO
# (5.1/Donjon/data/rbmk_a5b_beta.don), not assumed.  It falls 31 % over life as
# Pu-239 (beta 0.002254) displaces U-235 (beta 0.006524).  Cross-checked at BU=0
# against OpenMC prompt-vs-total, 0.006856 +/- 0.000162 -- agreement to -0.5 %.
# The 0.0048 this project assumed until 2026-09-23 is a DISCHARGE number: right
# to 2 % at 20 MWd/t, wrong by +42 % at fresh fuel.  Using it flat understated
# the growth of the void worth in dollars over life.
BETA_BU = {
    0:     0.006824,
    2000:  0.006361,
    5000:  0.005877,
    10000: 0.005358,
    15000: 0.004985,
    20000: 0.004680,
}


def main(path="branch_results81.json"):
    if not os.path.exists(path):
        print("no depletion branch results yet")
        return
    res = json.load(open(path))
    by = {(int(round(r["bu"] * 1000)), r["dca"]): (r["k"], r["sd"])
          for r in res}

    print("FULL-VOID REACTIVITY vs BURNUP  (dca 0.72 -> 0.02)")
    print("=" * 74)
    print(f"{'BU':>7} | {'k-inf nominal':>21} | {'full-void reactivity, pcm':>36}")
    print(f"{'MWd/t':>7} | {'OpenMC':>12}{'DRAGON':>9} | "
          f"{'OpenMC':>17}{'DRAGON':>9}{'ratio':>8}")
    print("-" * 74)
    for bu in sorted(DRAGON):
        if (bu, 0.72) not in by or (bu, 0.02) not in by:
            continue
        kn, sn = by[(bu, 0.72)]
        kv, sv = by[(bu, 0.02)]
        o = 1e5 * (rho(kv) - rho(kn))
        so = 1e5 * ((sv / kv**2) ** 2 + (sn / kn**2) ** 2) ** 0.5
        dn, dv = DRAGON[bu]
        d = 1e5 * (rho(dv) - rho(dn))
        ratio = f"{o/d:>7.1f}x" if abs(d) > 20 else "    n/a"
        print(f"{bu:>7d} | {kn:>9.5f}+/-{sn:.5f}{dn:>9.5f} | "
              f"{o:>+12.0f} +/-{so:<3.0f}{d:>+9.0f}{ratio:>8}")
    print("-" * 74)
    print("\nin dollars, using the measured beta(BU) curve:")
    for bu in sorted(DRAGON):
        if (bu, 0.02) not in by:
            continue
        kn, _ = by[(bu, 0.72)]; kv, _ = by[(bu, 0.02)]
        o = rho(kv) - rho(kn)
        dn, dv = DRAGON[bu]
        d = rho(dv) - rho(dn)
        b = BETA_BU[bu]
        print(f"  BU {bu:>6d} MWd/t   beta {b:.6f}   "
              f"OpenMC {o/b:>+6.2f} $   DRAGON {d/b:>+6.2f} $")


if __name__ == "__main__":
    main()
