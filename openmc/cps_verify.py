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
    # A6.3 Track C: the same WAT supercell with the CPS water on a draglib
    # temperature node (293.6 K), where DRAGON does no interpolation.  Pairs
    # with the rbmk_cps_a63_twat deck.  OpenMC has 294 K, so it barely
    # interpolates at either temperature; DRAGON spans 29.5 K at 323.15.
    for dca in (0.72, 0.02):
        out.append(dict(layout="3x3", type="WAT", bu=0, dca=dca, t_wat=293.6))
    # cheapest-first within priority: fresh before burned
    return sorted(out, key=lambda c: (c["bu"], c["layout"] != "3x3", c["dca"] != 0.72))


def tag(c):
    t = f"{c['layout']}_{c['type']}_bu{c['bu']}_d{c['dca']}"
    return t + (f"_tw{c['t_wat']:g}" if "t_wat" in c else "")


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
        kw = {k: v for k, v in c.items()
              if k not in ("layout", "type", "bu", "dca")}
        model = cc.openmc_supercell(c["type"], c["layout"], dca=c["dca"], fuel=fuel, **kw)
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
    pat = r">\|CPSTAB\s+" + r"\s+".join([num] * 3) + r"\s+(\d+)\s+" + num
    for line in open(p, errors="ignore"):
        m = re.search(pat, line)
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
    # A worth is a difference of two k's, so a worth error says nothing about
    # WHICH of the two states is wrong.  This does: it localises the residual.
    print("\nABSOLUTE k of the supercell, DRAGON minus OpenMC, pcm on rho")
    print(f"{'BU':>3} {'dca':>5} {'type':>5} {'OpenMC k':>9} {'prod k':>9} {'d_rho':>7}"
          f" {'conv k':>9} {'d_rho':>7}")
    for bu in (0, 10):
        for dca in (0.72, 0.02):
            for t in cc.TYPES[1:]:
                o = O.get((bu, dca, t))
                if o is None:
                    continue
                d = lambda x: "     --" if x is None else f"{1e5 * (rho(x) - rho(o)):+7.0f}"
                g = lambda x: "       --" if x is None else f"{x:9.5f}"
                p, c = prod.get((bu, dca, t)), conv.get((bu, dca, t))
                print(f"{bu:>3} {dca:5.2f} {t:>5} {o:9.5f} {g(p)} {d(p)} {g(c)} {d(c)}")


# ------------------------------------------------------- GATE A6.4 (a64 decks)
DON = os.path.join(os.path.dirname(HERE), "5.1", "Donjon", "Linux_aarch64")


def _rows(path, key):
    import re
    out = {}
    if not os.path.exists(path):
        return out
    num = r"([-+]?\d+\.\d+[eE][-+]\d+)"
    pat = r">\|" + key + r"\s+" + r"\s+".join([num] * 3) + r"\s+(\d+)\s+" + num
    for line in open(path, errors="ignore"):
        m = re.search(pat, line)
        if m:
            bu, dca, tf, it, k = (float(x) for x in m.groups())
            out[(int(round(bu)), round(dca, 2), int(tf))] = (cc.TYPES[int(it) - 1], k)
    return out


def a64():
    """GATE A6.4: DONJON on the homogenised supercell vs DRAGON's own k-inf.
      A64S  all nine cells from the CPS MULTICOMPO -- tests SPH + homogenisation
            + the DONJON solver alone.  Must reproduce DRAGON.
      A64V  the eight fuel cells from the FUEL MULTICOMPO instead (what the core
            will actually do) -- adds the error of using infinite-lattice fuel
            data next to a rod.
      A64M  as A64V but with the core's old MCFD 1 discretisation, for scale."""
    print("GATE A6.4: DONJON on the homogenised 3 x 3 supercell vs DRAGON, pcm")
    print(f"  {'state':>22} {'type':>5} {'DRAGON k':>9} {'A64S':>7} {'A64V':>7} {'A64M':>7}")
    D, S_, V, M = {}, {}, {}, {}
    for t in cc.TYPES[1:]:
        dp = os.path.join(DRA, f"rbmk_cps_a64_{t}.result")
        for (bu, dca, tf), (ty, k) in _rows(dp, "CPSTAB").items():
            D[(bu, dca, tf, ty)] = k
        p = os.path.join(DON, f"rbmk_cps_a64v_{t}.don.result")
        for tag, dst in (("A64S", S_), ("A64V", V), ("A64M", M)):
            for (bu, dca, tf), (ty, k) in _rows(p, tag).items():
                dst[(bu, dca, tf, ty)] = k
    for key in sorted(V, key=lambda k: (k[0], -k[1], k[2], k[3])):
        bu, dca, tf, ty = key
        d = D.get(key)
        if d is None:
            continue
        f = lambda x: "     --" if x is None else f"{1e5 * (rho(x) - rho(d)):+7.0f}"
        print(f"  BU {bu:>6.0f} dca {dca:4.2f} TF {tf:4d} {ty:>5} {d:9.6f} "
              f"{f(S_.get(key))} {f(V.get(key))} {f(M.get(key))}")
    print("\n  section worths (rho(type) - rho(WAT)), pcm, and the gate (1 %):")
    states = sorted({(k[0], k[1], k[2]) for k in V})
    err = {"V": {}, "M": {}}
    for st in states:
        w = lambda src: {t: (1e5 * (rho(src[st + (t,)]) - rho(src[st + ("WAT",)])))
                         for t in ("ABS", "DSP", "VOID") if st + (t,) in src and st + ("WAT",) in src}
        wd, wv, ws, wm = w(D), w(V), w(S_), w(M)
        for t in wd:
            if t not in wv:
                continue
            e_v = 100 * (wv[t] - wd[t]) / abs(wd[t])
            e_s = 100 * (ws[t] - wd[t]) / abs(wd[t]) if t in ws else float("nan")
            err["V"].setdefault(t, []).append(e_v)
            if t in wm:
                err["M"].setdefault(t, []).append(100 * (wm[t] - wd[t]) / abs(wd[t]))
            print(f"  BU {st[0]:>6.0f} dca {st[1]:4.2f} TF {st[2]:4d} {t + '-WAT':>9}: "
                  f"DRAGON {wd[t]:+7.0f}   A64S {ws.get(t, float('nan')):+7.0f} ({e_s:+5.1f} %)"
                  f"   A64V {wv[t]:+7.0f} ({e_v:+5.1f} %)  {'PASS' if abs(e_v) <= 1 else 'FAIL'}")
    # The discretisation the CORE uses, over every state.  A2 chose MCFD 1 for
    # speed, before any rod cell existed; one mesh-centred point per 25 cm node
    # cannot represent the flux depression in a black absorber.
    print("\n  DISCRETISATION: worth error vs DRAGON over all states, %")
    print(f"  {'worth':>9} {'DUAL 1 1 (A64V)':>22} {'MCFD 1 (A64M)':>22}")
    for t in ("ABS", "DSP", "VOID"):
        rng = lambda e: "--" if not e.get(t) else f"{min(e[t]):+.1f} to {max(e[t]):+.1f}"
        print(f"  {t + '-WAT':>9} {rng(err['V']):>22} {rng(err['M']):>22}")


if __name__ == "__main__":
    {"run": run, "table": table, "a64": a64}[sys.argv[1]]()
