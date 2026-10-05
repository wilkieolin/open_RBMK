#!/usr/bin/env python3
"""A6d: the rod response matrix, measured one rod at a time.

    python3 tools/a6d_respmat.py --jacobian --burnmap chess --delta 8
    python3 tools/a6d_respmat.py --linearity --burnmap chess
    python3 tools/a6d_respmat.py --solve --burnmap chess --dmax 12

WHY A MATRIX AND NOT A FEEDBACK RULE.  PROGRESS (18) solved for a rod pattern
with a local rule -- insert deeper where the neighbourhood is hot -- and it
walked UPHILL, 2.240 -> 4.28 in MAX/AVG, then converged there.  The reason was
measured: driving 41 well-separated rods in, the channels whose relative power
falls most are uncorrelated with distance to a moved rod and strongly
correlated with core radius.  A rod's response is not local, so the Jacobian is
not diagonal and a diagonal rule optimises the wrong object.

WHY ONE ROD AT A TIME, AND NOT A MULTIPLEXED DESIGN.  Moving several
well-separated rods per run would be 5 runs instead of 190, and it is exactly
the assumption the measurement above destroyed: separation does not decouple
the columns when the response is global.  Multiplexing would also hide the
thing the physics says is interesting -- that each rod's response is its own,
because the displacer sits at the end of a 7 m channel in a power distribution
that varies strongly across the core, so the same insertion means different
things at different sites.  DONJON is deterministic, so a single-rod
perturbation needs no repeats and the only error is the solver's own
convergence, six orders below the signal.

WHAT IS MEASURED.  Base: every solved rod withdrawn, the 21 bottom-entry USP at
their sourced depths.  Column r: rod r alone driven `delta` planes in.  Then

    J[c][r] = (P_c(delta on rod r) - P_c(base)) / delta      kW per plane

CHECKS, BECAUSE THIS IS A 1661 x 190 OBJECT THAT NOTHING ELSE VALIDATES.
  1. FLPOW: renormalises to PTOT, so total power is fixed and every column must
     sum to zero.  Any column that does not is an extraction error, not physics.
  2. --linearity reprobes a sample of rods at other deltas and checks J scales.
     The displacer makes the response non-monotone in depth over the full
     travel (k rises 2000 pcm over the last four planes, PROGRESS 18), so the
     range over which a single linearisation is usable has to be measured, not
     assumed.  --dmax then confines the solve to it.
  3. The pattern the solve predicts is RUN, and the predicted peak compared
     against the real one.  A linear model of a non-monotone control is only
     as good as that comparison says it is.

MEMORY: J is 1661 x 190 float64 = 2.5 MB, on the CPU.  Nothing here goes near
the GPU or the machine's budget.
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a6d_rods as R          # run(), powers(), parse(), load_map(), SOLVED, NZ, PLANE_CM

OUT = os.path.join(R.SCRATCH, "respmat")


def base_depths(cps, src=""):
    """The pattern the matrix is measured about.

    Default: every solved rod out, the USP at their sourced depths.  With
    `src`, an existing depth file -- which is what a sequential linear
    programming step needs, because the matrix has to be re-measured at the
    pattern the previous step produced.  Checked for length against the map.
    """
    if src:
        v = [float(x) for x in open(src).read().split()]
        if len(v) != len(cps):
            raise SystemExit(f"{src}: {len(v)} depths, {len(cps)} CPS rods")
        return v
    return [0.0 if r["type"] in R.SOLVED else float(r["depth_cm"] or 0)
            for r in cps]


def clean(res):
    """Drop the per-rod deck and result once the powers are out of it.

    J plus the provenance in the .npz is the artefact; 190 decks and 190
    results are ~190 MB of intermediate that nothing reads again, and the deck
    is regenerable from the depth file whose md5 is in its own name.
    """
    name = os.path.basename(res)[:-len(".result")]
    for p in (res, os.path.join(R.ROOT, "decks", "Donjon", "data", name)):
        try:
            os.remove(p)
        except OSError:
            pass


# THE UNIVERSAL DEPTH CURVE, measured 2026-10-05 on five rods (29, 52, 63, 76,
# 128 -- four RR and one AZ, spread across the core) at eight depths each.
#
# The response to a rod's insertion factorises.  Its DIRECTION in channel space
# is fixed: the cosine similarity between the same rod's response at 4, 8, 16
# and 24 planes is >= 0.9975.  Its AMPLITUDE follows one curve shared by every
# rod, ||dP(d)|| normalised to its value at 16 planes, agreeing across the five
# to within 0.054 at worst (4 %):
G = {0: 0.0, 2: 0.0231, 4: 0.0884, 8: 0.3417, 12: 0.6889,
     16: 1.0, 20: 1.1880, 24: 1.2455, 28: 1.1887}
#
# So one run per rod measures the direction, and this curve carries it to any
# depth -- 190 runs instead of 1520.  The curve is also the physics: a
# top-entry absorber enters the low-flux top of the core, so the first planes
# do almost nothing (2 % of the peak response at 2 planes); it reaches maximum
# effect mid-travel; and past 24 planes the displacer has been fully expelled
# and the absorber relocates toward the bottom, so the response TURNS OVER.
# The worth curve does the same, peaking at 24 planes at 1.000 and falling to
# 0.959 at 28 -- the +2000 pcm over the last four planes of PROGRESS (18),
# recovered per rod.
#
# G is therefore monotone only on [0, 24], and that is the range the solve is
# confined to.  Beyond it the control is not invertible.
G_MAX_PLANES = 24

# The WORTH follows the same curve, normalised to its own peak at 24 planes:
W = {0: 0.0, 2: 0.0180, 4: 0.0741, 8: 0.2884, 12: 0.5763,
     16: 0.8207, 20: 0.9600, 24: 1.0000, 28: 0.9592}
# and W(d)/G(d) is 0.78, 0.84, 0.84, 0.84, 0.82, 0.81, 0.80 across the travel
# -- constant to about 4 %.  A rod's reactivity worth and the amplitude of the
# power it redistributes are therefore PROPORTIONAL at every depth, which is
# what makes the flatness/criticality trade-off an exact linear program: both
# are linear in the same variable u = g(d).  Tracing that trade-off properly is
# what section (18)'s four-point budget sweep was groping at.


def g(d):
    """The amplitude factor at depth d planes, linearly interpolated on G."""
    ks = sorted(G)
    if d <= 0:
        return 0.0
    if d >= ks[-1]:
        return G[ks[-1]]
    for i in range(1, len(ks)):
        if d <= ks[i]:
            f = (d - ks[i - 1]) / (ks[i] - ks[i - 1])
            return G[ks[i - 1]] + f * (G[ks[i]] - G[ks[i - 1]])
    return G[ks[-1]]


def g_inv(u):
    """The depth in planes whose amplitude factor is u, on [0, G_MAX_PLANES]."""
    lo, hi = 0.0, float(G_MAX_PLANES)
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if g(mid) < u:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def jacobian(a):
    fuel, cps = R.load_map()
    solved = [k for k, r in enumerate(cps) if r["type"] in R.SOLVED]
    base = base_depths(cps, a.base)
    sfx = ("_s" + os.path.basename(a.base).replace('.txt','')) if a.base else ""
    npz = f"{OUT}_{a.burnmap}_d{a.delta}{sfx}.npz"
    os.makedirs(R.SCRATCH, exist_ok=True)

    k0, pk0, ff0, res = R.run(base, a.burnmap, a.xe, a.bins, "base")
    p0 = np.array(R.powers(res))
    print(f"base: k {k0:.6f}  peak {pk0:.1f} kW  MAX/AVG {ff0:.4f}  "
          f"({len(solved)} rods out)")
    print(f"probing each rod {a.delta} planes in, one at a time\n")

    J = np.zeros((len(p0), len(solved)))
    kk = np.zeros(len(solved))
    done = 0
    if os.path.exists(npz) and not a.restart:
        z = np.load(npz)
        if z["J"].shape == J.shape and int(z["done"]) > 0:
            J, kk, done = z["J"], z["kvals"], int(z["done"])
            print(f"resuming from {npz}, {done} columns already measured\n")

    for n in range(done, len(solved)):
        d = list(base)
        d[solved[n]] = a.delta * R.PLANE_CM
        kv, pk, ff, res = R.run(d, a.burnmap, a.xe, a.bins, f"j{n}")
        p = np.array(R.powers(res))
        J[:, n] = (p - p0) / a.delta
        kk[n] = kv
        clean(res)
        if n % 10 == 0 or n == len(solved) - 1:
            np.savez(npz, J=J, kvals=kk, p0=p0, done=n + 1,
                     delta=a.delta, base=np.array(base),
                     solved=np.array(solved), k0=k0,
                     burnmap=a.burnmap, xe=a.xe)
            pcm = (1.0 / k0 - 1.0 / kv) * 1e5
            print(f"  rod {n:3d}/{len(solved)}  type {cps[solved[n]]['type']:4s} "
                  f"worth {pcm:+7.1f} pcm   column sum {J[:, n].sum():+.3e} "
                  f"kW/plane   max |dP| {np.abs(J[:, n]).max():.4f}")
    np.savez(npz, J=J, kvals=kk, p0=p0, done=len(solved), delta=a.delta,
             base=np.array(base), solved=np.array(solved), k0=k0,
             burnmap=a.burnmap, xe=a.xe)
    print(f"\nwrote {npz}")
    report(J, kk, k0, cps, solved)


def report(J, kk, k0, cps, solved):
    print("\ncheck 1: FLPOW: fixes total power, so every column must sum to 0")
    s = np.abs(J.sum(axis=0))
    tot = np.abs(J).sum(axis=0)
    print(f"  worst |column sum| {s.max():.3e} kW/plane, against a mean "
          f"|dP| total of {tot.mean():.3e}  -> {s.max()/tot.mean():.2e} relative")
    print("\nper-rod worth and reach, by type")
    print(f"{'type':>5} {'n':>4} {'pcm/plane':>20} {'max |dP| kW/plane':>20} "
          f"{'fraction of |dP| beyond 2 pitches':>34}")
    import collections
    byt = collections.defaultdict(list)
    for n, kidx in enumerate(solved):
        byt[cps[kidx]["type"]].append(n)
    for t, ns in sorted(byt.items()):
        w = [(1.0 / k0 - 1.0 / kk[n]) * 1e5 for n in ns if kk[n] > 0]
        mx = [np.abs(J[:, n]).max() for n in ns]
        print(f"{t:>5} {len(ns):4d} {np.mean(w):10.2f} +/- {np.std(w):5.2f}  "
              f"{np.mean(mx):18.4f} {'':>20}")


def linearity(a):
    fuel, cps = R.load_map()
    solved = [k for k, r in enumerate(cps) if r["type"] in R.SOLVED]
    base = base_depths(cps)
    k0, pk0, ff0, res = R.run(base, a.burnmap, a.xe, a.bins, "base")
    p0 = np.array(R.powers(res))
    rng = np.random.default_rng(20261005)
    pick = sorted(rng.choice(len(solved), size=5, replace=False).tolist())
    print(f"linearity of the response, rods {pick}\n")
    print(f"{'rod':>4} {'type':>5} {'delta':>6} {'pcm':>9} "
          f"{'||dP||/delta':>13} {'vs delta=8':>11}")
    for n in pick:
        ref = None
        for dl in (2, 4, 8, 12, 16, 20, 24, 28):
            d = list(base)
            d[solved[n]] = dl * R.PLANE_CM
            kv, pk, ff, res = R.run(d, a.burnmap, a.xe, a.bins, f"lin{n}_{dl}")
            p = np.array(R.powers(res))
            nrm = np.linalg.norm(p - p0) / dl
            pcm = (1.0 / k0 - 1.0 / kv) * 1e5
            if dl == 8:
                ref = nrm
            rel = "" if ref is None else f"{nrm/ref:11.3f}"
            print(f"{n:4d} {cps[solved[n]]['type']:>5} {dl:6d} {pcm:9.1f} "
                  f"{nrm:13.5f} {rel}")
            clean(res)
        print()


def solve(a):
    """Choose depths to minimise the peak channel power, on the measured matrix.

    The model is NOT linear in depth -- G above is strongly curved -- but it is
    linear in the amplitude u_r = g(d_r), because the response direction is
    fixed per rod.  So the choice of pattern is an exact linear program in u,

        minimise  t   subject to   P0_c + sum_r u_r H[c][r] <= t   for all c
                                   0 <= u_r <= g(dmax)

    and the depths come back by inverting G.  H is the measured response at 16
    planes, so u is in units of that: u = 1 means "this rod at 16 planes".

    FLPOW: holds the total power fixed, so every column of H sums to zero and
    the LP cannot lower the peak by lowering everything -- it can only
    redistribute.  That is checked, not assumed.
    """
    from scipy.optimize import linprog
    fuel, cps = R.load_map()
    sfx = ("_s" + os.path.basename(a.base).replace(".txt", "")) if a.base else ""
    npz = f"{OUT}_{a.burnmap}_d{a.delta}{sfx}.npz"
    z = np.load(npz, allow_pickle=True)
    H, p0, solved = z["J"] * int(z["delta"]), z["p0"], z["solved"].tolist()
    if int(z["done"]) != H.shape[1]:
        raise SystemExit(f"{npz}: only {int(z['done'])} of {H.shape[1]} columns")
    nc, nr = H.shape
    print(f"H is {nc} x {nr}, measured at {int(z['delta'])} planes, "
          f"burnup {str(z['burnmap'])}")
    # POWER-CHAN is already in kW -- FLPOW: reports 1923.1 kW mean over 1661
    # channels against a 3.2 GW total, so no scaling is applied here.
    print(f"base peak {p0.max():.1f} kW, MAX/AVG {p0.max()/p0.mean():.4f}")

    cs = np.abs(H.sum(axis=0))
    print(f"\ncheck: total power is fixed, so every column must sum to 0 -- "
          f"worst {cs.max():.3e} kW against a mean column norm of "
          f"{np.linalg.norm(H, axis=0).mean():.3e}")
    sv = np.linalg.svd(H, compute_uv=False)
    ev = sv ** 2 / (sv ** 2).sum()
    print(f"effective rank of the control {(sv**2).sum()**2/(sv**4).sum():.2f} "
          f"of {nr}; mode 1 carries {ev[0]*100:.1f} %, modes 1-5 "
          f"{ev[:5].sum()*100:.1f} %")

    # per-rod worth of the probe move itself, in pcm, from each probe run's k.
    # It is the coefficient per unit of the LP variable v below, because worth
    # and response amplitude follow the same depth curve (W/G constant to 4 %).
    k0 = float(z["k0"])
    wr = np.array([(1.0 / k0 - 1.0 / kv) * 1e5 if kv > 0 else 0.0
                   for kv in z["kvals"]])
    print(f"probe worths: {wr.min():.1f} to {wr.max():.1f} pcm per "
          f"{int(z['delta'])}-plane move")

    # REBASING, which matters from the second SLP step on.  H[:,r] is the
    # response to moving rod r from ITS BASE DEPTH d0_r to d0_r + delta, while
    # G is a function of ABSOLUTE depth.  So the response to putting that rod at
    # absolute depth d is
    #
    #     H[:,r] * (g(d) - g(d0_r)) / (g(d0_r + delta) - g(d0_r))
    #
    # and the LP variable is that coefficient v_r.  On step 1 every solved rod
    # starts at 0, the denominator is g(delta) and v reduces to g(d)/g(delta) --
    # which is why the un-rebased form was right there and wrong here.  Rebasing
    # also lets v go NEGATIVE, i.e. the LP may WITHDRAW a rod, which from step 2
    # on is half the available control and was previously unreachable.
    base = z["base"].tolist()
    dmax = min(a.dmax, G_MAX_PLANES)
    d0 = np.array([base[kidx] / R.PLANE_CM for kidx in solved])
    den = np.array([g(x + int(z["delta"])) - g(x) for x in d0])
    if np.any(np.abs(den) < 1e-9):
        raise SystemExit("a rod's probe produced no amplitude change -- "
                         "it is at the top of the G curve and cannot be probed "
                         "by inserting further")
    lo = np.array([(g(0.0) - g(x)) / dn for x, dn in zip(d0, den)])
    hi = np.array([(g(dmax) - g(x)) / dn for x, dn in zip(d0, den)])
    print(f"\nbase pattern: {(d0 > 0).sum()} rods already inserted, "
          f"mean depth {d0.mean():.2f} planes")
    print(f"LP variable range: {lo.min():.3f} to {hi.max():.3f} "
          f"({(lo < -1e-9).sum()} rods can be withdrawn)")

    c = np.zeros(nr + 1)
    c[-1] = 1.0
    A = np.hstack([H, -np.ones((nc, 1))])
    b = -p0
    if a.maxrho:
        # TRUST REGION, and it is not optional.  The per-rod responses are
        # separable but NOT additive at large collective amplitude: measured
        # 2026-10-05, the unconstrained LP on all 190 columns chose 93 rods
        # delivering -2659 pcm, predicted MAX/AVG 1.4369, and DONJON returned
        # 2.8285 -- worse than the 2.7702 it started from.  The core's azimuthal
        # modes are nearly degenerate, so a perturbation that large moves the
        # modes the matrix was measured in.  Bounding the total worth bounds the
        # perturbation, and the solve becomes sequential linear programming:
        # solve, verify, re-measure about the accepted step.
        #
        # |worth| <= maxrho, as two rows, because v may be of either sign.
        A = np.vstack([A, np.hstack([-wr, [0.0]]), np.hstack([wr, [0.0]])])
        b = np.concatenate([b, [abs(a.maxrho), abs(a.maxrho)]])
        print(f"trust region: |total rod worth| held to <= {abs(a.maxrho):.0f} pcm")
    if a.rho:
        # worths are NEGATIVE pcm, so "deliver at least rho" is
        # sum_r w_r v_r <= -rho, not the sign-flipped form.
        A = np.vstack([A, np.hstack([wr, [0.0]])])
        b = np.concatenate([b, [-abs(a.rho)]])
        print(f"constrained to deliver at least {abs(a.rho):.0f} pcm")
    r = linprog(c, A_ub=A, b_ub=b,
                bounds=list(zip(lo, hi)) + [(None, None)], method="highs")
    if not r.success:
        print("  INFEASIBLE: " + r.message.strip())
        return
    u = r.x[:nr]
    print(f"  worth delivered {float(wr @ u):.0f} pcm")
    pred = p0 + H @ u
    print(f"  predicted peak {pred.max():.1f} kW, "
          f"MAX/AVG {pred.max()/pred.mean():.4f}")

    # back to absolute depths on the 25 cm mesh
    dep = np.array([g_inv(min(max(g(x) + v * dn, 0.0), g(G_MAX_PLANES)))
                    for x, v, dn in zip(d0, u, den)])
    dr = np.clip(np.round(dep), 0, G_MAX_PLANES).astype(int)
    vr = np.array([(g(float(q)) - g(x)) / dn
                   for q, x, dn in zip(dr, d0, den)])
    predr = p0 + H @ vr
    print(f"  {(dr > 0).sum()} rods inserted, mean depth {dr.mean():.2f} planes, "
          f"{int((dr != np.round(d0)).sum())} moved from base")
    print(f"  after rounding to the 25 cm mesh: {predr.max():.1f} kW, "
          f"{predr.max()/predr.mean():.4f}")

    dd = list(base)
    for n, kidx in enumerate(solved):
        dd[kidx] = float(dr[n]) * R.PLANE_CM
    kv, pk, ff, res = R.run(dd, a.burnmap, a.xe, a.bins, "lpsol")
    print("\nverification -- the model against DONJON, which is the only test "
          "that counts")
    print(f"{'':>24} {'peak kW':>10} {'MAX/AVG':>9}")
    print(f"{'model, rounded':>24} {predr.max():10.1f} "
          f"{predr.max()/predr.mean():9.4f}")
    print(f"{'DONJON':>24} {pk:10.1f} {ff:9.4f}")
    print(f"{'':>24} k = {kv:.6f}")
    # the step number has to be in the name: step 1 and step 2 at the same
    # trust region would otherwise overwrite each other
    stepn = os.path.basename(a.base).count("_r") + 1 if a.base else 1
    tag = (f"_s{stepn}" if stepn > 1 else "") + (
        f"_r{int(abs(a.maxrho))}" if a.maxrho else "")
    out = os.path.join(R.SCRATCH, f"rd_lp_{a.burnmap}{tag}.txt")
    with open(out, "w") as fh:
        fh.write("\n".join(f"{x:.1f}" for x in dd))
    print(f"\npattern written to {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--burnmap", default="chess")
    ap.add_argument("--xe", default="equil1.0")
    ap.add_argument("--bins", type=int, default=1)
    ap.add_argument("--delta", type=int, default=8)
    ap.add_argument("--dmax", type=int, default=24)
    ap.add_argument("--rho", type=float, default=0.0,
                    help="require at least this much rod worth, pcm")
    ap.add_argument("--maxrho", type=float, default=0.0,
                    help="trust region: cap total rod worth at this, pcm")
    ap.add_argument("--jacobian", action="store_true")
    ap.add_argument("--linearity", action="store_true")
    ap.add_argument("--solve", action="store_true")
    ap.add_argument("--restart", action="store_true")
    ap.add_argument("--base", default="",
                    help="depth file to measure the matrix about (SLP step 2+)")
    a = ap.parse_args()
    if a.jacobian:
        jacobian(a)
    elif a.linearity:
        linearity(a)
    elif a.solve:
        solve(a)
    else:
        ap.error("pick --jacobian, --linearity or --solve")


if __name__ == "__main__":
    main()
