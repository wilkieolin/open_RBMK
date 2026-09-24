"""
Compare the independent OpenMC cross-check against the DRAGON5 A3/A5 decks.

DRAGON reference values are read off the run logs of rbmk_cell_a3.x2m and
rbmk_a5_void.x2m (172-group ENDF/B-VIII.1 draglib, CP/ASM + FLU: TYPE K).
OpenMC runs the same cell in continuous energy.  Two OpenMC libraries are
used on purpose: ENDF/B-VIII.1 matches DRAGON's data, so that comparison
isolates the method; ENDF/B-VIII.0 then bounds the data sensitivity.
"""
import glob, json, os
import numpy as np
import openmc

DRAGON_K = {0: 1.312816, 500: 1.259013, 2000: 1.236771, 5000: 1.185538,
            10000: 1.098654, 15000: 1.011790, 20000: 0.9282272}
DRAGON_BR = {
    (0, 0.35): 1.316728,     (0, 0.02): 1.314234,
    (500, 0.35): 1.262974,   (500, 0.02): 1.262075,
    (2000, 0.35): 1.239869,  (2000, 0.02): 1.238341,
    (5000, 0.35): 1.187345,  (5000, 0.02): 1.185391,
    (10000, 0.35): 1.101068, (10000, 0.02): 1.102323,
    (15000, 0.35): 1.016252, (15000, 0.02): 1.021979,
    (20000, 0.35): 0.9350131,(20000, 0.02): 0.9453484,
}
VOIDPC = {0.72: 0.0, 0.35: 51.39, 0.02: 97.22}
DENS = (0.72, 0.35, 0.02)

rho  = lambda k: 1.0 - 1.0 / k
pcm  = lambda k, kr: 1e5 * (rho(k) - rho(kr))
srho = lambda k, s: s / k**2          # sigma on rho


def read_sweep(prefix):
    out = {}
    for d in DENS:
        sps = sorted(glob.glob(f"{prefix}_d{d:g}/statepoint.*.h5"),
                     key=lambda p: int(p.split(".")[-2]))
        if sps:
            with openmc.StatePoint(sps[-1]) as s:
                out[d] = (s.keff.nominal_value, s.keff.std_dev)
    return out


def fresh(prefix, label):
    sw = read_sweep(prefix)
    if not sw:
        print(f"[{label}] fresh-fuel sweep: no results yet\n"); return
    print("=" * 76)
    print(f"FRESH FUEL (BU = 0)   OpenMC {label}  vs  DRAGON ENDF/B-VIII.1")
    print("=" * 76)
    print(f"{'dca':>5}{'void%':>7}{'OpenMC k-inf':>22}{'DRAGON':>10}{'diff pcm':>10}")
    for d in DENS:
        if d not in sw: continue
        k, s = sw[d]
        kd = DRAGON_K[0] if d == 0.72 else DRAGON_BR[(0, d)]
        print(f"{d:>5.2f}{VOIDPC[d]:>7.1f}{k:>14.5f} +/-{s:.5f}"
              f"{kd:>10.5f}{pcm(k, kd):>+10.0f}")
    if 0.72 in sw:
        k0, s0 = sw[0.72]
        print(f"\n  void reactivity, relative to dca=0.72:")
        print(f"{'void%':>9}{'OpenMC pcm':>18}{'DRAGON pcm':>14}{'diff':>8}")
        for d in (0.35, 0.02):
            if d not in sw: continue
            k, s = sw[d]
            dr  = pcm(k, k0)
            sd  = 1e5 * np.hypot(srho(k, s), srho(k0, s0))
            drd = pcm(DRAGON_BR[(0, d)], DRAGON_K[0])
            print(f"{VOIDPC[d]:>8.1f}%{dr:>+13.0f} +/-{sd:<4.0f}"
                  f"{drd:>+14.0f}{dr-drd:>+8.0f}")
    print()


def burnup(jsonfile, label):
    if not os.path.exists(jsonfile):
        print(f"[{label}] depletion branches: no results yet\n"); return
    res = json.load(open(jsonfile))
    by = {(int(round(r["bu"] * 1000)), r["dca"]): (r["k"], r["sd"])
          for r in res}
    print("=" * 76)
    print(f"VOID COEFFICIENT vs BURNUP   OpenMC {label} depletion  vs  DRAGON EVO:")
    print("=" * 76)
    print(f"{'BU':>7}{'k-inf nominal':>26}{'':>3}"
          f"{'full-void reactivity, pcm':>32}")
    print(f"{'MWd/t':>7}{'OpenMC':>16}{'DRAGON':>10}{'':>3}"
          f"{'OpenMC':>18}{'DRAGON':>10}{'diff':>8}")
    for bu in sorted(DRAGON_K):
        if (bu, 0.72) not in by: continue
        k0, s0 = by[(bu, 0.72)]
        line = f"{bu:>7d}{k0:>11.5f}+/-{s0:.5f}{DRAGON_K[bu]:>10.5f}   "
        if (bu, 0.02) in by:
            kv, sv = by[(bu, 0.02)]
            dr  = pcm(kv, k0)
            sd  = 1e5 * np.hypot(srho(kv, sv), srho(k0, s0))
            drd = pcm(DRAGON_BR[(bu, 0.02)], DRAGON_K[bu])
            line += f"{dr:>+13.0f} +/-{sd:<4.0f}{drd:>+10.0f}{dr-drd:>+8.0f}"
        print(line)
    print()


if __name__ == "__main__":
    fresh("run81", "ENDF/B-VIII.1")
    fresh("run",   "ENDF/B-VIII.0")
    burnup("branch_results81.json", "ENDF/B-VIII.1")
    burnup("branch_results.json",   "ENDF/B-VIII.0")
