#!/usr/bin/env python3
"""Invert INSAG-7 Fig. II-9's t = 0 axial flux for a per-bundle burnup shape.

This is a FIT, not a validation.  It solves for the 28 per-bundle burnup
multipliers (U4_AXBURN=file:, mean 1, each channel's burnup kept) that make
the static device-model core reproduce the measured 01:23:40 axial shape.  The
multiplier is an EFFECTIVE axial reactivity profile: the real shape was set by
burnup, xenon, void and rod positions together, and this lumps all of them
into the one knob the model exposes.  The 4/6/7 s curves of the same figure
stay untouched -- they are the independent test of the result.

Two approximations, stated:
  * the model's axial shape is the plane POWER (POWER-BUND); the figure is
    neutron flux.  Plane power over plane flux varies with burnup along the
    channel, so this is a shape comparison at the ~10 % level, not better;
  * the target below D = 33 cm and above D = 685 cm (the end bundles) is a
    linear extrapolation of the last two markers.

Method.  A multiplicative fixed point, g <- g*(P/T)**alpha, was tried first
and does not work here: the core is axially near-degenerate, and a burnup
tilt of about +-5 % end to end swings the flux from the upper hump to a
bottom peak (iterates 1-4: rms 0.84, 0.37, 0.90, 0.26 as alpha halved).  So
the fit is Levenberg-Marquardt on a smooth basis instead:
    log g(z) = sum_{n=1..N} c_n P_n(x),   x = 2 z/H - 1,
renormalised to mean 1 (so each channel keeps its burnup), with a
forward-difference Jacobian -- N extra static solves per iteration.  The
smooth basis is also the honest resolution: eight markers do not determine
28 independent bundle values.

Usage: a8_axinvert.py <outdir> [max_iter] [N] [start_g.txt]
Runs DONJON sequentially; one static solve per iteration.
"""
import csv
import os
import subprocess
import sys
import time

import numpy as np
from scipy.interpolate import PchipInterpolator

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from a8_axial import shape, NB, PITCH            # noqa: E402

GMAX = 20000.0 / 10900.0    # top COMPO burnup node over the flat core burnup
GMIN = 0.05


def target():
    rows = [r for r in csv.reader(
        l for l in open(os.path.join(ROOT, "sources/derived/insag7_fig_II9_axial.csv"))
        if not l.startswith("#"))][1:]
    pts = sorted((float(r[2]), float(r[3])) for r in rows if r[0] == "0")
    D, f = map(np.array, zip(*pts))
    Db = 700.0 - (np.arange(NB) + 0.5) * PITCH          # bundle k, bottom up
    T = PchipInterpolator(D, f, extrapolate=False)(Db)
    lo, hi = Db < D[0], Db > D[-1]
    T[lo] = f[0] + (Db[lo] - D[0]) * (f[1] - f[0]) / (D[1] - D[0])
    T[hi] = f[-1] + (Db[hi] - D[-1]) * (f[-1] - f[-2]) / (D[-1] - D[-2])
    # A8_TILT=a multiplies the target by (1 - a x), x = -1 at the core bottom
    # and +1 at the top, before renormalising: a = +0.1 raises the bottom-to-
    # top power density ratio by 1.1/0.9 = 1.22.  This is INSAG-7 p. 69's
    # "20 % variation in initial power density" (Ref. [28]: 31x or 64x at
    # 6.5 s) made into a band on the measured shape.  The source does not say
    # which 20 %; a linear tilt is the smallest assumption that moves power
    # between the halves, which is what decides the scram (section 26).
    tilt = float(os.environ.get("A8_TILT", "0"))
    x = 2.0 * (np.arange(NB) + 0.5) / NB - 1.0
    T = T * (1.0 - tilt * x)
    return T / T.mean(), Db


