#!/usr/bin/env python3
"""Tier B B0: export the cross sections DONJON's NCR builds, at every COMPO
grid node, to HDF5 for the Julia engine (TIER_B_WORKPLAN.md, B0).

Rather than re-implement NCR's assembly of a macrolib from the COMPO's
isotope records (residual macro, SPH, transport correction, scattering
compression, delayed-neutron spectra), DONJON's own NCR evaluates the fuel
COMPO at every grid node -- SET exactly on the stored parameter values, where
NCR's TERP factor is one calculation with weight 1 -- and the reference
mixtures exactly as the A8 decks build them (MACREF).  The Julia side then
interpolates multilinearly between nodes, which is what NCR LINEAR does; the
B0 gate checks that against NCR at off-grid states.

    tierb_export_xs.py run  [--vb] [--cb]   # write and run the DONJON deck
    tierb_export_xs.py h5   <stem> <out.h5> # parse its macrolibs into HDF5
    tierb_export_xs.py check <stem>         # 20 off-grid states for the gate

--vb stages _ACompoVB (bracket B) as the fuel COMPO, --cb the corrected CPS
COMPOs (_CCompoABScB/_CCompoDSPcB), exactly as gen_rbmk_unit4.py's U4_VOIDB
and U4_CPSB do.  The stem is content-addressed on the staged COMPOs.

Run `h5` with the OpenMC venv python (h5py).
"""
import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from compo_voidB import parse, nums  # noqa: E402

COMPO = os.path.join(ROOT, "5.1", "Dragon", "compo")
DON = os.path.join(ROOT, "5.1", "Donjon")
DATA = os.path.join(ROOT, "decks", "Donjon", "data")
STORE = os.path.join(ROOT, "tierb", "xs")


def fuel_axes(path):
    """PARKEY order and pval axes of the fuel COMPO's GLOBAL directory, read
    from the head of the file (the axes precede the 300 MB of calculations)."""
    head = open(path, "rb").read(200_000).decode("latin1")
    tmp = os.path.join(STORE, ".head")
    os.makedirs(STORE, exist_ok=True)
    cut = head.index("STATE-VECTOR")
    open(tmp, "w").write(head[:head.rindex("->", 0, cut)])
    lines, recs = parse(tmp)
    os.remove(tmp)
    keys, ax = None, {}
    for r in recs:
        if r["name"] == "PARKEY":            # 12-character fields, last line
            raw = lines[r["d1"] - 1]
            keys = [raw[i:i + 12].strip() for i in range(0, len(raw.rstrip()), 12)]
        if r["name"].startswith("pval"):
            ax[int(r["name"][4:])] = nums(lines, r)
    return keys, [ax[i + 1] for i in range(len(keys))]


def staged(vb, cb):
    fuel = "_ACompoVB" if vb else "_ACompo"
    abs_, dsp = ("_CCompoABScB", "_CCompoDSPcB") if cb else ("_CCompoABS", "_CCompoDSP")
    return {"_ACompo": fuel, "_CCompoWAT": "_CCompoWAT", "_CCompoABS": abs_,
            "_CCompoDSP": dsp, "_RCompo": "_RCompo"}


def stem_of(files):
    h = hashlib.md5()
    for k in sorted(files):
        h.update(k.encode()); h.update(open(os.path.join(COMPO, files[k]), "rb").read())
    return "tierb_xs_" + h.hexdigest()[:8]


# The reference mixtures exactly as the A8 decks build them (gen_rbmk_unit4.py
# MACREF; e.g. rbmk_unit4_a7_acc_pc99b7f3_..._cB4af83e.don:7411-7423).
MACREF = """MACR := NCR: CCpo ACpo DCpo RCpo :: EDIT 0 MACRO LINEAR NMIX 7
  COMPO CCpo 'EDICPS'
  MIX 1 FROM 5 SET 'burnup' 10900.0 SET 'DCA' 0.72 SET 'TF' 900.0 ENDMIX
  COMPO ACpo 'EDICPS'
  MIX 2 FROM 5 SET 'burnup' 10900.0 SET 'DCA' 0.72 SET 'TF' 900.0 ENDMIX
  COMPO DCpo 'EDICPS'
  MIX 3 FROM 5 SET 'burnup' 10900.0 SET 'DCA' 0.72 SET 'TF' 900.0 ENDMIX
  COMPO RCpo 'EDIREFL'
  MIX 4 FROM 5 SET 'burnup' 10900.0 SET 'DCA' 0.72 ENDMIX
  MIX 5 FROM 6 SET 'burnup' 10900.0 SET 'DCA' 0.72 ENDMIX
  MIX 6 FROM 7 SET 'burnup' 10900.0 SET 'DCA' 0.72 ENDMIX
  MIX 7 FROM 8 SET 'burnup' 10900.0 SET 'DCA' 0.72 ENDMIX
  ;
"""


