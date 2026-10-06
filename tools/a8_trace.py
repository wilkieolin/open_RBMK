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
        for k, tt, pp, rr in rows:
            if k in (1, 2, 5, 10, 20, 50, 100, 200, 400) or k == n:
                print("     step %4d  t %7.4f s  P %10.2f MW  P/P0 %.6f"
                      "  rho %+8.2f pcm" % (k, tt, pp, rr, rho_pcm(rr)))
        print()


if __name__ == "__main__":
    main()
