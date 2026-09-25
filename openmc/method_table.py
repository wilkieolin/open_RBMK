"""Collect the method-gap study into one table (PROGRESS.md, "Method gap").

DRAGON:  METHTAB rows of 5.1/Dragon/<arch>/rbmk_meth_*.result
OpenMC:  method_study.json, plus the control from run81_d*/log.txt
         (same seed and statistics as every method_study.py variant)

For each variant: k-inf at 0.72, void reactivity at 0.35 and 0.02 g/cm3, and
the change of each relative to that code's control.  Nothing here holds an
expected value.
"""
import glob
import json
import os
import platform
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ARCH = os.environ.get("DRAGON_ARCH", f"Linux_{platform.machine()}")
DRA = os.path.join(ROOT, "5.1", "Dragon", ARCH)
NUM = r"([-+]?\d+\.\d+[eE][-+]\d+)"
rho = lambda k: 1 - 1 / k
DCAS = (0.72, 0.35, 0.02)


def dragon():
    out = {}
    for f in sorted(glob.glob(os.path.join(DRA, "rbmk_meth_*.result"))):
        vid = os.path.basename(f)[len("rbmk_meth_"):-len(".result")]
        rows = {}
        for line in open(f, errors="ignore"):
            m = re.search(r"METHTAB\s+\d+\s+" + NUM + r"\s+" + NUM, line)
            if m:
                rows[round(float(m.group(1)), 2)] = (float(m.group(2)), 0.0)
        if rows:
            out[vid] = rows
    return out


def openmc():
    out = {"control": {}}
    for d in DCAS:
        log = os.path.join(HERE, f"run81_d{d}", "log.txt")
        if os.path.exists(log):
            m = re.search(r"RESULT dca=\S+ k=(\S+) \+/- (\S+)", open(log).read())
            out["control"][d] = (float(m.group(1)), float(m.group(2)))
    p = os.path.join(HERE, "method_study.json")
    if os.path.exists(p):
        for r in json.load(open(p)):
            out.setdefault(r["variant"], {})[round(r["dca"], 2)] = (r["k"], r["sd"])
    return out


def drho(rows, d):
    """Void reactivity (pcm) at density d, and its 1-sigma."""
    if 0.72 not in rows or d not in rows:
        return None
    (kn, sn), (k, s) = rows[0.72], rows[d]
    return (1e5 * (rho(k) - rho(kn)),
            1e5 * ((s / k**2) ** 2 + (sn / kn**2) ** 2) ** 0.5)


def fmt(x, sig=True):
    if x is None:
        return f"{'--':>14}"
    return f"{x[0]:>+8.0f} ±{x[1]:<4.0f}" if (sig and x[1]) else f"{x[0]:>+8.0f}      "


def table(name, data, ctrl):
    print(f"\n{name}")
    print(f"  {'variant':<12}{'k-inf 0.72':>12}{'dk pcm':>10}"
          f"{'drho 0.35':>15}{'drho 0.02':>15}{'d(drho0.02)':>14}")
    c = data.get(ctrl, {})
    c02 = drho(c, 0.02)
    for vid, rows in data.items():
        k = rows.get(0.72)
        dk = (1e5 * (rho(k[0]) - rho(c[0.72][0]))) if (k and 0.72 in c) else None
        r02 = drho(rows, 0.02)
        dd = (r02[0] - c02[0]) if (r02 and c02) else None
        print(f"  {vid:<12}{(k[0] if k else float('nan')):>12.6f}"
              f"{(f'{dk:+10.0f}' if dk is not None else '        --')}"
              f"{fmt(drho(rows, 0.35))}{fmt(r02)}"
              f"{(f'{dd:+14.0f}' if dd is not None else '            --')}")


if __name__ == "__main__":
    D, O = dragon(), openmc()
    table("DRAGON (deterministic; no statistical error)", D, "ctrl")
    table("OpenMC (seed-matched to control; sigma per value, not per difference)", O, "control")
    if "ctrl" in D and O.get("control"):
        print("\nGap, OpenMC control - DRAGON ctrl:")
        for d in (0.35, 0.02):
            o, g = drho(O["control"], d), drho(D["ctrl"], d)
            if o and g:
                print(f"  drho({d}) : OpenMC {o[0]:+.0f} ± {o[1]:.0f}   DRAGON {g[0]:+.0f}"
                      f"   gap {o[0]-g[0]:+.0f} pcm")
