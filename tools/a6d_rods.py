#!/usr/bin/env python3
"""A6d: solve for a control-rod pattern, rather than assume one.

    python3 tools/a6d_rods.py --burnmap chess --xe equil1.0 --phase1
    python3 tools/a6d_rods.py --burnmap chess --xe equil1.0 --refine 20

WHAT IS BEING ASKED.  PROGRESS (17) closed with one question: a burnup placement
is admissible if SOME rod pattern takes it to a channel power inside [D]'s
published 3000-3200 kW at full power.  That is an existence question about 190
rod depths, and it is well posed without a source, because the TARGET is sourced
even though the pattern is not.  What comes out is NOT the historical pattern --
INSAG-7 gives the 01:22:30 depths and nothing for normal operation -- it is a
demonstration that an admissible pattern does or does not exist.

WHAT IS HELD FIXED.  Every rod's sourced TYPE and SITE, from
sources/derived/unit4_channel_map.csv; only the depth moves, and only for the
190 TOP-ENTRY rods (RR 121, AZOC 36, AZ 21, AR 12).  The 21 bottom-entry USP
keep their sourced depths, because they are a distinct system on a 3.5 m
absorber and mixing them in would conflate two shaping mechanisms.  The
generator checks the file against the map before it is trusted, and writing the
sourced depths back through it is a verified no-op.

THE CRITICALITY TARGET IS NOT USED, DELIBERATELY.  Reaching k = 1 from the
rods-out 1.045255 needs 4330 pcm, and the 211 rods are worth 5552 pcm fully in,
so it takes about 190 rods at four fifths of their travel.  A real RBMK at full
power carries 55-70 inserted rods.  That gap is a statement about the MODEL's
excess reactivity -- TG is pinned ~120 K low, worth about +500 pcm (A6b), and
the reflector is still a placeholder -- not about the rods.  Driving k to 1 by
adding absorber would be compensating a known modelling bias with physical
absorber, which is standing rule 1.  So the shape is solved at a stated
insertion BUDGET and the resulting k is reported as a diagnostic.

THE SEARCH, AND WHY IT IS NOT A FIXED-POINT ITERATION.  Two earlier naive
fixed-point solves in this project diverged -- the burnup placement, and the
xenon field, which needed w = 0.35 to converge (PROGRESS 16).  The loop here is
the same shape and would do the same thing, so phase 1 does not iterate at all:
it reduces 190 unknowns to TWO, by ranking the rod sites on local power and
laying a monotone depth profile over the ranks,

    depth_i = B + A * (rank_i / (N-1) - 1/2)      planes, clamped to [0, NZ]

with the hottest site deepest, and sweeps (A, B) on a grid.  B is the budget and
A is how hard the pattern discriminates.  Phase 2 then refines per rod from the
best grid point, damped, and reports every pass so a divergence is visible
rather than averaged away.

LOCAL POWER is the mean fuel-channel power within RADIUS lattice pitches of the
rod site.  The pitch is 25 cm and the migration length is comparable to it, so a
radius of 2 (50 cm) is about the smallest neighbourhood the flux can resolve;
a rod cannot shape anything finer than that however it is positioned.
"""
import argparse
import csv
import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(ROOT, "sources", "derived", "unit4_channel_map.csv")
RUNDIR = os.path.join(ROOT, "5.1", "Donjon")
BINDIR = os.path.join(RUNDIR, "Linux_aarch64")
GEN = os.path.join(ROOT, "decks", "Donjon", "data", "gen_rbmk_unit4.py")
NZ = 28                      # active planes, 25 cm each
PLANE_CM = 700.0 / NZ
SOLVED = {"RR", "AZOC", "AZ", "AR"}      # top-entry; USP held at sourced
CPS = SOLVED | {"USP"}
SCRATCH = os.environ.get("A6D_SCRATCH", "/tmp/a6d_rods")


def load_map():
    rows = list(csv.DictReader(open(MAP)))
    fuel = [(int(r["i"]), int(r["j"])) for r in rows if r["type"] == "FUEL"]
    cps = [r for r in rows if r["type"] in CPS]
    return fuel, cps


