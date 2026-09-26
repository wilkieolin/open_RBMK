"""
A6.3: OpenMC reference for the CPS supercells (standing rule 4).

    python cps_verify.py run        # every case not already in cps_verify.json
    python cps_verify.py table      # section worths, OpenMC vs DRAGON

Cases (cps_common.openmc_supercell):
  3x3 supercell, centre FUEL / WAT / ABS / DSP / VOID, surrounding fuel at
  dca 0.72 and 0.02, fresh and at 10 MWd/kg.  The burned fuel is OpenMC's own
  depletion on the energy-deposition scale (depl_gb10_ed) -- the same isotopics
  DRAGON reads through RbmkLibOED10 / RbmkOED10N2 -- so the comparison is
  transport alone, as oed10 / oedbest10 were for the fuel cell (Gate B).
  r45 (the true rotated CPS lattice, 7 fuel cells per CPS cell) at fresh fuel:
  the supercell-shape effect, reported, not applied.

Graphite: c_Graphite_10p, DRAGON's C12_GR (the matched basis of void_bracket B).
Statistics: 50k x 300 (50 inactive) -> sigma(k) ~ 20 pcm.
"""
import json
import os
import sys

import openmc
import openmc.deplete

import cps_common as cc

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "cps_verify.json")
RUNDIR = os.path.join(HERE, "cps_runs")
DEPL = os.path.join(HERE, "depl_gb10_ed")
THREADS = int(os.environ.get("RBMK_THREADS", 12))


def cases():
    out = []
    for bu in (0, 10):
        for dca in (0.72, 0.02):
            for t in cc.TYPES:
                if t == "FUEL" and not (bu == 0 and dca == 0.72):
                    continue            # the single-cell references exist (g10p, accident_ref)
                out.append(dict(layout="3x3", type=t, bu=bu, dca=dca))
    for dca in (0.72, 0.02):
        for t in ("WAT", "ABS", "DSP", "VOID"):
            out.append(dict(layout="r45", type=t, bu=0, dca=dca))
    # cheapest-first within priority: fresh before burned
    return sorted(out, key=lambda c: (c["bu"], c["layout"] != "3x3", c["dca"] != 0.72))


def tag(c):
    return f"{c['layout']}_{c['type']}_bu{c['bu']}_d{c['dca']}"


def burned_fuel(bu):
    from deplete_void import substeps, BU_GRID
    idx = substeps()[1][BU_GRID.index(float(bu))]
    res = openmc.deplete.Results(os.path.join(DEPL, "depletion_results.h5"))
    mats = {m.id: m for m in res.export_to_materials(idx, path=os.path.join(DEPL, "materials.xml"))}
    return {6: mats[6], 7: mats[7]}


def run():
    done = json.load(open(OUT)) if os.path.exists(OUT) else []
    have = {r["tag"] for r in done}
    for c in cases():
        if tag(c) in have:
            continue
        fuel = burned_fuel(c["bu"]) if c["bu"] else None
        model = cc.openmc_supercell(c["type"], c["layout"], dca=c["dca"], fuel=fuel)
        d = os.path.join(RUNDIR, tag(c))
        os.makedirs(d, exist_ok=True)
        sp = model.run(cwd=d, threads=THREADS, output=False)
        with openmc.StatePoint(sp) as s:
            k, sd = s.keff.nominal_value, s.keff.std_dev
        done.append(dict(c, tag=tag(c), k=k, sd=sd))
        json.dump(done, open(OUT, "w"), indent=1)
        print(f"{tag(c):28s} k = {k:.5f} +/- {sd:.5f}", flush=True)


# ------------------------------------------------------------------ table
DRA = os.path.join(os.path.dirname(HERE), "5.1", "Dragon", "Linux_aarch64")
rho = lambda k: 1.0 - 1.0 / k


def dragon_rows(deck):
    """{(bu, dca, type): k} from the CPSTAB rows of rbmk_cps_<deck>.result."""
    import re
    out = {}
    p = os.path.join(DRA, f"rbmk_cps_{deck}.result")
    if not os.path.exists(p):
        return out
    num = r"([-+]?\d+\.\d+[eE][-+]\d+)"
    for line in open(p, errors="ignore"):
        m = re.search(r">\|CPSTAB\s+" + r"\s+".join([num] * 5), line)
        if m:
            bu, dca, tf, it, k = (float(x) for x in m.groups())
            out[(int(round(bu / 1000)), round(dca, 2), cc.TYPES[int(it) - 1])] = k
    return out


