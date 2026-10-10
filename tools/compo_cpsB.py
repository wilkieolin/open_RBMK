#!/usr/bin/env python3
"""CPS-channel worths corrected to OpenMC: the CPS analogue of bracket B.

PROGRESS (35).  Against OpenMC's 3 x 3 supercell (openmc/cps_verify.py), the
production CPS MULTICOMPO is biased on both rod sections at once, and both in
the direction that weakens the positive scram:
  - DRAGON (production) vs OpenMC, 10 MWd/kg, dca 0.72: absorber worth too
    STRONG, displacer worth too WEAK (cps_verify.py table, 'prod');
  - DONJON on the homogenised supercell with fuel-COMPO neighbours (A64V, what
    the core does) vs DRAGON: a further displacer deficit (cps_verify.py a64).
This tool rebuilds the ABS and DSP COMPOs so that the CORE-EQUIVALENT
supercell (A64V: eight fuel-COMPO cells round one CPS cell, DUAL 1 1) carries
OpenMC's section worth at the state the core reads (burnup 10 900, DCA 0.72,
TF 900 -- the generator's MACREF block):

    target(T) = W_DRAGON(T; 10.9) x W_OpenMC(T; 10) / W_prod(T; 10)

i.e. DRAGON's own worth at the core state, scaled by the measured OpenMC/DRAGON
ratio at the nearest OpenMC point.  Nothing is fitted to the accident.

The CPS COMPO is macroscopic: every (mixture, calculation) holds one *MAC*RES
isotope.  Mixture 5 (the CPS cell) of COMPO T becomes
    Sigma' = Sigma_WAT + f_T (Sigma_T - Sigma_WAT)
record by record (cross sections, scattering, transport), at all 18 points,
with f_T found by secant iteration on the A64V deck.  f = 1 is the original.

  usage: compo_cpsB.py fit            # iterate f_ABS, f_DSP; write the COMPOs
         compo_cpsB.py build fA fD    # write the COMPOs for given factors
Run with the OpenMC venv python (it reads openmc/cps_verify.py's tables).
"""
import hashlib
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "openmc"))
from compo_voidB import parse, nums, fmt_reals  # noqa: E402

COMPO = os.path.join(ROOT, "5.1", "Dragon", "compo")
DON = os.path.join(ROOT, "5.1", "Donjon")
DATA = os.path.join(ROOT, "decks", "Donjon", "data")
MIX = 5
# records combined linearly; flux weights, 1/v, energies and the scattering
# index arrays are left as they are (checked identical below)
LIN = ("NTOT0", "NTOT1", "STRD", "SIGS00", "SCAT00", "SIGS01", "SCAT01",
       "NG", "NA", "TRANC", "H-FACTOR")
STATE = (10900.0, 0.72, 900.0)


def mixture_records(recs, mix):
    """{calc element: {record name: index}} for the *MAC*RES isotope of one
    mixture.  Layout (see the dump in PROGRESS (35)): level-3 element = mixture,
    level-5 element = calculation, level-8 records = the isotope's data."""
    out, inmix, calc = {}, False, None
    for k, r in enumerate(recs):
        if r["level"] == 3 and r["elem"] is not None:
            inmix = (r["elem"] == mix)
            calc = None
            continue
        if not inmix:
            continue
        if r["level"] == 5 and r["elem"] is not None:
            calc = out.setdefault(r["elem"], {})
            continue
        if r["level"] == 8 and calc is not None and r["name"]:
            calc[r["name"]] = k
    return out


