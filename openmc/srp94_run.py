"""Run the SRP-1994 single-cell benchmark in OpenMC and compare with everything.

    python srp94_run.py run  <Zr|Al> [graphite_tsl]   # watered + voided, appends srp94_openmc.json
    python srp94_run.py table                          # OpenMC, our DRAGON, and [ALX98]'s codes

Same statistics and seed as method_study.py (50k x 250 active).  DRAGON values
are read from the SRP94TAB rows of 5.1/Dragon/<arch>/rbmk_srp94_*.result.
Nothing here holds an expected value; PUBLISHED values are [ALX98]'s own.
"""
import glob
import json
import os
import platform
import re
import sys

import srp94_common as S

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "srp94_openmc.json")
DRA = os.path.join(os.path.dirname(HERE), "5.1", "Dragon",
                   os.environ.get("DRAGON_ARCH", f"Linux_{platform.machine()}"))


def run(tube, tsl):
    import openmc
    rec = dict(tube=tube, graphite_tsl=tsl)
    for tag, watered in (("watered", True), ("voided", False)):
        d = os.path.join(HERE, f"srp94_{tube}_{tsl}_{tag}")
        os.makedirs(d, exist_ok=True)
        sp = S.openmc_model(tube, watered, graphite_tsl=tsl).run(
            cwd=d, output=False, threads=int(os.environ.get("RBMK_THREADS", os.cpu_count())))
        with openmc.StatePoint(sp) as s:
            rec[tag] = (s.keff.nominal_value, s.keff.std_dev)
        print(f"SRP94 OpenMC {tube} {tsl} {tag}: k = {rec[tag][0]:.5f} +/- {rec[tag][1]:.5f}",
              flush=True)
    recs = json.load(open(OUT)) if os.path.exists(OUT) else []
    recs = [r for r in recs if not (r["tube"] == tube and r["graphite_tsl"] == tsl)]
    json.dump(recs + [rec], open(OUT, "w"), indent=1)


def dragon():
    out = {}
    for f in sorted(glob.glob(os.path.join(DRA, "rbmk_srp94_*.result"))):
        vid = os.path.basename(f)[len("rbmk_srp94_"):-len(".result")]
        k = {}
        for line in open(f, errors="ignore"):
            m = re.search(r"SRP94TAB\s+(\d)\s+([-+]?\d+\.\d+[eE][-+]\d+)", line)
            if m:
                k[int(m.group(1))] = float(m.group(2))
        if len(k) == 2:
            out[vid] = (S.DRAGON_VARIANTS[vid][0], k[1], k[2])
    return out


def table():
    rows = [(f"{c} ({lib})", t, kw, kv, dk, None) for c, lib, t, kw, kv, dk in S.PUBLISHED]
    if os.path.exists(OUT):
        for r in json.load(open(OUT)):
            (kw, sw), (kv, sv) = r["watered"], r["voided"]
            rows.append((f"OpenMC (VIII.1, {r['graphite_tsl']})", r["tube"], kw, kv,
                         100 * (kv - kw), 100 * (sw**2 + sv**2) ** 0.5))
    for vid, (tube, kw, kv) in dragon().items():
        rows.append((f"DRAGON {vid} (VIII.1)", tube, kw, kv, 100 * (kv - kw), None))
    for tube in ("Zr", "Al"):
        print(f"\n{tube} pressure tube      k-inf watered  k-inf voided   void dk (%)")
        for name, t, kw, kv, dk, sig in rows:
            if t == tube:
                e = f" +/- {sig:.2f}" if sig else ""
                print(f"  {name:<34s} {kw:>9.4f}     {kv:>9.4f}     {dk:>6.2f}{e}")


if __name__ == "__main__":
    if sys.argv[1] == "run":
        run(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "c_Graphite")
    else:
        table()
