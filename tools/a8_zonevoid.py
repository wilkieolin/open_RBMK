#!/usr/bin/env python3
"""Axially-resolved void worth of the converged A7 state.

PROGRESS (32): at 1 C subcooling the lower half of the core boils during the
AZ-5 transient and power still falls, so the question is what steam is worth
WHERE it forms.  This measures it statically, zone by zone:

  pass 1  the generator's static A7 deck, plus an export of the converged fuel
          map (FMAPX := FMAP) to a SEQ_ASCII file;
  edit    copies of that map with the coolant density (fuel-map PARAM
          'D-COOL', NCH x NB, bottom bundle first) lowered by DRHO in one
          axial zone of ZW bundles, and one with it lowered everywhere;
  pass 2  the same static deck, converged again, then for each map: replace
          FMAP, one NCR:/MACINI:/NEWMAC:/TRIVAA:/FLUD: pass, keff.  Map 0 is
          the unedited export, so its keff must reproduce UNIT4 FINAL keff:
          that is the round-trip check on export/import.

Nothing is fitted.  Temperatures, burnup, xenon and rods are those of the
converged state; only the coolant density moves.

  usage: tools/a8_zonevoid.py <static deck stem> [DRHO] [ZW]
         (deck generated beforehand by gen_rbmk_unit4.py; DRHO in g/cm3,
          default 0.1; ZW bundles per zone, default 4)
"""
import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "decks", "Donjon", "data")
RUN = os.path.join(ROOT, "5.1", "Donjon")
OUT = os.path.join(RUN, "Linux_aarch64")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compo_voidB import parse, nums, fmt_reals  # noqa: E402


def link(name):
    for ext in ("", ".access", ".save"):
        src = os.path.join(DATA, name + ext)
        dst = os.path.join(RUN, "data", name + ext)
        if os.path.exists(src) and not os.path.lexists(dst):
            os.symlink(src, dst)