def states_block(keys, states, name):
    out = [f"{name} := NCR: FCpo :: EDIT 0 MACRO LINEAR NMIX {len(states)}\n",
           "  COMPO FCpo 'EDIRBMK'\n"]
    for m, st in enumerate(states, 1):
        # one SET per line: CLE-2000 truncates input past column 120
        sets = "".join(f"    SET '{k}' {v:.8E}\n" for k, v in zip(keys, st))
        out.append(f"  MIX {m} FROM 1\n{sets}  ENDMIX\n")
    out.append("  ;\n")
    return "".join(out)


def deck(stem, keys, states, files, extra=""):
    decl = "".join(f"SEQ_ASCII   {k} :: FILE './{k}' ;\n" for k in files)
    text = f"""*  {stem}: Tier B B0 cross-section export (tools/tierb_export_xs.py).
*  NCR evaluated at {len(states)} fuel states and at the A8 reference mixtures;
*  both macrolibs written as SEQ_ASCII for the Julia engine.
LINKED_LIST FCpo CCpo ACpo DCpo RCpo MACF MACR ;
MODULE      NCR: END: ;
{decl}SEQ_ASCII   MACF_A :: FILE './macf.asc' ;
SEQ_ASCII   MACR_A :: FILE './macr.asc' ;
FCpo := _ACompo ;
CCpo := _CCompoWAT ;
ACpo := _CCompoABS ;
DCpo := _CCompoDSP ;
RCpo := _RCompo ;
{states_block(keys, states, "MACF")}{MACREF}MACF_A := MACF ;
MACR_A := MACR ;
ECHO "{stem} completed" ;
END: ;
QUIT .
"""
    name = stem + ".don"
    open(os.path.join(DATA, name), "w").write(text)
    acc = "#!/bin/sh\nsrc=\"$1\"/../Dragon/compo\n" + "".join(
        f"cp \"$src\"/{v} ./{k} || exit 1\n" for k, v in files.items())
    open(os.path.join(DATA, name + ".access"), "w").write(acc)
    out = os.path.join(STORE, stem)
    os.makedirs(out, exist_ok=True)
    open(os.path.join(DATA, name + ".save"), "w").write(
        f"#!/bin/sh\ncp ./macf.asc ./macr.asc {out}/ || exit 1\n")
    for ext in (".access", ".save"):
        os.chmod(os.path.join(DATA, name + ext), 0o755)
    for ext in ("", ".access", ".save"):
        dst = os.path.join(DON, "data", name + ext)
        if os.path.lexists(dst):
            os.remove(dst)
        os.symlink(os.path.join(DATA, name + ext), dst)
    res = os.path.join(DON, "Linux_aarch64", name + ".result")
    if os.path.exists(res):
        os.remove(res)                                   # rule 5
    subprocess.run(["./rdonjon", name], cwd=DON, capture_output=True)
    txt = open(res, "rb").read().decode("latin1")
    # the listing echoes the deck source, so match the executed ECHO (">|")
    if f">|{stem} completed" not in txt:
        sys.exit(f"{name}: did not complete; see {res}")
    return out


def grid(axes):
    import itertools
    return list(itertools.product(*axes))


def cmd_run(argv):
    files = staged("--vb" in argv, "--cb" in argv)
    stem = stem_of(files)
    keys, axes = fuel_axes(os.path.join(COMPO, files["_ACompo"]))
    states = grid(axes)
    print(stem, keys, [len(a) for a in axes], len(states), "states")
    out = deck(stem, keys, states, files)
    import json
    json.dump({"stem": stem, "files": files, "keys": keys, "axes": axes,
               "order": "itertools.product over keys, last key fastest"},
              open(os.path.join(out, "axes.json"), "w"), indent=1)
    print("wrote", out)