def local_power(fuel, cps, pw, radius):
    """Mean fuel-channel power near each rod site, as a ratio to the core mean.

    A rod with no fuel inside `radius` gets 1.0, i.e. no reason to move -- that
    happens only at the outermost sites and is reported by the caller.
    """
    mean = sum(pw) / len(pw)
    r2 = radius * radius
    out, lonely = [], 0
    for r in cps:
        i, j = int(r["i"]), int(r["j"])
        acc = n = 0
        for (fi, fj), q in zip(fuel, pw):
            if (fi - i) ** 2 + (fj - j) ** 2 <= r2:
                acc += q
                n += 1
        if n == 0:
            lonely += 1
            out.append(1.0)
        else:
            out.append(acc / n / mean)
    return out, lonely


def profile(cps, ratio, A, B, base):
    """Depths in cm: monotone in the local-power rank, hottest deepest.

    `base` supplies the depth of any rod not being solved for, so the USP keep
    their sourced insertion while the top-entry rods are rearranged.
    """
    idx = [k for k, r in enumerate(cps) if r["type"] in SOLVED]
    order = sorted(idx, key=lambda k: ratio[k])       # coldest first
    n = len(order)
    out = list(base)
    for rank, k in enumerate(order):
        d = B + A * (rank / (n - 1) - 0.5)
        out[k] = max(0, min(NZ, int(round(d)))) * PLANE_CM
    return out


def run(depths, burnmap, xe, bins, tag):
    """Generate the deck for these depths, run it, return (k, peak kW, MAX/AVG).

    The deck name is content-addressed on the depth file (standing rule 7), so a
    pattern can never be served a result built from a different one, and the
    .result is deleted before the run so a stale file cannot be read as a new
    one (standing rule 5).
    """
    os.makedirs(SCRATCH, exist_ok=True)
    f = os.path.join(SCRATCH, f"rd_{tag}.txt")
    with open(f, "w") as fh:
        fh.write("\n".join(f"{d:.1f}" for d in depths))
    env = dict(os.environ, U4_RODS="insag", U4_RODDEPTH=f)
    if burnmap != "flat":
        env["U4_BURNMAP"] = burnmap
    if bins > 1:
        env["U4_XEBINS"] = str(bins)
        env["U4_XEHIST"] = xe
        env["U4_PCHAN"] = env.get("A6D_PCHAN", "")
    out = subprocess.run([sys.executable, GEN], env=env, capture_output=True,
                         text=True)
    if out.returncode:
        raise SystemExit("generator failed:\n" + out.stdout + out.stderr)
    deck = re.search(r"wrote (\S+\.don)", out.stdout).group(1)
    name = os.path.basename(deck)
    subprocess.run([os.path.join(ROOT, "tools", "link_decks.sh")],
                   capture_output=True)
    res = os.path.join(BINDIR, name + ".result")
    if os.path.exists(res):
        os.remove(res)
    subprocess.run(["./rdonjon", name], cwd=RUNDIR, capture_output=True,
                   timeout=3600)
    if not os.path.exists(res):
        raise SystemExit(f"{name}: no .result produced")
    return parse(res) + (res,)


def parse(res):
    txt = open(res, "rb").read().decode("latin1")
    k = re.search(r"KEFF\s+([0-9.]+e[-+][0-9]+)", txt)
    pk = re.search(r"MAXIMUM CHANNEL POWER\s*=\s*([0-9.]+)", txt)
    ff = re.search(r"CHANNEL-POWER FORM FACTOR.*?MAX/AVG\s*=\s*([0-9.]+)", txt)
    if not (k and pk and ff):
        raise SystemExit(f"{res}: could not read k / peak / form factor")
    return float(k.group(1)), float(pk.group(1)), float(ff.group(1))


def powers(res):
    txt = open(res, "rb").read().decode("latin1").splitlines()
    for i, l in enumerate(txt):
        if "CONTENT OF BLOCK 'POWER-CHAN" not in l:
            continue
        v = []
        for q in txt[i + 1:]:
            if "CONTENT OF BLOCK" in q or "DRVUTL" in q or "LEAVING" in q:
                break
            v += [float(x) for x in q.split()
                  if re.match(r"^[-+]?\d*\.?\d+E[-+]\d+$", x)]
        return v
    raise SystemExit(f"no POWER-CHAN block in {res}")


