#!/usr/bin/env python3
"""Where the steam is during the transient: reduce U4_KINVOID=1 dumps.

At each A8SHAPE time the deck prints POWER-BUND and the fuel map's D-COOL,
both NCH x NB with block 1 the core BOTTOM (FLPOWB.f:52, RESPFM.f:65-72).
Per bundle this prints the plane power share, the mean coolant density, and an
APPROXIMATE void fraction (rho_f - rho)/(rho_f - rho_g) with saturated values
at 7.38 MPa (0.7345 / 0.0393 g/cm3, the liquid value read off THM's own
boiling-onset plane); subcooled liquid denser than rho_f counts as zero void.
The lower/upper half split is the test of INSAG-7 p. 64's claim that a power
increase voids the LOWER core most.

Usage: a8_voidz.py result [--every]
"""
import re
import sys

NB = 28
RF, RG = 0.7345, 0.0393


def blocks(txt, name):
    out = []
    for m in re.finditer(r"CONTENT OF BLOCK '%s\s*'" % re.escape(name), txt):
        j = txt.find("\n\n\n", m.end())
        out.append([float(x) for x in txt[txt.index("\n", m.end()):j].split()])
    return out


def main():
    path = sys.argv[1]
    txt = open(path, "rb").read().decode("latin1")
    times = [float(t) for t in re.findall(r">\|A8SHAPE\s+\d+\s+T\s+([0-9.eE+-]+)", txt)]
    pw, dc = blocks(txt, "POWER-BUND"), blocks(txt, "P-VALUE")
    pp = {float(t): float(p) for t, p in
          re.findall(r">\|A8STEP\s+\d+\s+T\s+([0-9.eE+-]+)\s+POWER\s+\S+\s+P/P0\s+([0-9.eE+-]+)", txt)}
    assert len(times) == len(pw) == len(dc), (len(times), len(pw), len(dc))
    for t, p, d in zip(times, pw, dc):
        nch = len(d) // NB
        assert nch * NB == len(d) == len(p)
        pl = [sum(p[k * nch:(k + 1) * nch]) for k in range(NB)]
        ptot = sum(pl)
        rho = [sum(d[k * nch:(k + 1) * nch]) / nch for k in range(NB)]
        vd = [sum(max(0.0, (RF - x) / (RF - RG)) for x in d[k * nch:(k + 1) * nch]) / nch
              for k in range(NB)]
        boil = [sum(1 for x in d[k * nch:(k + 1) * nch] if x < RF) / nch for k in range(NB)]
        pk = min(pp, key=lambda x: abs(x - t)) if pp else None
        print(f"t = {t:.2f} s   P/P0 {pp[pk]:.3f}   min D-COOL {min(d):.4f}" if pk is not None
              else f"t = {t:.2f} s")
        lo, hi = sum(vd[:NB // 2]) / (NB // 2), sum(vd[NB // 2:]) / (NB - NB // 2)
        print(f"   mean void: lower half {lo:.4f}, upper half {hi:.4f};"
              f" power share lower half {sum(pl[:NB // 2]) / ptot:.3f}")
        if "--every" in sys.argv or t == times[-1] or len(times) <= 3:
            print("   bundle  D cm  power   rho     void   boiling")
            for k in range(NB - 1, -1, -1):
                print(f"   {k + 1:5d}  {700 - (k + 0.5) * 25:4.0f}  {pl[k] / ptot:.4f}  "
                      f"{rho[k]:.4f}  {vd[k]:.4f}  {boil[k]:.3f}")


if __name__ == "__main__":
    main()
