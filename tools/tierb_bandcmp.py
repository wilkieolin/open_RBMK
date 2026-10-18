#!/usr/bin/env python3
"""Tier B coupled trace (test/b4_coupled.jl) against its DONJON listing.
Usage: tools/tierb_bandcmp.py <stem> [trace suffix ...]   (suffix '' = THMTRS port, '_newton', '_colthm')
Prints, per trace: time of 530 MW, peak (P/P0 and time), energy to DONJON's peak, end time."""
import os, re, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
P0 = 200.0                                        # MW (A8INIT POWER, checked below)

def donjon(stem):
    txt = open(os.path.join(ROOT, "5.1/Donjon/Linux_aarch64", stem + ".don.result"), "rb").read().decode("latin1")
    p0 = float(re.search(r">\|A8INIT POWER\s+([0-9.eE+-]+)", txt).group(1))
    rows = re.findall(r">\|A8STEP\s+(\d+)\s+T\s+([0-9.eE+-]+)\s+POWER\s+([0-9.eE+-]+)\s+P/P0\s+([0-9.eE+-]+)", txt)
    return p0, [(0.0, 1.0)] + [(float(t), float(r)) for _, t, _, r in rows]

def tierb(stem, suf):
    f = os.path.join(ROOT, "tierb/xs", stem + "_tbd0", "b4_trace_dt0.01%s.txt" % suf)
    if not os.path.exists(f):
        return None
    return [(0.0, 1.0)] + [tuple(float(x) for x in l.split()[:2]) for l in open(f) if l.strip() and not l.startswith("#")]

def summary(rows, p0, tpk=None):
    e = 0.0; E = {}
    for (t0, r0), (t1, r1) in zip(rows, rows[1:]):
        e += 0.5 * (r0 + r1) * p0 * (t1 - t0) / 1e3; E[round(t1, 2)] = e
    pk = max(rows, key=lambda r: r[1])
    t530 = next((t for t, r in rows if r * p0 >= 530.0), float("nan"))
    tp = round(tpk if tpk is not None else pk[0], 2)
    return dict(t530=t530, peak=pk[1], tpeak=pk[0], e_to_peak=E.get(tp, float("nan")), end=rows[-1][0])

stem = sys.argv[1]; sufs = sys.argv[2:] or [""]
p0, D = donjon(stem)
assert abs(p0 - P0) < 1.0, p0
sd = summary(D, p0)
print(stem)
print("  %-10s t530 %.2f s  peak %8.2fx at %.2f s  E to peak %7.2f GJ  end %.2f s" %
      ("DONJON", sd["t530"], sd["peak"], sd["tpeak"], sd["e_to_peak"], sd["end"]))
for suf in sufs:
    T = tierb(stem, suf)
    if T is None:
        print("  %-10s (no trace)" % (suf or "thmtrs")); continue
    st = summary(T, p0, sd["tpeak"])
    print("  %-10s t530 %.2f s  peak %8.2fx at %.2f s  E to DONJON peak %7.2f GJ (%+.1f %%)  end %.2f s" %
          (suf or "thmtrs", st["t530"], st["peak"], st["tpeak"], st["e_to_peak"],
           100 * (st["e_to_peak"] / sd["e_to_peak"] - 1), st["end"]))