def signtest(fuel, cps, burnmap, xe, bins, sep=6.0, near=1.5):
    """Probe how a rod's insertion redistributes power, by distance from the rod.

    Phase 2's update rule assumes a rod's insertion mainly affects the power
    AROUND that rod.  Refining the chequerboard pattern under that rule took
    MAX/AVG from 2.240 to 4.28 and then converged there, which is a wrong model
    of the control reaching a self-consistent wrong answer rather than a
    divergence.

    What this measured (2026-10-05, PROGRESS 18): driving 41 well-separated
    rods 24 planes in is worth -1978 pcm, and the 100 fuel channels whose
    relative power falls most sit at a mean distance of 2.80 pitches from the
    nearest moved rod against a core-wide 2.75 -- uncorrelated -- while their
    mean radius is 21.3 against 17.4.  The response is a global radial
    redistribution, so a diagonal per-rod feedback rule is the wrong method and
    a response matrix is the right one.

    CAUTION, because the first reading of this was wrong.  At -1978 pcm the
    per-channel scatter is +/-35 %, so a 163-channel near-field bin has a
    standard error of ~2.7 % and its mean says nothing.  At 2, 4 and 8 planes
    the changes are 0.01-0.3 % with strongly skewed per-channel distributions
    whose bin means do not average to zero.  So this probe can show that the
    dominant response is NON-LOCAL; it cannot measure how much local authority
    the rods have, and nothing here should be quoted as if it could.

    The measurement moves only a mutually well-separated subset of rods -- at
    least `sep` pitches apart, so their perturbations do not overlap -- and
    reports the mean power of the fuel channels within `near` pitches of them.
    Everything else is held withdrawn, on flat burnup, so the only thing moving
    is rod depth.
    """
    idx, picked = [], []
    for k, r in enumerate(cps):
        if r["type"] not in SOLVED:
            continue
        i, j = int(r["i"]), int(r["j"])
        if all((i - pi) ** 2 + (j - pj) ** 2 >= sep * sep for pi, pj in picked):
            picked.append((i, j))
            idx.append(k)
    n2 = near * near
    probe = [k for k, (fi, fj) in enumerate(fuel)
             if any((fi - i) ** 2 + (fj - j) ** 2 <= n2 for i, j in picked)]
    base = [float(r["depth_cm"] or 0) for r in cps]
    print(f"{len(idx)} rods at least {sep} pitches apart, "
          f"{len(probe)} fuel channels within {near} of one; all other rods out")
    print(f"\n{'depth':>6} {'k':>10} {'pcm':>8} {'local/avg':>10} "
          f"{'d(local)':>9}   sign")
    prev = None
    k0 = None
    for nd in (0, 2, 4, 6, 8, 12, 16, 20, 24, 28):
        d = list(base)
        for kk in [q for q in range(len(cps)) if cps[q]["type"] in SOLVED]:
            d[kk] = 0.0
        for kk in idx:
            d[kk] = nd * PLANE_CM
        kv, pk, ff, res = run(d, burnmap, xe, bins, f"sgn{nd}")
        pw = powers(res)
        m = sum(pw) / len(pw)
        loc = sum(pw[q] for q in probe) / len(probe) / m
        if k0 is None:
            k0 = kv
        pcm = (1.0 / k0 - 1.0 / kv) * 1e5
        if prev is None:
            print(f"{nd:6d} {kv:10.6f} {pcm:8.1f} {loc:10.5f} {'':>9}   (reference)")
        else:
            dl = loc - prev
            print(f"{nd:6d} {kv:10.6f} {pcm:8.1f} {loc:10.5f} {dl:+9.5f}   "
                  f"{'suppresses' if dl < 0 else 'RAISES local power'}")
        prev = loc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--burnmap", default="chess")
    ap.add_argument("--xe", default="equil1.0")
    ap.add_argument("--bins", type=int, default=1)
    ap.add_argument("--radius", type=float, default=2.0)
    ap.add_argument("--seed", default="")
    ap.add_argument("--phase1", action="store_true")
    ap.add_argument("--refine", type=int, default=0)
    ap.add_argument("--signtest", action="store_true")
    ap.add_argument("--startA", type=float, default=None)
    ap.add_argument("--startB", type=float, default=None)
    ap.add_argument("--relax", type=float, default=0.35)
    ap.add_argument("--gain", type=float, default=8.0)
    a = ap.parse_args()

    fuel, cps = load_map()
    base = [float(r["depth_cm"] or 0) for r in cps]
    print(f"{len(fuel)} fuel channels, {len(cps)} CPS rods, "
          f"{sum(1 for r in cps if r['type'] in SOLVED)} of them solved for")
    print(f"burnup {a.burnmap}, xenon {a.xe} in {a.bins} bin(s), "
          f"local radius {a.radius} pitches\n")

    # the starting power shape: the sourced pattern, which is where PROGRESS
    # (17) left the core
    seed = a.seed or os.path.join(BINDIR, f"rbmk_unit4_core_insag"
                                  + ("" if a.burnmap == "flat"
                                     else f"_b{a.burnmap}") + ".don.result")
    if not os.path.exists(seed):
        raise SystemExit(f"{seed}: run the sourced-pattern deck first")
    k0, pk0, ff0 = parse(seed)
    pw = powers(seed)
    ratio, lonely = local_power(fuel, cps, pw, a.radius)
    print(f"seed {os.path.basename(seed)}")
    print(f"  k {k0:.6f}  peak {pk0:.1f} kW  MAX/AVG {ff0:.4f}")
    print(f"  local power ratio at the rod sites: {min(ratio):.3f} to "
          f"{max(ratio):.3f}" + (f", {lonely} sites with no fuel in range"
                                 if lonely else "") + "\n")

    if a.signtest:
        signtest(fuel, cps, a.burnmap, a.xe, a.bins)
        return

    best = None
    if a.phase1:
        print("phase 1: (A, B) grid, A = discrimination, B = budget, in planes")
        print(f"{'A':>4} {'B':>4} {'mean d':>7} {'k':>10} {'peak kW':>9} "
              f"{'MAX/AVG':>8}")
        for B in (4, 8, 14, 20):
            for A in (4, 8, 12, 16):
                d = profile(cps, ratio, A, B, base)
                md = sum(d) / len(d) / PLANE_CM
                tag = f"A{A}B{B}"
                k, pk, ff, _ = run(d, a.burnmap, a.xe, a.bins, tag)
                print(f"{A:4d} {B:4d} {md:7.2f} {k:10.6f} {pk:9.1f} {ff:8.4f}")
                if best is None or ff < best[0]:
                    best = (ff, A, B, k, pk, d)
        print(f"\nbest: A = {best[1]}, B = {best[2]}, MAX/AVG {best[0]:.4f}, "
              f"k {best[3]:.6f}, peak {best[4]:.1f} kW")

    if a.refine:
        if best:
            d = best[5]
        elif a.startA is not None:
            d = profile(cps, ratio, a.startA, a.startB, base)
            print(f"\nstarting from A = {a.startA}, B = {a.startB}")
        else:
            d = profile(cps, ratio, 8, 4, base)
        print(f"\nphase 2: per-rod refinement, relax {a.relax}, gain {a.gain} "
              "planes per unit ratio")
        print(f"{'pass':>4} {'mean d':>7} {'k':>10} {'peak kW':>9} "
              f"{'MAX/AVG':>8} {'moved':>6}")
        for it in range(a.refine):
            k, pk, ff, res = run(d, a.burnmap, a.xe, a.bins, f"ref{it}")
            pw = powers(res)
            ratio, _ = local_power(fuel, cps, pw, a.radius)
            nd, moved = list(d), 0
            for kk, r in enumerate(cps):
                if r["type"] not in SOLVED:
                    continue
                step = a.relax * a.gain * (ratio[kk] - 1.0)
                v = max(0, min(NZ, int(round(d[kk] / PLANE_CM + step))))
                if v * PLANE_CM != d[kk]:
                    moved += 1
                nd[kk] = v * PLANE_CM
            md = sum(d) / len(d) / PLANE_CM
            print(f"{it:4d} {md:7.2f} {k:10.6f} {pk:9.1f} {ff:8.4f} {moved:6d}")
            d = nd


if __name__ == "__main__":
    main()