def macrolib(path):
    """Decode a DONJON MACROLIB SEQ_ASCII dump into numpy arrays.

    Per-mixture records come out as [mix, group]; NUSIGF/CHI and their
    delayed forms as [mix, iso, group] (NCR interpolates them per fissile
    isotope, so the fission source must be formed after interpolation);
    scattering is decompressed from SCAT00/NJJS00/IJJS00/IPOS00 into
    S[mix, g_to, g_from]: for destination group g, SCAT(IPOS + k) is the
    transfer from source group IJJS - k, k = 0 .. NJJS - 1."""
    import numpy as np
    lines, recs = parse(path)
    top = {r["name"]: r for r in recs if r["level"] == 1 and r["name"]}
    sv = nums(lines, top["STATE-VECTOR"], int)
    ng, nmix, nifi, ndel = sv[0], sv[1], sv[3], sv[6]
    groups, cur = [], None
    for r in recs:
        if r["level"] == 2 and r["elem"] is not None:
            cur = {}
            groups.append(cur)
        elif r["level"] == 3 and r["name"] and cur is not None:
            cur[r["name"]] = r
    assert len(groups) == ng, (len(groups), ng)
    def per_mix(name):
        return np.array([nums(lines, g[name]) for g in groups]).T      # [mix, g]
    out = {"ng": ng, "nmix": nmix, "nifi": nifi, "ndel": ndel}
    for name in ("NTOT0", "DIFF", "OVERV", "H-FACTOR", "NFTOT", "SIGS00", "NSPH",
                 "FLUX-INTG", "TRANC"):
        if name in groups[0]:
            out[name] = per_mix(name)
    def per_iso(name):
        # DONJON stores NUSIGF(NMIX, NIFI) in Fortran order: mixture fastest
        a = np.array([nums(lines, g[name]) for g in groups])            # [g, iso*mix]
        return a.reshape(ng, nifi, nmix).transpose(2, 1, 0)               # [mix, iso, g]
    if nifi > 0:
        out["NUSIGF"] = per_iso("NUSIGF")
        out["CHI"] = per_iso("CHI")
        out["NUSIGFd"] = np.stack([per_iso("NUSIGF%02d" % d) for d in range(1, ndel + 1)], 1)
        out["CHId"] = np.stack([per_iso("CHI%02d" % d) for d in range(1, ndel + 1)], 1)
    S = np.zeros((nmix, ng, ng))
    for g, rec in enumerate(groups):
        scat = nums(lines, rec["SCAT00"])
        nj = nums(lines, rec["NJJS00"], int)
        ij = nums(lines, rec["IJJS00"], int)
        ip = nums(lines, rec["IPOS00"], int)
        for m in range(nmix):
            for k in range(nj[m]):
                S[m, g, ij[m] - 1 - k] = scat[ip[m] - 1 + k]
    out["SCAT"] = S
    if "LAMBDA-D" in top:
        out["LAMBDA-D"] = np.array(nums(lines, top["LAMBDA-D"]))
    return out


def cmd_h5(argv):
    import json
    import h5py
    import numpy as np
    stem, dst = argv[0], argv[1]
    d = os.path.join(STORE, stem)
    meta = json.load(open(os.path.join(d, "axes.json")))
    with h5py.File(dst, "w") as h:
        h.attrs["stem"] = stem
        h.attrs["generator"] = "tools/tierb_export_xs.py"
        for k, v in meta["files"].items():
            h.attrs["md5 " + k] = hashlib.md5(open(os.path.join(COMPO, v), "rb").read()).hexdigest()
            h.attrs["file " + k] = v
        for grp, fn in (("fuel", "macf.asc"), ("ref", "macr.asc")):
            m = macrolib(os.path.join(d, fn))
            g = h.create_group(grp)
            for k, v in m.items():
                if isinstance(v, np.ndarray):
                    g.create_dataset(k, data=v)
                else:
                    g.attrs[k] = v
        f = h["fuel"]
        f.attrs["keys"] = meta["keys"]
        f.attrs["order"] = meta["order"]
        for k, ax in zip(meta["keys"], meta["axes"]):
            f.create_dataset("axis_" + k, data=np.array(ax))
        h["ref"].attrs["mixtures"] = ("1 CPS water, 2 CPS absorber, 3 CPS displacer, "
                                      "4-7 reflector mixtures 5-8 of _RCompo; "
                                      "burnup 10900, DCA 0.72, TF 900 (A8 MACREF)")
    print("wrote", dst)


def cmd_check(argv):
    """B0 gate reference: NCR at 20 seeded random off-grid states (within the
    axes, TG on 750 as the A8 decks pin it, plus 6 states free in TG)."""
    import json
    import random
    stem = argv[0]
    meta = json.load(open(os.path.join(STORE, stem, "axes.json")))
    rnd = random.Random(20261016)
    states = []
    for i in range(26):
        st = []
        for k, ax in zip(meta["keys"], meta["axes"]):
            if k == "TG" and i < 20:
                st.append(750.0)
            else:
                st.append(rnd.uniform(ax[0], ax[-1]))
        states.append(tuple(st))
    cstem = stem + "_chk"
    deck(cstem, meta["keys"], states, meta["files"])
    json.dump({"keys": meta["keys"], "states": states},
              open(os.path.join(STORE, cstem, "states.json"), "w"), indent=1)
    print("wrote", os.path.join(STORE, cstem))


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("run", "h5", "check"):
        sys.exit(__doc__)
    {"run": cmd_run, "h5": cmd_h5, "check": cmd_check}[sys.argv[1]](sys.argv[2:])
