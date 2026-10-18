#!/usr/bin/env python3
"""Tier B B1 reference: re-run a generated Unit 4 deck with the objects the
Julia engine needs dumped as SEQ_ASCII, so the engine can be checked in two
independent halves (TIER_B_WORKPLAN.md, B1):

  * solver gate -- MACRD (the final per-region macrolib, after NCR, MACINI
    and NEWMAC's rod devices) and MATEX (the element -> region INDEX and the
    mesh): Julia's diffusion solver run on exactly DONJON's cross sections;
  * input gate  -- the same MACRD against the per-element cross sections
    Julia builds itself from the deck (mixture map, fuel map, XS tables,
    rod devices).

    tierb_export_core.py <stem>      # stem of an existing generated deck

The copy is <stem>_tb.don, identical to the deck except for the SEQ_ASCII
declarations and dumps inserted after the flux solve; its results land in
tierb/xs/<stem>/ with the deck's md5.
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


def main(stem):
    src = os.path.join(DATA, stem + ".don")
    text = open(src).read()
    md5 = hashlib.md5(text.encode()).hexdigest()
    tb = stem + "_tb"
    decl = ("SEQ_ASCII   MATEX_A :: FILE './matex.asc' ;\n"
            "SEQ_ASCII   MACRD_A :: FILE './macrd.asc' ;\n"
            "SEQ_ASCII   POWER_A :: FILE './power.asc' ;\n"
            "SEQ_ASCII   FMAP_A  :: FILE './fmap.asc' ;\n")
    anchor = "SEQ_ASCII   _RCompo    :: FILE './_RCompo' ;\n"
    assert anchor in text, "no _RCompo declaration to anchor on"
    text = text.replace(anchor, anchor + decl, 1)
    # dump after the power edit, which is the last use of these objects
    m = re.search(r"^UTL: POWER :: IMPR POWER-CHAN \* ;\n", text, re.M)
    assert m, "no POWER-CHAN edit to anchor on"
    dump = ("MATEX_A := MATEX ;\nMACRD_A := MACRD ;\nPOWER_A := POWER ;\n"
            "FMAP_A := FMAP ;\n")
    text = text[:m.end()] + dump + text[m.end():]
    text = text.replace(f'ECHO "{stem} completed" ;', f'ECHO "{tb} completed" ;')
    out = os.path.join(STORE, stem)
    os.makedirs(out, exist_ok=True)
    open(os.path.join(DATA, tb + ".don"), "w").write(text)
    acc = open(os.path.join(DATA, stem + ".don.access")).read()
    open(os.path.join(DATA, tb + ".don.access"), "w").write(acc)
    open(os.path.join(DATA, tb + ".don.save"), "w").write(
        "#!/bin/sh\ncp ./matex.asc ./macrd.asc ./power.asc ./fmap.asc "
        f"{out}/ || exit 1\n")
    for ext in (".access", ".save"):
        os.chmod(os.path.join(DATA, tb + ".don" + ext), 0o755)
    for ext in ("", ".access", ".save"):
        dst = os.path.join(DON, "data", tb + ".don" + ext)
        if os.path.lexists(dst):
            os.remove(dst)
        os.symlink(os.path.join(DATA, tb + ".don" + ext), dst)
    res = os.path.join(DON, "Linux_aarch64", tb + ".don.result")
    if os.path.exists(res):
        os.remove(res)                                   # rule 5
    subprocess.run(["./rdonjon", tb + ".don"], cwd=DON, capture_output=True)
    txt = open(res, "rb").read().decode("latin1")
    if f">|{tb} completed" not in txt:
        sys.exit(f"{tb}: did not complete; see {res}")
    k = re.findall(r">\|UNIT4 KEFF\s+(\S+)", txt)
    open(os.path.join(out, "deck.md5"), "w").write(f"{md5}  {stem}.don\n")
    open(os.path.join(out, "keff.txt"), "w").write((k[-1] if k else "nan") + "\n")
    print(tb, "keff", k[-1] if k else None, "->", out)


if __name__ == "__main__":
    main(sys.argv[1])