def worths(K, bu, dca):
    """{'ABS-WAT': drho, ...} in pcm from {(bu, dca, type): k}; None where missing."""
    out = {}
    for t in ("ABS", "DSP", "VOID"):
        a, w = K.get((bu, dca, t)), K.get((bu, dca, "WAT"))
        out[f"{t}-WAT"] = None if a is None or w is None else 1e5 * (rho(a) - rho(w))
    return out


def table():
    omc = json.load(open(OUT)) if os.path.exists(OUT) else []
    O = {(r["bu"], r["dca"], r["type"]): r["k"] for r in omc if r["layout"] == "3x3"}
    S = {(r["bu"], r["dca"], r["type"]): r["sd"] for r in omc if r["layout"] == "3x3"}
    R = {(r["bu"], r["dca"], r["type"]): r["k"] for r in omc if r["layout"] == "r45"}
    prod, conv = {}, {}
    for f in ("a63_fresh", "a63_oed10"):
        prod.update(dragon_rows(f))
    for t in cc.TYPES[1:]:
        for f in (f"a63_fresh_conv_{t}", f"a63_oed10_conv_{t}",
                  f"a63_fresh_conv_{t}_v", f"a63_oed10_conv_{t}_v"):
            conv.update(dragon_rows(f))
    fmt = lambda x: "     --" if x is None else f"{x:+7.0f}"
    print("Section worths, pcm (rho(type) - rho(WAT)), 3 x 3 supercell")
    print(f"{'BU':>3} {'dca':>5} {'worth':>9} {'OpenMC':>7} {'sd':>4} {'prod':>7} {'conv':>7}"
          f" {'prod%':>6} {'conv%':>6} {'A-corr':>7}")
    for bu in (0, 10):
        for dca in (0.72, 0.02):
            wo, wp, wc = worths(O, bu, dca), worths(prod, bu, dca), worths(conv, bu, dca)
            for key in wo:
                sd = None
                if (bu, dca, key[:-4]) in S and (bu, dca, "WAT") in S:
                    k1, k2 = O[(bu, dca, key[:-4])], O[(bu, dca, "WAT")]
                    sd = 1e5 * ((S[(bu, dca, key[:-4])] / k1**2)**2 + (S[(bu, dca, "WAT")] / k2**2)**2)**0.5
                pct = lambda d: None if d is None or wo[key] is None else 100 * (d - wo[key]) / abs(wo[key])
                corr = None if wp[key] is None or wc[key] is None else wc[key] - wp[key]
                print(f"{bu:>3} {dca:5.2f} {key:>9} {fmt(wo[key])} {('%4.0f' % sd) if sd else '  --'}"
                      f" {fmt(wp[key])} {fmt(wc[key])} {fmt(pct(wp[key]))[1:]:>6} {fmt(pct(wc[key]))[1:]:>6}"
                      f" {fmt(corr)}")
    print("\nWorth change when the surrounding fuel voids (0.02 minus 0.72), pcm")
    for bu in (0, 10):
        for name, K in (("OpenMC", O), ("prod", prod), ("conv", conv)):
            a, b = worths(K, bu, 0.72), worths(K, bu, 0.02)
            print(f"  BU {bu:>2} {name:>6}: " + "  ".join(
                f"{k} {fmt(None if a[k] is None or b[k] is None else b[k] - a[k])}" for k in a))
    print("\nGATE A6.2: 3x3 FUEL-centre supercell vs single cell, pcm")
    for name, K, cell in (("prod", prod, {(0, 0.72): 1.313968}),):
        if (0, 0.72, "FUEL") in K:
            print(f"  {name}: {1e5 * (rho(K[(0, 0.72, 'FUEL')]) - rho(cell[(0, 0.72)])):+.1f}")
    if (0, 0.72, "FUEL") in O:
        g = {(r["variant"], round(r["dca"], 2)): r["k"] for r in json.load(open(os.path.join(HERE, "method_study.json")))}
        print(f"  OpenMC 3x3 FUEL {O[(0, 0.72, 'FUEL')]:.5f} vs g10p single cell {g[('g10p', 0.72)]:.5f}"
              f" ({1e5 * (rho(O[(0, 0.72, 'FUEL')]) - rho(g[('g10p', 0.72)])):+.0f} pcm)")
    print("\nSupercell shape (OpenMC r45 minus 3x3 worth), fresh, pcm")
    for dca in (0.72, 0.02):
        a, b = worths(O, 0, dca), worths(R, 0, dca)
        print(f"  dca {dca}: " + "  ".join(
            f"{k} {fmt(None if a[k] is None or b[k] is None else b[k] - a[k])}" for k in a))


if __name__ == "__main__":
    {"run": run, "table": table}[sys.argv[1]]()
