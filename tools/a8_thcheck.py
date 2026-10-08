#!/usr/bin/env python3
"""Where the steam is: reduce a U4_THDUMP=1 result to axial profiles.

THM stores, per channel, 32 axial values ordered with the flow (inlet first):
two lower-reflector planes are NOT first -- the 28 heated planes are indices
2..29 and the four unheated entries are the reflector planes.  The heated
planes are found from POWER > 0, so nothing about the ordering is assumed
beyond 'enthalpy rises along the index', which is checked.

Prints, per bundle from the bottom (inlet) up: the mean void fraction, the
power-weighted mean void, the fraction of channels with any vapour, and the
core energy balance.  With two files it prints the per-plane change, which is
INSAG-7 p. 64's claim made testable: "a small power increase ... could result
in a much higher increase in the volumetric steam quality in the lower part of
the core than in the upper part".

Usage: a8_thcheck.py result [result2]
"""
import re
import sys

BLK = re.compile(r"CONTENT OF BLOCK '(\w[\w-]*)\s*'\s+LENGTH =\s+(\d+)")
NUM = re.compile(r"[-+]?\d\.\d+E[-+]\d+")


def read(path):
    txt = open(path, "rb").read().decode("latin1")
    parts = re.split(r">\|THDUMP\s+(\d+)", txt)
    chans = {}
    for k in range(1, len(parts), 2):
        ich, body = int(parts[k]), parts[k + 1]
        rec, pos = {}, [(m.group(1), int(m.group(2)), m.end())
                        for m in BLK.finditer(body)]
        for name, n, e in pos:
            vals = [float(x) for x in NUM.findall(body[e:e + 20 * n + 400])][:n]
            assert len(vals) == n, (path, ich, name)
            rec[name] = vals
        chans[ich] = rec
    assert len(chans) == 1661, (path, len(chans))
    return chans


def profiles(chans):
    first = next(iter(chans.values()))
    heat = [i for i, p in enumerate(first["POWER"]) if p > 0.0]
    nz = len(heat)
    void = [0.0] * nz
    vw = [0.0] * nz
    pw = [0.0] * nz
    boil = [0] * nz
    onset = []
    ptot = 0.0
    for c in chans.values():
        h = [c["ENTHALPY"][i] for i in heat]
        assert all(b >= a - 1e-6 for a, b in zip(h, h[1:])), "enthalpy not rising"
        on = None
        for k, i in enumerate(heat):
            e, p = c["EPSILON"][i], c["POWER"][i]
            void[k] += e
            vw[k] += e * p
            pw[k] += p
            ptot += p
            if e > 0.0:
                boil[k] += 1
                if on is None:
                    on = k
        onset.append(nz if on is None else on)
    n = len(chans)
    return dict(nz=nz, void=[v / n for v in void],
                vw=[a / b for a, b in zip(vw, pw)],
                boil=[b / n for b in boil], onset=onset, ptot=ptot,
                pz=[p / ptot for p in pw])


def summary(tag, pr):
    nz = pr["nz"]
    print(f"{tag}: sum of POWER {pr['ptot'] / 1e6:.2f} MW over {nz} heated planes")
    on = sorted(pr["onset"])
    q = lambda f: on[int(f * (len(on) - 1))]
    print("  boiling onset, bundle from the bottom (median / 10 % / 90 %):"
          f" {q(.5) + 1} / {q(.1) + 1} / {q(.9) + 1};"
          f" channels with no vapour: {sum(1 for x in on if x == nz)}")


def main():
    files = sys.argv[1:]
    if not files:
        sys.exit(__doc__)
    prs = [read(f) for f in files]
    prs = [profiles(c) for c in prs]
    for f, p in zip(files, prs):
        summary(f.split("/")[-1], p)
    nz = prs[0]["nz"]
    hdr = "  bundle  D cm   power   void   P-wtd void  boiling"
    if len(prs) == 2:
        hdr += "  | void 2   d void   boiling 2"
    print(hdr)
    for k in range(nz - 1, -1, -1):              # top of core first
        a = prs[0]
        d = (nz - 1 - k) * 25.0 + 12.5          # depth below the core top
        line = (f"  {k + 1:5d}  {d:5.0f}  {a['pz'][k]:.4f}  {a['void'][k]:.4f}"
                f"  {a['vw'][k]:.4f}     {a['boil'][k]:.3f}")
        if len(prs) == 2:
            b = prs[1]
            line += (f"  | {b['void'][k]:.4f}  {b['void'][k] - a['void'][k]:+.4f}"
                     f"   {b['boil'][k]:.3f}")
        print(line)
    for j, p in enumerate(prs):
        lo = sum(p["void"][:nz // 2]) / (nz // 2)
        hi = sum(p["void"][nz // 2:]) / (nz - nz // 2)
        print(f"file {j + 1}: mean void lower half {lo:.4f}, upper half {hi:.4f}")


if __name__ == "__main__":
    main()