def run(name):
    res = os.path.join(OUT, name + ".result")
    if os.path.exists(res):
        os.remove(res)
    link(name)
    subprocess.run(["./rdonjon", name], cwd=RUN, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
    txt = open(res, "rb").read().decode("latin1")
    if not re.search(r">\|" + re.escape(name[:-4]) + r" completed", txt):
        sys.exit(f"{name}: did not complete; see {res}")
    return txt


def write(name, text, access_src, extra_copy=(), save=None):
    with open(os.path.join(DATA, name), "w") as f:
        f.write(text)
    acc = open(os.path.join(DATA, access_src + ".don.access")).read()
    for p in extra_copy:
        acc += f"cp {p} || exit 1\n"
    with open(os.path.join(DATA, name + ".access"), "w") as f:
        f.write(acc)
    os.chmod(os.path.join(DATA, name + ".access"), 0o755)
    if save:
        with open(os.path.join(DATA, name + ".save"), "w") as f:
            f.write("#!/bin/sh\n" + save)
        os.chmod(os.path.join(DATA, name + ".save"), 0o755)


def main():
    stem = sys.argv[1].removesuffix(".don")
    drho = float(sys.argv[2]) if len(sys.argv) > 2 else 0.1
    zw = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    base = open(os.path.join(DATA, stem + ".don")).read()
    anchor = 'ECHO "UNIT4 FINAL keff" keff ;\n'
    assert base.count(anchor) == 1, "not a static A7 deck"
    assert "KINSOL:" not in base, "use the static deck (no U4_KIN)"
    head, _ = base.split(anchor)
    decl = "SEQ_ASCII   _RCompo    :: FILE './_RCompo' ;\n"
    assert head.count(decl) == 1
    tail = (f'ECHO "{stem}_X completed" ;\nEND: ;\nQUIT .\n')

    # pass 1: export the converged map
    store = os.path.join(OUT, stem + "_fx.fmap")
    n1 = stem + "_fx.don"
    # pass 1 keeps the whole static deck (its converged power edits too), adds
    # the export, and prints POWER-BUND so the t = 0 axial shape of this state
    # can be read back with tools/a8_axial.py.
    pchan = "UTL: POWER :: IMPR POWER-CHAN * ;"
    assert base.count(pchan) == 1 and base.count(f"{stem} completed") == 1
    d1 = (base.replace(decl, decl + "SEQ_ASCII   FMAPX :: FILE './fmapx' ;\n")
          .replace(anchor, anchor + "FMAPX := FMAP ;\n")
          .replace(pchan, pchan + "\nUTL: POWER :: IMPR POWER-BUND * ;")
          .replace(f"{stem} completed", f"{stem}_fx completed"))
    r1 = os.path.join(OUT, n1 + ".result")
    old = os.path.join(DATA, n1)
    if (os.path.exists(r1) and os.path.exists(store) and os.path.exists(old)
            and open(old).read() == d1
            and os.path.getmtime(r1) > os.path.getmtime(old)):
        t1 = open(r1, "rb").read().decode("latin1")   # pass 1 already done
    else:
        write(n1, d1, stem, save=f"cp ./fmapx {store}\n")
        t1 = run(n1)
    k1 = float(re.search(r">\|UNIT4 FINAL keff\s+(\S+)", t1).group(1))
    from a8_axial import shape
    sh, _ = shape(os.path.join(OUT, n1 + ".result"))

    # edit
    lines, recs = parse(store)
    pn = [r for r in recs if r["name"] == "P-NAME"]
    idx = None
    for r in pn:
        tag = " ".join(lines[r["d0"]:r["d1"]])
        if "D-COOL" in tag:
            idx = recs.index(r)
    assert idx is not None, "no D-COOL parameter in the exported map"
    # P-VALUE is the sibling record of P-NAME in the same parameter directory
    lev = recs[idx]["level"]
    j = idx + 1
    while recs[j]["name"] != "P-VALUE" or recs[j]["level"] != lev:
        assert recs[j]["level"] >= lev
        j += 1
    rv = recs[j]
    rho = nums(lines, rv)
    nch = 1661
    assert len(rho) % nch == 0, len(rho)
    nb = len(rho) // nch
    zones = [(z, min(z + zw, nb)) for z in range(0, nb, zw)]
    edits = [("base", None)] + [(f"z{a+1}-{b}", (a, b)) for a, b in zones] \
        + [("all", (0, nb))]
    files = []
    tag = hashlib.md5(f"{drho} {zw}".encode()).hexdigest()[:6]
    for lab, zr in edits:
        new = list(rho)
        if zr:
            for k in range(zr[0], zr[1]):
                for c in range(nch):
                    new[k * nch + c] -= drho
        out = lines[:rv["d0"]] + fmt_reals(new) + lines[rv["d1"]:]
        p = os.path.join(OUT, f"{stem}_zv{tag}_{lab}.fmap")
        with open(p, "wb") as f:
            f.write("\n".join(out).encode("latin1"))
        files.append((lab, p))

    # pass 2: converge again, then one pass per map
    n2 = f"{stem}_zv{tag}.don"
    decls = "".join(f"SEQ_ASCII   FZ{i} :: FILE './fz{i}' ;\n"
                    for i in range(len(files)))
    single = base.split("*--- ONE FINAL SOLVE")[1].split(anchor)[0]
    single = single[single.index("MACFUEL := NCR:"):]
    body = ""
    for i, (lab, _) in enumerate(files):
        body += ("MACFUEL MACRO MACRD SYSTEM FLUX := DELETE:\n"
                 "  MACFUEL MACRO MACRD SYSTEM FLUX ;\n"
                 "FMAP := DELETE: FMAP ;\n"
                 f"FMAP := FZ{i} ;\n" + single +
                 f'ECHO "ZONEVOID {lab}" keff ;\n')
    d2 = (head.replace(decl, decl + decls) + anchor + body
          + tail.replace("_X", f"_zv{tag}"))
    write(n2, d2, stem,
          extra_copy=[f"{p} ./fz{i}" for i, (_, p) in enumerate(files)])
    t2 = run(n2)
    ks = dict(re.findall(r">\|ZONEVOID (\S+)\s+(\S+)", t2))
    k0 = float(ks["base"])
    print(f"# {stem}  drho {drho} g/cm3  zones of {zw} bundles (bottom = z1)")
    print(f"# pass-1 FINAL keff {k1:.6f}; re-imported base {k0:.6f} "
          f"(diff {1e5*(k0-k1):+.2f} pcm)")
    print("# t = 0 axial shape, bottom bundle first: "
          + " ".join(f"{v:.3f}" for v in sh))
    tot = 0.0
    for lab, _ in files[1:]:
        k = float(ks[lab])
        rho_pcm = 1e5 * (1 / k0 - 1 / k)
        if lab != "all":
            tot += rho_pcm
        print(f"{lab:8s} keff {k:.6f}  dRho {rho_pcm:+9.1f} pcm")
    print(f"sum of zones {tot:+9.1f} pcm")


if __name__ == "__main__":
    main()
