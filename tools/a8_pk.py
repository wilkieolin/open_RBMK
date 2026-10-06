#!/usr/bin/env python3
"""Point kinetics driven by the MEASURED static rod ramp, as an independent
check on DONJON's 3-D transient (standing rule 4).

The question this answers is not "is DONJON right" but "how much of this
transient is amplitude and how much is SHAPE".  Point kinetics assumes the flux
shape is frozen; the 3-D solve lets it move, and section (19) measured that 92 %
of the rods' authority is the first azimuthal mode -- i.e. the rods are
shape-movers above all.  So a difference between the two is the spatial content
of the transient, which is the entire reason PROJECT_PLAN says spatial
resolution is mandatory here.  Agreement would be the surprise.

Inputs, none of them fitted:
  rho(t)   the measured static ramp (tools/a8_ramp_reference.txt) evaluated at
           travel = speed * t.  Linear interpolation between measured points.
  lambda_i read out of the COMPO (the same six constants lambda_d() hands to
           INIKIN:).
  beta_i   the COMPO's own per-precursor NUSIGF0i/NUSIGF group shape,
           renormalised to A5b's measured total at the core's 10.9 MWd/kg.
           The SHAPE is from fresh fuel, which is the branch point that can be
           read without indexing a 312 MB file; the shift from U-235 to Pu-239
           changes the split by a few per cent and the total by 22 %, and it is
           the total that sets the amplitude.
  Lambda   NOT derived -- swept over 0.5, 1 and 2 ms, and the answer is
           reported for each so its insensitivity is visible rather than
           asserted.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

LAM = [1.3336e-02, 3.2739e-02, 1.2078e-01, 3.0278e-01, 8.4949e-01, 2.8530e+00]
# COMPO NUSIGF0i/NUSIGF at the fresh-fuel branch point, group 1
BSHAPE = [0.000229, 0.001182, 0.001129, 0.002531, 0.001038, 0.000435]
BETA_TOT = 0.005358 + (10.9 - 10.0) / 5.0 * (0.004985 - 0.005358)   # A5b curve
BETA = [b / sum(BSHAPE) * BETA_TOT for b in BSHAPE]


def ramp():
    out = []
    for line in open(os.path.join(HERE, "a8_ramp_reference.txt")):
        f = line.split()
        if len(f) >= 3:
            try:
                out.append((float(f[0]), float(f[2]) * 1e-5))
            except ValueError:
                pass
    return out


def rho_at(r, travel):
    if travel <= r[0][0]:
        return r[0][1]
    if travel >= r[-1][0]:
        return r[-1][1]
    for (d0, r0), (d1, r1) in zip(r, r[1:]):
        if d0 <= travel <= d1:
            return r0 + (travel - d0) / (d1 - d0) * (r1 - r0)
    return r[-1][1]


def solve(tend, speed, lam_p, dt=1.0e-5):
    """Integrate point kinetics to tend, returning [(t, P/P0)] on a 10 ms grid."""
    r = ramp()
    p = 1.0
    c = [BETA[i] / (LAM[i] * lam_p) for i in range(6)]      # equilibrium
    out, t, nextout = [], 0.0, 0.01
    n = int(round(tend / dt))
    for k in range(n):
        rho = rho_at(r, speed * t)
        dp = (rho - BETA_TOT) / lam_p * p + sum(LAM[i] * c[i] for i in range(6))
        dc = [BETA[i] / lam_p * p - LAM[i] * c[i] for i in range(6)]
        p += dt * dp
        c = [c[i] + dt * dc[i] for i in range(6)]
        t += dt
        if t >= nextout - 1e-12:
            out.append((t, p))
            nextout += 0.01
    return out


def donjon(path):
    txt = open(path, "rb").read().decode("latin1")
    return {round(float(b), 4): float(d) for _, b, _, d in
            re.findall(r">\|A8STEP\s+(\d+)\s+T\s+([0-9.eE+-]+)\s+POWER\s+"
                       r"([0-9.eE+-]+)\s+P/P0\s+([0-9.eE+-]+)", txt)}


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    speed = float(os.environ.get("A8_VROD", "40.0"))
    d = donjon(sys.argv[1])
    tend = max(d) if d else 1.0
    print("beta_tot %.6f (A5b at 10.9 MWd/kg), lambda from the COMPO, "
          "rho(t) from the measured ramp at %g cm/s\n" % (BETA_TOT, speed))
    print("     t s   DONJON 3-D    point kinetics at Lambda =")
    print("                          0.5 ms     1.0 ms     2.0 ms")
    pk = {lp: dict(solve(tend, speed, lp)) for lp in (0.5e-3, 1.0e-3, 2.0e-3)}
    want = [0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0]
    worst = 0.0
    for t in sorted(d):
        if not any(abs(t - w) < 5e-4 for w in want) and abs(t - tend) > 1e-9:
            continue
        vals = []
        for lp in (0.5e-3, 1.0e-3, 2.0e-3):
            key = min(pk[lp], key=lambda x: abs(x - t))
            vals.append(pk[lp][key])
        worst = max(worst, abs(d[t] - vals[1]))
        print("   %6.3f    %.5f    %.5f    %.5f    %.5f   (3-D - pk1ms "
              "%+.5f)" % (t, d[t], vals[0], vals[1], vals[2], d[t] - vals[1]))
    print()
    print("worst |3-D - point kinetics| over the reported points: %.5f in P/P0"
          % worst)
    print("The Lambda sweep spans %.5f at t = %.2f s, so a residual inside that"
          % (abs(pk[2.0e-3][min(pk[2.0e-3], key=lambda x: abs(x - tend))]
                 - pk[0.5e-3][min(pk[0.5e-3], key=lambda x: abs(x - tend))]),
             tend))
    print("spread is not evidence of a spatial effect -- it is the prompt")
    print("lifetime, which this script does not constrain.")


if __name__ == "__main__":
    main()
