#!/usr/bin/env python3
"""Compare A8 transient traces from several DONJON listings on common times.

Reads every 'A8STEP n T t POWER p P/P0 r' line, and the 'A8THM' lines that
A8.3 decks add (TMAXFUEL, DCOOLMIN, NCYC, ERRCYC), and prints P/P0 for each
listing at the requested times, linearly interpolated, plus the difference
of each listing from the FIRST one.  The first listing is the reference,
so pass the finest timestep (or the coupled run) first.

    a8_compare.py [--t 0.1,0.25,0.5,1.0] <ref.result> <other.result> ...

A trace that stops early (an aborted run) is reported up to where it stops.
"""
import re
import sys

import numpy as np

STEP = re.compile(r"^>\|A8STEP\s+(\d+)\s+T\s+(\S+)\s+POWER\s+(\S+)\s+P/P0\s+(\S+)")
THM = re.compile(r"^>\|A8THM\s+(\d+)\s+T\s+(\S+)\s+TMAXFUEL\s+(\S+)\s+DCOOLMIN\s+(\S+)"
                 r"(?:\s+NCYC\s+(\S+)\s+ERRCYC\s+(\S+))?")


def trace(path):
    t, r, th = [0.0], [1.0], []
    for line in open(path, "rb").read().decode("latin1").splitlines():
        m = STEP.match(line)
        if m:
            t.append(float(m.group(2))); r.append(float(m.group(4)))
            continue
        m = THM.match(line)
        if m:
            th.append([float(m.group(k)) if m.group(k) else 0.0 for k in (2, 3, 4, 5, 6)])
    return np.array(t), np.array(r), np.array(th) if th else None


def main():
    args = sys.argv[1:]
    times = [0.1, 0.25, 0.5, 0.75, 1.0]
    if args and args[0] == "--t":
        times = [float(x) for x in args[1].split(",")]
        args = args[2:]
    tr = [trace(p) for p in args]
    print("  t, s   " + "".join(f"  {'#%d' % i:>10s}" for i in range(len(args)))
          + "".join(f"   #{i}-#0 %" for i in range(1, len(args))))
    for tq in times:
        vals = [np.interp(tq, t, r) if tq <= t[-1] + 1e-4 else np.nan for t, r, _ in tr]
        row = f"  {tq:5.3f} " + "".join(f"  {v:10.6f}" for v in vals)
        row += "".join(f"   {100 * (v - vals[0]) / vals[0]:+8.4f}" for v in vals[1:])
        print(row)
    for i, (p, (t, r, th)) in enumerate(zip(args, tr)):
        s = f"  #{i}: {p.split('/')[-1]}\n      to t = {t[-1]:.4f} s, {len(t) - 1} steps, P/P0 min {r.min():.6f} max {r.max():.6f}"
        if th is not None and len(th):
            s += (f"\n      Tfuel max {th[:, 1].max():.2f} K, D-cool min {th[:, 2].min():.5f},"
                  f" cycling channels/step max {int(th[:, 3].max())}, worst accepted {th[:, 4].max():.2e}")
        print(s)


if __name__ == "__main__":
    main()
