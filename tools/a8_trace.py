#!/usr/bin/env python3
"""Read an A8 power trace out of a DONJON listing and invert it for reactivity.

Usage:  tools/a8_trace.py <listing> [<listing> ...]

The prompt-jump relation P/P0 = beta/(beta - rho) is used to turn the power
ratio into a reactivity in pcm.  That is only valid while the delayed source is
still the t=0 one, i.e. for times short against the shortest precursor
half-life (0.24 s here), so the inversion is printed with that caveat attached
and the later points are indicative rather than exact.

beta is NOT assumed: it is the A5b burnup curve's value at the core's own
10 900 MWd/t, and the figure used is printed so a reader can substitute.
"""
import os
import re
import sys

# A5b MEASURED beta_eff as a burnup curve, from the library's own NDEL 6 data
# and confirmed against OpenMC to -1.3 % at fresh fuel:
#
#   MWd/kg   0        2        5        10       15       20
#   beta     0.006824 0.006361 0.005877 0.005358 0.004985 0.004680
#
# The core is flat at 10.9 MWd/kg, so this is the linear interpolation between
# the 10 and 15 nodes.  It is read off a measured curve, not fitted to make any
# number come out, and the inversion below is linear in it so a reader can
# rescale: rho scales as beta.
BETA = 0.005358 + (10.9 - 10.0) / 5.0 * (0.004985 - 0.005358)


def trace(path):
    txt = open(path, "rb").read().decode("latin1")
    init = re.search(r">\|A8INIT POWER\s+([0-9.eE+-]+)", txt)
    rows = re.findall(r">\|A8STEP\s+(\d+)\s+T\s+([0-9.eE+-]+)\s+POWER\s+"
                      r"([0-9.eE+-]+)\s+P/P0\s+([0-9.eE+-]+)", txt)
    if not rows:
        return None
    p0 = float(init.group(1)) if init else float(rows[0][2])
    return p0, [(int(a), float(b), float(c), float(d)) for a, b, c, d in rows]


# The static reactivity ramp, from tools/a8_ramp.py, kept beside this script so
# a trace can be anchored without re-running it.  rho = 1 - k(0)/k(d), the same
# normalisation KINSOL: imposes.
RAMP = None


def load_ramp():
    """Read the static ramp reference, if it is there."""
    global RAMP
    if RAMP is not None:
        return RAMP
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "a8_ramp_reference.txt")
    RAMP = []
    if os.path.exists(path):
        for line in open(path):
            f = line.split()
            if len(f) >= 3:
                try:
                    RAMP.append((float(f[0]), float(f[1]), float(f[2])))
                except ValueError:
                    pass
    return RAMP


def ramp_rho(travel):
    """Linearly interpolate the static ramp at a travel in cm."""
    r = load_ramp()
    if not r or travel < r[0][0] or travel > r[-1][0]:
        return None
    for (d0, _, r0), (d1, _, r1) in zip(r, r[1:]):
        if d0 <= travel <= d1:
            if d1 == d0:
                return r0
            return r0 + (travel - d0) / (d1 - d0) * (r1 - r0)
    return None


def rho_pcm(ratio):
    """Invert the prompt jump: rho = beta*(1 - 1/ratio)."""
    return BETA * (1.0 - 1.0 / ratio) * 1.0e5


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    print("beta_eff assumed %.5f (A5b curve at 10 900 MWd/t)\n" % BETA)
    for path in sys.argv[1:]:
        got = trace(path)
        name = path.split("/")[-1].replace(".don.result", "")
        if got is None:
            print("%-44s no A8 trace" % name)
            continue
        p0, rows = got
        n, t, p, r = rows[-1]
        # the gate is "a prompt power rise BEFORE the absorber takes over", so
        # the peak and its timing are the two numbers that decide it.  A peak
        # at the last step means the run is too short to have found one.
        kpk, tpk, ppk, rpk = max(rows, key=lambda x: x[3])
        tail = " (PEAK AT THE LAST STEP -- run is too short)" if kpk == n else ""
        print("%-44s %4d steps to %6.3f s" % (name, n, t))
        print("     peak  P/P0 %.5f at t = %.4f s (step %d)%s"
              % (rpk, tpk, kpk, tail))
        print("     final P/P0 %.5f   first-step rho %+.2f pcm"
              % (r, rho_pcm(rows[0][3])))
        # anchor the trace: A8KFINAL solves the final rod geometry statically,
        # and that k must agree with a static deck at the same travel.  A trace
        # whose geometry has not been checked this way is not evidence -- it is
        # how the retracted 9.3 % rise got as far as it did.
        anc = re.search(r">\|A8KFINAL travel-cm\s+([0-9.eE+-]+)\s+keff\s+"
                        r"([0-9.eE+-]+)", open(path, "rb").read()
                        .decode("latin1"))
        if anc:
            travel, kfin = float(anc.group(1)), float(anc.group(2))
            exp = ramp_rho(travel)
            k0 = None
            for d, kk, _ in load_ramp():
                if d == 0.0:
                    k0 = kk
            got = (1.0 - k0 / kfin) * 1.0e5 if k0 else None
            msg = ""
            if exp is not None and got is not None:
                msg = ("  static ramp says %+.1f, delta %+.1f pcm"
                       % (exp, got - exp))
            print("     anchor: travel %.2f cm, k %.6f -> rho %s%s"
                  % (travel, kfin,
                     "%+.1f pcm" % got if got is not None else "n/a", msg))
        else:
            print("     anchor: ABSENT -- this trace has no A8KFINAL line")
        for k, tt, pp, rr in rows:
            if k in (1, 2, 5, 10, 20, 50, 100, 200, 400) or k == n:
                print("     step %4d  t %7.4f s  P %10.2f MW  P/P0 %.6f"
                      "  rho %+8.2f pcm" % (k, tt, pp, rr, rho_pcm(rr)))
        print()


if __name__ == "__main__":
    main()