def run(g, path):
    np.savetxt(path, g, fmt="%.6f")
    env = dict(os.environ, U4_DEV="1", U4_RODS="wat", U4_PBUND="1",
               U4_AXBURN="file:" + path)
    out = subprocess.run(["python3", "gen_rbmk_unit4.py"], env=env, text=True,
                         capture_output=True, check=True,
                         cwd=os.path.join(ROOT, "decks/Donjon/data")).stdout
    name = out.splitlines()[0].split("wrote decks/Donjon/data/")[1].strip()
    subprocess.run([os.path.join(ROOT, "tools/link_decks.sh")], check=True,
                   capture_output=True)
    res = os.path.join(ROOT, "5.1/Donjon/Linux_aarch64", name + ".result")
    if os.path.exists(res):
        os.remove(res)                                    # rule 5
    subprocess.run(["./rdonjon", name], cwd=os.path.join(ROOT, "5.1/Donjon"),
                   capture_output=True)
    txt = open(res, "rb").read().decode("latin1")
    k = float(txt.rsplit("KEFF", 1)[1].split()[0]) if "KEFF" in txt else float("nan")
    s, _ = shape(res)
    return np.array(s), k, name


def basis(N):
    from numpy.polynomial import legendre
    x = 2.0 * (np.arange(NB) + 0.5) / NB - 1.0
    return np.array([legendre.legval(x, [0] * n + [1]) for n in range(1, N + 1)]).T


def g_of(B, c):
    g = np.exp(B @ c)
    g = g / g.mean()
    if g.max() > GMAX or g.min() < GMIN:
        raise ValueError(f"g out of the COMPO burnup table: [{g.min():.3f},{g.max():.3f}]")
    return g


def main():
    outdir = sys.argv[1]
    nmax = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    N = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    os.makedirs(outdir, exist_ok=True)
    T, Db = target()
    np.savetxt(os.path.join(outdir, "target.txt"), T, fmt="%.6f")
    B = basis(N)
    c = np.zeros(N)
    if len(sys.argv) > 4:                       # start from a previous g
        c = np.linalg.lstsq(B, np.log(np.loadtxt(sys.argv[4])), rcond=None)[0]
    log = open(os.path.join(outdir, "log.txt"), "a")
    nrun = [0]

    def ev(c, tag):
        t0 = time.time()
        g = g_of(B, c)
        P, k, name = run(g, os.path.join(outdir, f"g_{nrun[0]:03d}.txt"))
        np.savetxt(os.path.join(outdir, f"P_{nrun[0]:03d}.txt"), P, fmt="%.6f")
        nrun[0] += 1
        rms = float(np.sqrt(np.mean((P - T) ** 2)))
        line = (f"{tag:10s} k {k:.6f}  rms {rms:.4f}  max {np.max(np.abs(P - T)):.4f}"
                f"  g[{g.min():.3f},{g.max():.3f}]  c {np.array2string(c, precision=4)}"
                f"  {time.time() - t0:.0f}s")
        print(line, flush=True)
        log.write(line + "\n"); log.flush()
        return P, k, rms, g

    P, k, rms, g = ev(c, "start")
    lam, h = 1e-2, 0.005
    for it in range(nmax):
        J = np.empty((NB, N))
        for n in range(N):
            dc = np.zeros(N); dc[n] = h
            J[:, n] = (ev(c + dc, f"J{it}.{n + 1}")[0] - P) / h
        r = P - T
        A, gr = J.T @ J, J.T @ r
        while True:
            step = -np.linalg.solve(A + lam * np.diag(np.diag(A)), gr)
            # trust region in log g: never move a bundle by more than 4 %
            sc = min(1.0, 0.04 / max(1e-12, np.max(np.abs(B @ step))))
            try:
                P2, k2, rms2, g2 = ev(c + sc * step, f"it{it} l{lam:.0e}")
            except ValueError as e:
                print(e); rms2 = np.inf
            if rms2 < rms:
                c, P, k, rms, g = c + sc * step, P2, k2, rms2, g2
                lam = max(lam / 3, 1e-4)
                break
            lam *= 4
            if lam > 1e3:
                break
        if lam > 1e3 or rms < 0.01:
            break
    np.savetxt(os.path.join(outdir, "g_best.txt"), g, fmt="%.6f")
    np.savetxt(os.path.join(outdir, "P_best.txt"), P, fmt="%.6f")
    print(f"\nbest: k {k:.6f}  rms {rms:.4f}  ({nrun[0]} solves)  c {c}")
    print("  bundle   D cm   target   model    g")
    for b in range(NB - 1, -1, -1):
        print(f"  {b + 1:5d}  {Db[b]:5.0f}   {T[b]:.3f}   {P[b]:.3f}   {g[b]:.3f}")


if __name__ == "__main__":
    main()
