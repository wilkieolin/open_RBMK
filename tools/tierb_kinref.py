#!/usr/bin/env python3
"""Tier B B2 reference: a generated A8 kinetic deck re-run with TRIVAT MCFD 1
(the scheme RBMKCore.Diffusion implements; B1 showed FD and DUAL 1 1 differ
by ~420 pcm at 25 cm) and with the t = 0 objects dumped right before INIKIN:

  FMAP  -- the fuel map after the steady THM loop: T-FUEL, D-COOL, ... per
           bundle, the state the frozen-TH transient starts from;
  MACRD -- the t = 0 per-region macrolib (for a cross-section spot check).

    tierb_kinref.py <stem>        # an existing generated kinetic deck

Writes <stem>_tbm.don (MCFD 1); results in tierb/xs/<stem>_tbm/.  The
A8STEP trace is read from the listing.
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


def main(stem, run=True):
    text = open(os.path.join(DATA, stem + ".don")).read()
    md5 = hashlib.md5(text.encode()).hexdigest()
    tb = stem + "_tbm"
    n = text.count("DUAL 1 1")
    assert n >= 1, "no DUAL 1 1 to replace"
    text = text.replace("DUAL 1 1", "MCFD 1")
    anchor = "SEQ_ASCII   _RCompo    :: FILE './_RCompo' ;\n"
    assert anchor in text
    text = text.replace(anchor, anchor +
                        "SEQ_ASCII   FMAP0_A :: FILE './fmap0.asc' ;\n"
                        "SEQ_ASCII   MACRD0_A :: FILE './macrd0.asc' ;\n", 1)
    k = text.index("KINET := INIKIN:")
    text = text[:k] + "FMAP0_A := FMAP ;\nMACRD0_A := MACRD ;\n" + text[k:]
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
    open(os.path.join(out, "deck.md5"), "w").write(f"{md5}  {stem}.don ({n} DUAL 1 1 -> MCFD 1)\n")
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
        f.write("# t_s power_MW P/P0 (DONJON, MCFD 1)\n")
        for t, p, r in steps:
            f.write(f"{t} {p} {r}\n")
    print(tb, "completed" if ok else "DID NOT COMPLETE", len(steps), "steps ->", out)


if __name__ == "__main__":
    main(sys.argv[1], run="--norun" not in sys.argv)
