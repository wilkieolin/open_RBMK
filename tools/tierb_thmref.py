#!/usr/bin/env python3
"""Tier B B3 reference: DONJON THM: itself on a known power, for the
line-by-line Julia port (RBMKCore.Channel).

From a generated A8 kinetic deck (run with TRIVAT MCFD 1 for speed: the
power SHAPE is only an input here), keep everything up to the converged
steady state and its final FLPOW, then replace the transient with

  1. a FRESH steady THM: on that final BUND-PW, RELAX 1.0 (the deck's own
     loop relaxes 0.5 between passes, so its FMAP lags its last power);
  2. 35 transient THM: steps of 0.01 s with the power SHAPE frozen and the
     total doubled every 5 steps (200 MW x 2^(i/5), x128 at 0.35 s), with
     the A8 transient keywords (CONV 100 100 60 0.05 1.0E-3 CYCLE-OK 0.1
     FLOW-RELAX 0.25).

Dumps (LCM ASCII) in tierb/xs/<stem>_tbt/:
  fmaps.asc   FMAP after the deck's own steady loop (BUND-PW, BURN-INST)
  fmapt00.asc FMAP after the fresh steady THM: (T-FUEL, D-COOL)
  ther0.asc   that THM: object (per-channel steady records)
  fmaptNN.asc FMAP after transient step NN = 05, 10, ..., 35 (BUND-PW of NN)

    tierb_thmref.py <stem>
"""
import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DON = os.path.join(ROOT, "5.1", "Donjon")
DATA = os.path.join(ROOT, "decks", "Donjon", "data")
STORE = os.path.join(ROOT, "tierb", "xs")
CHECK = [5, 10, 15, 20, 25, 30, 35]


def main(stem, run=True):
    text = open(os.path.join(DATA, stem + ".don")).read()
    md5 = hashlib.md5(text.encode()).hexdigest()
    tb = stem + "_tbt"
    text = text.replace("DUAL 1 1", "MCFD 1")
    # the deck's first (steady) THM: call, keywords verbatim
    a = text.index("  THER FMAP := THM: FMAP ::\n")
    b = text.index("\n    ;\n", a)
    steady = text[a:b + len("\n    ;\n")]
    assert "RELAX 0.5" in steady and "SPEED CHAN" in steady
    steady = (steady.replace("THER FMAP := THM: FMAP ::", "THER2 FMAP := THM: FMAP ::")
                    .replace("RELAX 0.5", "RELAX 1.0").replace("EDIT 1", "EDIT 0"))
    cut = text.index("KINET := INIKIN:")
    head = text[:cut]
    decl = ("SEQ_ASCII   FMAPS_A :: FILE './fmaps.asc' ;\n"
            "SEQ_ASCII   FMAPT00_A :: FILE './fmapt00.asc' ;\n"
            "SEQ_ASCII   THER0_A :: FILE './ther0.asc' ;\n"
            + "".join(f"SEQ_ASCII   FMAPT{n:02d}_A :: FILE './fmapt{n:02d}.asc' ;\n" for n in CHECK)
            + "LINKED_LIST THER2 ;\n")
    anchor = "SEQ_ASCII   _RCompo    :: FILE './_RCompo' ;\n"
    assert anchor in head
    head = head.replace(anchor, anchor + decl, 1)
    body = ["FMAPS_A := FMAP ;", steady.rstrip("\n"), "FMAPT00_A := FMAP ;", "THER0_A := THER2 ;",
            "REAL pp t0 := 200.0 0.0 ;", "INTEGER istep := 0 ;", "REPEAT",
            "  EVALUATE istep := istep 1 + ;",
            "  EVALUATE pp := pp 1.148698355 * ;",
            "  POWER := DELETE: POWER ;",
            "  POWER FMAP := FLPOW: FMAP FLUX TRACK MATEX :: EDIT 0 PTOT <<pp>> ;",
            "  THER2 FMAP := THM: THER2 FMAP :: EDIT 0 TIME <<t0>> 0.01 HISTORY 2",
            "    CONV 100 100 60 0.05 1.0E-3 CYCLE-OK 0.1 FLOW-RELAX 0.25 ;",
            "  EVALUATE t0 := t0 0.01 + ;",
            '  ECHO "THMREF STEP" istep "T" t0 "PTOT" pp ;']
    for n in CHECK:
        body.append(f"  IF istep {n} = THEN\n    FMAPT{n:02d}_A := FMAP ;\n  ENDIF ;")
    body += ["UNTIL istep 35 = ;", f'ECHO "{tb} completed" ;', "END: ;", "QUIT ."]
    text = head + "\n".join(body) + "\n"
    out = os.path.join(STORE, tb)
    os.makedirs(out, exist_ok=True)
    open(os.path.join(DATA, tb + ".don"), "w").write(text)
    open(os.path.join(DATA, tb + ".don.access"), "w").write(
        open(os.path.join(DATA, stem + ".don.access")).read())
    files = " ".join(["./fmaps.asc", "./fmapt00.asc", "./ther0.asc"] + [f"./fmapt{n:02d}.asc" for n in CHECK])
    open(os.path.join(DATA, tb + ".don.save"), "w").write(f"#!/bin/sh\ncp {files} {out}/ || exit 1\n")
    for ext in (".access", ".save"):
        os.chmod(os.path.join(DATA, tb + ".don" + ext), 0o755)
    for ext in ("", ".access", ".save"):
        dst = os.path.join(DON, "data", tb + ".don" + ext)
        if os.path.lexists(dst):
            os.remove(dst)
        os.symlink(os.path.join(DATA, tb + ".don" + ext), dst)
    open(os.path.join(out, "deck.md5"), "w").write(f"{md5}  {stem}.don (DUAL 1 1 -> MCFD 1; THM: test tail)\n")
    if not run:
        print("wrote", tb)
        return
    res = os.path.join(DON, "Linux_aarch64", tb + ".don.result")
    if os.path.exists(res):
        os.remove(res)
    subprocess.run(["./rdonjon", tb + ".don"], cwd=DON, capture_output=True)
    txt = open(res, "rb").read().decode("latin1")
    ok = f">|{tb} completed" in txt
    print(tb, "completed" if ok else "DID NOT COMPLETE", "->", out)


if __name__ == "__main__":
    main(sys.argv[1], run="--norun" not in sys.argv)