def build(fa, fd):
    lw, rw = parse(os.path.join(COMPO, "_CCompoWAT"))
    mw = mixture_records(rw, MIX)
    assert len(mw) == 18, len(mw)
    tag = hashlib.md5(f"{fa:.6f} {fd:.6f}".encode()).hexdigest()[:6]
    paths = {}
    for t, f in (("ABS", fa), ("DSP", fd)):
        lt, rt = parse(os.path.join(COMPO, f"_CCompo{t}"))
        mt = mixture_records(rt, MIX)
        assert sorted(mt) == sorted(mw)
        edits = []
        for c in mt:
            for nm in ("NJJS00", "IJJS00", "NJJS01", "IJJS01"):
                assert nums(lt, rt[mt[c][nm]], int) == nums(lw, rw[mw[c][nm]], int), (t, c, nm)
            for nm in LIN:
                if nm not in mt[c]:
                    continue
                a = nums(lt, rt[mt[c][nm]])
                w = nums(lw, rw[mw[c][nm]])
                new = [wi + f * (ai - wi) for ai, wi in zip(a, w)]
                edits.append((rt[mt[c][nm]], new))
        out = list(lt)
        for r, new in sorted(edits, key=lambda e: -e[0]["d0"]):
            out[r["d0"]:r["d1"]] = fmt_reals(new)
        p = os.path.join(COMPO, f"_CCompo{t}cB")
        with open(p, "wb") as fh:
            fh.write("\n".join(out).encode("latin1"))
        paths[t] = p
    return tag, paths


