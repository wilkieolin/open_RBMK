#!/usr/bin/env python3
"""Tier B B2 reference: a generated A8 kinetic deck re-run with TRIVAT MCFD 1
(the scheme RBMKCore.Diffusion implements; B1 showed FD and DUAL 1 1 differ
by ~420 pcm at 25 cm) and with the t = 0 objects dumped right before INIKIN:

  FMAP  -- the fuel map after the steady THM loop: T-FUEL, D-COOL, ... per
           bundle, the state the frozen-TH transient starts from;
  MACRD -- the t = 0 per-region macrolib (for a cross-section spot check).

    tierb_kinref.py <stem>          # an existing generated kinetic deck
    tierb_kinref.py <stem> --dual   # keep DUAL 1 1: only add the dumps
    tierb_kinref.py <stem> --dual --t0only   # stop at INIKIN: the t = 0 dumps only
    tierb_kinref.py <stem> --dual --epsout 1e-7 --nsteps 100   # KINSOL tolerance study

Writes <stem>_tbm.don (MCFD 1) or <stem>_tbd.don (DUAL 1 1); results in
tierb/xs/<stem>_tb{m,d}/.  The A8STEP trace is read from the listing.
"""
import hashlib
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DON = os.path.join(ROOT, "5.1", "Donjon")
DATA = os.path.join(ROOT, "decks", "Donjon", "data")
STORE = os.path.join(ROOT, "tierb", "xs")


def main(stem, run=True, dual=False, t0only=False, epsout=None, nsteps=None):
    text = open(os.path.join(DATA, stem + ".don")).read()
    md5 = hashlib.md5(text.encode()).hexdigest()
    tb = stem + ("_tbd" if dual else "_tbm") + ("0" if t0only else "")
    if epsout is not None:
        tb += "e" + f"{epsout:.0e}".replace("-", "m").replace("+", "")
    if nsteps is not None:
        tb += f"n{nsteps}"
    n = text.count("DUAL 1 1")
    assert n >= 1, "no DUAL 1 1 to replace"
    if not dual:
        text = text.replace("DUAL 1 1", "MCFD 1")
    anchor = "SEQ_ASCII   _RCompo    :: FILE './_RCompo' ;\n"
    assert anchor in text
    text = text.replace(anchor, anchor +
                        "SEQ_ASCII   FMAP0_A :: FILE './fmap0.asc' ;\n"
                        "SEQ_ASCII   MACRD0_A :: FILE './macrd0.asc' ;\n", 1)
    k = text.index("KINET := INIKIN:")
    dumps = "FMAP0_A := FMAP ;\nMACRD0_A := MACRD ;\n"
    if t0only:
        text = text[:k] + dumps + f'ECHO "{stem} completed" ;\nEND: ;\nQUIT .\n'
    else:
        text = text[:k] + dumps + text[k:]
    if epsout is not None:
        # KINSOL's flux convergence per step (KINRD2: EPSOUT default 1e-4)
        k = "SCHEME FLUX THETA 0.8 PREC THETA 0.8 ;"
        assert text.count(k) == 1
        text = text.replace(k, f"SCHEME FLUX THETA 0.8 PREC THETA 0.8 EXTE 2000 {epsout:.1E} ;")
    if nsteps is not None:
        assert text.count("UNTIL istep 700 >= ;") == 1
        text = text.replace("UNTIL istep 700 >= ;", f"UNTIL istep {nsteps} >= ;")
    text = text.replace(f'"{stem} completed"', f'"{tb} completed"')
    out = os.path.join(STORE, tb)
    os.makedirs(out, exist_ok=True)
    open(os.path.join(DATA, tb + ".don"), "w").write(text)
    open(os.path.join(DATA, tb + ".don.access"), "w").write(
        open(os.path.join(DATA, stem + ".don.access")).read())
    open(os.path.join(DATA, tb + ".don.save"), "w").write(
        f"#!/bin/sh\ncp ./fmap0.asc ./macrd0.asc {out}/ || exit 1\n")
    for ext in (".access", ".save"):
        os.chmod(os.path.join(DATA, tb + ".don" + ext), 0o755)
    for ext in ("", ".access", ".save"):
        dst = os.path.join(DON, "data", tb + ".don" + ext)
        if os.path.lexists(dst):
            os.remove(dst)
        os.symlink(os.path.join(DATA, tb + ".don" + ext), dst)
    open(os.path.join(out, "deck.md5"), "w").write(f"{md5}  {stem}.don ({n} DUAL 1 1{'' if dual else ' -> MCFD 1'})\n")
    if not run:
        print("wrote", tb)
        return
    res = os.path.join(DON, "Linux_aarch64", tb + ".don.result")
    if os.path.exists(res):
        os.remove(res)                                   # rule 5
    subprocess.run(["./rdonjon", tb + ".don"], cwd=DON, capture_output=True)
    txt = open(res, "rb").read().decode("latin1")
    ok = f">|{tb} completed" in txt
    steps = re.findall(r">\|A8STEP\s+\d+\s+T\s+(\S+)\s+POWER\s+(\S+)\s+P/P0\s+(\S+)", txt)
    with open(os.path.join(out, "trace.txt"), "w") as f:
        f.write(f"# t_s power_MW P/P0 (DONJON, {'DUAL 1 1' if dual else 'MCFD 1'})\n")
        for t, p, r in steps:
            f.write(f"{t} {p} {r}\n")
    print(tb, "completed" if ok else "DID NOT COMPLETE", len(steps), "steps ->", out)


if __name__ == "__main__":
    a = sys.argv
    opt = lambda k, f: f(a[a.index(k) + 1]) if k in a else None
    main(a[1], run="--norun" not in a, dual="--dual" in a, t0only="--t0only" in a,
         epsout=opt("--epsout", float), nsteps=opt("--nsteps", int))
