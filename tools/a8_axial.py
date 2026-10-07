#!/usr/bin/env python3
"""The core-integrated AXIAL power shape, read out of a DONJON listing.

Needs a deck generated with U4_PBUND=1, which prints POWER-BUND.  FLPOWB.f:52
declares it POWB(NCH,NB), so the flat record is NB blocks of NCH, and
RESPFM.f:65-72 numbers IB upward in IZ: block 1 is the core BOTTOM.

The shape is printed bottom to top as a plane power over the plane average,
and alongside it in the coordinate INSAG-7 Fig. II-9 uses -- distance below
the core TOP, D = 700 - (z - 50) cm for the 700 cm active height -- so the two
can be laid side by side without anyone redoing the flip in their head.
"""
import re
import sys

NB = 28
PITCH = 25.0


def shape(path, which=0):
    """The which-th printed POWER-BUND block (0 = first, -1 = last)."""
    txt = open(path, "rb").read().decode("latin1")
    starts = [m.start() for m in __import__("re").finditer("CONTENT OF BLOCK 'POWER-BUND", txt)]
    if not starts:
        sys.exit(f"{path}: no POWER-BUND block -- generate with U4_PBUND=1")
    i = starts[which]
    j = txt.find("\n\n\n", i)
    vals = [float(x) for x in txt[txt.index("\n", i):j].split()]
    if len(vals) % NB:
        sys.exit(f"{path}: {len(vals)} bundle powers is not a multiple of {NB}")
    nch = len(vals) // NB
    plane = [sum(vals[k * nch:(k + 1) * nch]) for k in range(NB)]
    avg = sum(plane) / NB
    return [p / avg for p in plane], nch


def main():
    for path in sys.argv[1:]:
        s, nch = shape(path)
        name = path.split("/")[-1].replace(".don.result", "")
        kpk = max(range(NB), key=lambda k: s[k])
        # the upper and lower halves' own maxima, which is what "double
        # peaked with a large upper maximum" is a statement about
        up = max(range(NB // 2, NB), key=lambda k: s[k])
        lo = max(range(NB // 2), key=lambda k: s[k])
        print(f"{name}   ({nch} channels)")
        print(f"  peak at bundle {kpk + 1} (z {50 + kpk * PITCH:.0f}-"
              f"{75 + kpk * PITCH:.0f} cm, D {700 - (kpk + 0.5) * PITCH:.0f} cm below "
              f"the top), {s[kpk]:.3f}")
        print(f"  upper-half max {s[up]:.3f} at D {700 - (up + 0.5) * PITCH:.0f}, "
              f"lower-half max {s[lo]:.3f} at D {700 - (lo + 0.5) * PITCH:.0f}, "
              f"ratio {s[up] / s[lo]:.3f}")
        print("   bundle  z_mid cm   D cm   P/<P>")
        for k in range(NB - 1, -1, -1):
            zm = 50 + (k + 0.5) * PITCH
            print(f"   {k + 1:5d}   {zm:7.1f}  {700 - (k + 0.5) * PITCH:5.0f}   "
                  f"{s[k]:.3f}  " + "#" * int(round(s[k] * 30)))
        print()


if __name__ == "__main__":
    main()