def deck(name, files):
    """One-state A64V deck: centre CPS cell from each listed COMPO file."""
    with open(os.path.join(DATA, "rbmk_cps_a64v_DSP.don")) as fh:
        src = fh.read()
    geo = src[src.index("GEOM := GEO:"):src.index("\nMACRO := NCR:")]
    bu, dca, tf = STATE
    lines = ["*  compo_cpsB.py fit deck: A64V at the core's CPS state.",
             "LINKED_LIST FCpo CCpo MACRO GEOM TRACK TRKFD GEOS TRKS SYSTEM FLUX ;",
             "SEQ_ASCII   _ACompo :: FILE './_ACompo' ;"]
    for i, (lab, f) in enumerate(files):
        lines.append(f"SEQ_ASCII   C{i} :: FILE './{os.path.basename(f)}' ;")
    lines += ["MODULE      NCR: GEO: TRIVAT: TRIVAA: FLUD: GREP: DELETE: END: ;",
              "REAL kinf ;", "FCpo := _ACompo ;", geo]
    for i, (lab, f) in enumerate(files):
        lines += [f"CCpo := C{i} ;",
                  "MACRO := NCR: FCpo CCpo :: EDIT 0 MACRO LINEAR NMIX 2",
                  "  COMPO FCpo 'EDIRBMK'",
                  f"  MIX 1 FROM 1 SET 'burnup' {bu} SET 'DCA' {dca} SET 'TF' {tf}"
                  " SET 'TG' 750.0 ENDMIX",
                  "  COMPO CCpo 'EDICPS'",
                  f"  MIX 2 FROM 5 SET 'burnup' {bu} SET 'DCA' {dca} SET 'TF' {tf} ENDMIX ;",
                  "SYSTEM := TRIVAA: MACRO TRACK :: EDIT 0 ;",
                  "FLUX := FLUD: SYSTEM TRACK :: EDIT 0 EXTE 1.0E-7 ;",
                  "GREP: FLUX :: GETVAL 'K-EFFECTIVE' 1 >>kinf<< ;",
                  f'ECHO "CPSB {lab}" kinf ;',
                  "MACRO SYSTEM FLUX CCpo := DELETE: MACRO SYSTEM FLUX CCpo ;"]
    lines += [f'ECHO "{name[:-4]} completed" ;', "END: ;", "QUIT ."]
    with open(os.path.join(DATA, name), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    acc = ("#!/bin/sh\nsrc=\"$1\"/../Dragon/compo\n"
           "cp \"$src\"/_ACompo . || exit 1\n"
           + "".join(f"cp {f} . || exit 1\n" for _, f in files))
    with open(os.path.join(DATA, name + ".access"), "w") as fh:
        fh.write(acc)
    os.chmod(os.path.join(DATA, name + ".access"), 0o755)
    for ext in ("", ".access"):
        dst = os.path.join(DON, "data", name + ext)
        if not os.path.lexists(dst):
            os.symlink(os.path.join(DATA, name + ext), dst)
    res = os.path.join(DON, "Linux_aarch64", name + ".result")
    if os.path.exists(res):
        os.remove(res)
    subprocess.run(["./rdonjon", name], cwd=DON, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
    txt = open(res, "rb").read().decode("latin1")
    if not re.search(r">\|" + re.escape(name[:-4]) + " completed", txt):
        sys.exit(f"{name}: did not complete")
    return {m.group(1): float(m.group(2))
            for m in re.finditer(r">\|CPSB (\S+)\s+(\S+)", txt)}


def rho(k):
    return 1.0 - 1.0 / k


def targets():
    import cps_verify as cv
    import json
    omc = [r for r in json.load(open(cv.OUT)) if "t_wat" not in r and r["layout"] == "3x3"]
    O = {(r["bu"], r["dca"], r["type"]): r["k"] for r in omc}
    prod = {}
    for f in ("a63_fresh", "a63_oed10"):
        prod.update(cv.dragon_rows(f))
    D = {}
    for t in ("WAT", "ABS", "DSP"):
        p = os.path.join(cv.DRA, f"rbmk_cps_a64_{t}.result")
        for (bu, dca, tf), (ty, k) in cv._rows(p, "CPSTAB").items():
            D[(bu, dca, tf, ty)] = k
    key = lambda t: (int(STATE[0]), STATE[1], int(STATE[2]), t)
    out = {}
    for t in ("ABS", "DSP"):
        wd = 1e5 * (rho(D[key(t)]) - rho(D[key("WAT")]))
        wo = 1e5 * (rho(O[(10, 0.72, t)]) - rho(O[(10, 0.72, "WAT")]))
        wp = 1e5 * (rho(prod[(10, 0.72, t)]) - rho(prod[(10, 0.72, "WAT")]))
        out[t] = dict(dragon=wd, openmc10=wo, prod10=wp, target=wd * wo / wp)
    return out


def worth(k, t, w="WAT"):
    return 1e5 * (rho(k[t]) - rho(k[w]))


def main():
    mode = sys.argv[1]
    if mode == "build":
        tag, p = build(float(sys.argv[2]), float(sys.argv[3]))
        print(tag, p)
        return
    T = targets()
    for t, v in T.items():
        print(f"# {t}: DRAGON(10.9) {v['dragon']:+.1f}  OpenMC(10) {v['openmc10']:+.1f}"
              f"  prod(10) {v['prod10']:+.1f}  -> target {v['target']:+.1f} pcm")
    W = os.path.join(COMPO, "_CCompoWAT")
    k0 = deck("rbmk_cps_cB_base.don", [("WAT", W),
                                        ("ABS", os.path.join(COMPO, "_CCompoABS")),
                                        ("DSP", os.path.join(COMPO, "_CCompoDSP"))])
    w0 = {t: worth(k0, t) for t in ("ABS", "DSP")}
    print(f"# A64V f=1: ABS {w0['ABS']:+.1f}  DSP {w0['DSP']:+.1f} pcm")
    f = {"ABS": 1.0, "DSP": 1.0}
    wprev = dict(w0)
    fprev = dict(f)
    # first guess: worth ~ f
    f = {t: T[t]["target"] / w0[t] for t in f}
    for it in range(8):
        tag, p = build(f["ABS"], f["DSP"])
        k = deck("rbmk_cps_cB_fit.don", [("WAT", W), ("ABS", p["ABS"]), ("DSP", p["DSP"])])
        w = {t: worth(k, t) for t in ("ABS", "DSP")}
        err = {t: w[t] / T[t]["target"] - 1 for t in f}
        print(f"  it {it}: f_ABS {f['ABS']:.5f} f_DSP {f['DSP']:.5f}  ->  ABS {w['ABS']:+.1f}"
              f" ({100 * err['ABS']:+.3f} %)  DSP {w['DSP']:+.1f} ({100 * err['DSP']:+.3f} %)")
        if max(abs(e) for e in err.values()) < 2e-4:
            break
        fn = {}
        for t in f:
            slope = (w[t] - wprev[t]) / (f[t] - fprev[t])
            fn[t] = f[t] + (T[t]["target"] - w[t]) / slope
        fprev, wprev, f = dict(f), dict(w), fn
    print(f"RESULT f_ABS {f['ABS']:.6f} f_DSP {f['DSP']:.6f} tag {tag}")
    print(f"files {p['ABS']} {p['DSP']}")


if __name__ == "__main__":
    main()
