"""Generate the DRAGON method-study decks (PROGRESS.md, "Method gap").

Every deck runs the FRESH cell at dca 0.72 / 0.35 / 0.02 (TF 900 K, TG 750 K,
coolant 573 K, bound hydrogen) and prints

    METHTAB <variant-id> <dca> <k-inf>

Each variant changes exactly one thing relative to 'ctrl', which is
rbmk_h2otest.x2m's bound-hydrogen branch and must reproduce it bit for bit.
The decks are generated rather than hand-copied so that the shared text
cannot drift between them (standing rule 6).

    python gen_meth.py        # writes ../Dragon/data/rbmk_meth_*.x2m + .access links
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "Dragon", "data")

SS_TRK = "TISO 8 15.0"
FL_TRK = "TISO 15 30.0"
GEO = "GEOSS GEOFL := RbmkGeo ;"

# id: (number, hypothesis, description, lib, geo call, SS tracking, flux tracking)
VARIANTS = {
    "ctrl":  (0, "--", "production settings (= rbmk_h2otest bound H)",
              "RbmkLib", GEO, SS_TRK, FL_TRK),
    "fine1": (1, "H3", "RbmkGeoFine k=1 -- must equal ctrl",
              "RbmkLib", "GEOSS GEOFL := RbmkGeoFine :: 1 ;", SS_TRK, FL_TRK),
    "fine2": (2, "H3", "flat-flux regions split 2x, tracking densified to match",
              "RbmkLib", "GEOSS GEOFL := RbmkGeoFine :: 2 ;", SS_TRK, "TISO 20 60.0"),
    "fine4": (3, "H3", "flat-flux regions split 4x, tracking densified to match",
              "RbmkLib", "GEOSS GEOFL := RbmkGeoFine :: 4 ;", SS_TRK, "TISO 30 120.0"),
    "trk2":  (4, "H4", "flux tracking 30 angles / 60 per cm",
              "RbmkLib", GEO, SS_TRK, "TISO 30 60.0"),
    "trk4":  (5, "H4", "flux tracking 60 angles / 120 per cm",
              "RbmkLib", GEO, SS_TRK, "TISO 60 120.0"),
    "tspc":  (6, "H2", "specular (mirror) boundary on the flux solution",
              "RbmkLib", GEO, SS_TRK, "TSPC 20 30.0"),
    "zrfine4": (8, "H7+H3", "Zr self-shielded AND flat-flux regions split 4x",
              "RbmkLibZ", "GEOSS GEOFL := RbmkGeoFine :: 4 ;", SS_TRK, "TISO 30 120.0"),
    "sstrk": (9, "H6'", "self-shielding tracking 20 angles / 40 per cm (flux unchanged)",
              "RbmkLib", GEO, "TISO 20 40.0", FL_TRK),
    "shem281": (10, "H9", "SHEM-281 library (fine groups through U-238 resonances)",
              "RbmkLib", GEO, SS_TRK, FL_TRK),
    "shem295": (11, "H9", "SHEM-295 library, subgroup iteration cap raised to 300",
              "RbmkLib", GEO, SS_TRK, FL_TRK),
    "shem361": (14, "H9", "SHEM-361 library, subgroup iteration cap raised to 300",
              "RbmkLib", GEO, SS_TRK, FL_TRK),
    "zr361": (15, "H7+H9", "Zr self-shielded on SHEM-361",
              "RbmkLibZ", GEO, SS_TRK, FL_TRK),
    "best361": (16, "H7+H9+H3", "Zr self-shielded, SHEM-361, flat-flux regions split 4x",
              "RbmkLibZ", "GEOSS GEOFL := RbmkGeoFine :: 4 ;", SS_TRK, "TISO 30 120.0"),
    "zrshem": (12, "H7+H9", "Zr self-shielded on SHEM-281",
              "RbmkLibZ", GEO, SS_TRK, FL_TRK),
    "allfix": (13, "H7+H9+H3", "Zr self-shielded, SHEM-281, flat-flux regions split 4x",
              "RbmkLibZ", "GEOSS GEOFL := RbmkGeoFine :: 4 ;", SS_TRK, "TISO 30 120.0"),
    "zrss":  (7, "H7", "Zr self-shielded (RbmkLibZ; Nb93 has no subgroup data)",
              "RbmkLibZ", GEO, SS_TRK, FL_TRK),
    # H5: method of characteristics on zr361.  moc1 keeps the CP physics
    # (isotropic + transport correction) and must reproduce zr361; moc2 / moc3
    # carry P1 / P2 scattering explicitly with the transport correction off.
    "moc1": (17, "H5", "MOC flux, isotropic + transport correction (zr361 physics)",
              "RbmkLibZ", GEO, SS_TRK, FL_TRK),
    "moc2": (18, "H5", "MOC flux, P1 scattering, no transport correction",
              "RbmkLibZN2", GEO, SS_TRK, FL_TRK),
    "moc3": (19, "H5", "MOC flux, P2 scattering, no transport correction",
              "RbmkLibZN3", GEO, SS_TRK, FL_TRK),
    # METHOD_CONVERGENCE_PLAN phase A, each against zr361 (or best361 for A4).
    "rim361": (20, "H6", "pellet in 4 equal-volume rings, each its own self-shielding set",
              "RbmkLibRim", "GEOSS GEOFL := RbmkGeoRim ;", SS_TRK, FL_TRK),
    "rim361t2": (25, "H6", "rim361, self-shielding tracking 20 angles / 60 per cm",
              "RbmkLibRim", "GEOSS GEOFL := RbmkGeoRim ;", "TISO 20 60.0", FL_TRK),
    "rim361t4": (26, "H6", "rim361, self-shielding tracking 30 angles / 120 per cm",
              "RbmkLibRim", "GEOSS GEOFL := RbmkGeoRim ;", "TISO 30 120.0", FL_TRK),
    # H10 / B1: zr361 with the fuel replaced by OpenMC's depleted isotopics
    # (RbmkLibOMC<bu>.c2m, written by openmc/isotopics_to_dragon.py).  Compare
    # with buzr361's VOIDTAB rows at the same burnup and with OpenMC's branches.
    "omc10": (27, "H10", "zr361 with OpenMC's fuel isotopics at 10 MWd/kg",
              "RbmkLibOMC10", GEO, SS_TRK, FL_TRK),
    "omc15": (28, "H10", "zr361 with OpenMC's fuel isotopics at 15 MWd/kg",
              "RbmkLibOMC15", GEO, SS_TRK, FL_TRK),
    "rim361s": (29, "H6", "rim361 geometry, all rings of a rod in one self-shielding set",
              "RbmkLibRimS", "GEOSS GEOFL := RbmkGeoRim ;", SS_TRK, FL_TRK),
    "bestmoc": (30, "H5+H3+H7+H9", "best361 with MOC P1 flux (no transport correction)",
              "RbmkLibZN2", "GEOSS GEOFL := RbmkGeoFine :: 4 ;", SS_TRK, "TISO 30 120.0"),
    "zr370": (21, "H9", "SHEM-370 library (group convergence, 361 -> 370)",
              "RbmkLibZ", GEO, SS_TRK, FL_TRK),
    "best361k8": (22, "H3", "best361 with flat-flux regions split 8x",
              "RbmkLibZ", "GEOSS GEOFL := RbmkGeoFine :: 8 ;", SS_TRK, "TISO 40 240.0"),
    "zr361nonb": (23, "A6a", "zr361 with Nb-93 removed (bounds leaving it unshielded)",
              "RbmkLibZnoNb", GEO, SS_TRK, FL_TRK),
    "tgrid": (24, "H11", "zr361 at library-grid temperatures, fuel 900 / graphite 800 / coolant 600 K",
              "RbmkLibZ", GEO, SS_TRK, FL_TRK),
}
# Temperature overrides (fuel, graphite, coolant) in K; default 900 / 750 / 573.
TEMPS = {"tgrid": (900.0, 800.0, 600.0)}

# MOC order per variant (absent = collision probabilities).  Options follow
# upstream RegtestCNG_mccg.x2m; the same string is in openmc/srp94_common.py.
MOC = {"moc1": 1, "moc2": 2, "moc3": 3, "bestmoc": 2}
MOC_OPTS = "EDIT 0 LCMD 3 MAXI 1 EPSI 1E-5 HDD 0. MCU 400000 KRYL 0 SCR 0 AAC 100 TMT"

# Library procedures for the anisotropic MOC variants: RbmkLibZ with the
# transport correction off and the Legendre order raised.  Derived by
# substitution, so they cannot drift from RbmkLibZ (standing rule 6).
PROC = os.path.join(DATA, "rbmk_proc")
_libz = open(os.path.join(PROC, "RbmkLibZ.c2m")).read()
for name, anis in (("RbmkLibZN2", 2), ("RbmkLibZN3", 3)):
    assert _libz.count("  CTRA APOL\n  ANIS 2\n") == 1
    body = _libz.replace("  CTRA APOL\n  ANIS 2\n", f"  CTRA NONE\n  ANIS {anis}\n")
    open(os.path.join(PROC, f"{name}.c2m"), "w").write(
        f"*----\n*  GENERATED by decks/scripts/gen_meth.py from RbmkLibZ.c2m with\n"
        f"*  CTRA APOL / ANIS 2 -> CTRA NONE / ANIS {anis}.  For the H5 MOC variants\n"
        f"*  only: collision-probability decks must keep the transport correction.\n*----\n"
        + body)

# H6: the pellet in 4 equal-volume rings, each its own mixture and self-shielding
# set, so U-238's radial self-shielding profile (the rim) is resolved.  Derived
# from RbmkGeo / RbmkLibZ by substitution.  Rings: 0.1000-0.30026-0.412689-
# 0.500469-0.5750 cm.  Inner-ring rods: MIX 6 10 11 12 (sets 1 6 7 8); outer-ring
# rods: MIX 7 13 14 15 (sets 2 9 10 11); Zr keeps sets 3-5.  Each ring is one
# flux region (4 per pellet, against 3 in RbmkGeo).
def _derive(src, dst, subs, why):
    t = open(os.path.join(PROC, src)).read()
    for a, b in subs:
        assert t.count(a) == 1, (src, a)
        t = t.replace(a, b)
    open(os.path.join(PROC, dst), "w").write(
        f"*----\n*  GENERATED by decks/scripts/gen_meth.py from {src}: {why}\n"
        f"*  Edit the generator, not this file.\n*----\n" + t)

_R = "0.1000 0.30026 0.412689 0.500469 0.5750"
_derive("RbmkGeo.c2m", "RbmkGeoRim.c2m", [
    ("  ::: ROD1 := GEO: TUBE 4\n    MIX  3 6 3 8 ", "  ::: ROD1 := GEO: TUBE 7\n    MIX  3 6 10 11 12 3 8 "),
    ("RADIUS 0.0000 0.1000 0.5750 0.5850 0.6790 ;", f"RADIUS 0.0000 {_R} 0.5850 0.6790 ;"),
    ("    MIX  3 7 3 8   NPIN 12", "    MIX  3 7 13 14 15 3 8   NPIN 12"),
    ("  ::: ROD1 := GEO: ROD1 SPLITR 1 3 1 1 ;", "  ::: ROD1 := GEO: ROD1 SPLITR 1 1 1 1 1 1 1 ;"),
    ("  ::: ROD2 := GEO: ROD2 SPLITR 1 3 1 1 ;", "  ::: ROD2 := GEO: ROD2 SPLITR 1 1 1 1 1 1 1 ;"),
    ], "pellet in 4 equal-volume rings (H6).")
_fuel = "".join(
    f"\n* MIX {m}: UO2 fuel, {ring} ring, pellet ring {i + 2} of 4 (H6)\n"
    f"  MIX    {m}  <<tfuel>>\n"
    f"     U235    = U235    4.69750E-4  {st}\n"
    f"     U238    = U238    2.27272E-2  {st}\n"
    f"     O16     = O16     4.63940E-2\n"
    for ring, mixes, sets in (("inner", (10, 11, 12), (6, 7, 8)), ("outer", (13, 14, 15), (9, 10, 11)))
    for i, (m, st) in enumerate(zip(mixes, sets)))
# Control for H6: same rings and mixtures, but every ring of a rod shares its
# rod's self-shielding set, so only the geometry / flux mesh differs from zr361.
_fuel_s = re.sub(r"(U23[58]    = U23[58]    \S+  )(\d+)",
                 lambda m: m.group(1) + ("1" if int(m.group(2)) in (6, 7, 8) else "2"), _fuel)
_derive("RbmkLibZ.c2m", "RbmkLibRimS.c2m", [
    ("  NMIX 9\n", "  NMIX 15\n"),
    ("     Nb93    = Nb93    4.24560E-4\n;\n", "     Nb93    = Nb93    4.24560E-4\n" + _fuel_s + ";\n"),
    ], "pellet rings as MIX 10-15 sharing sets 1 / 2 (H6 control).")
_derive("RbmkLibZ.c2m", "RbmkLibRim.c2m", [
    ("  NMIX 9\n", "  NMIX 15\n"),
    ("     Nb93    = Nb93    4.24560E-4\n;\n", "     Nb93    = Nb93    4.24560E-4\n" + _fuel + ";\n"),
    ], "pellet rings as MIX 10-15 (H6).")
# A6a: Nb-93 has no subgroup data, so it can only be left unshielded; removing
# it outright bounds what that approximation can be worth.
_t = open(os.path.join(PROC, "RbmkLibZ.c2m")).read()
_nb = [l for l in _t.splitlines(keepends=True) if l.startswith("     Nb93    = Nb93 ")]
assert len(_nb) == 3, _nb
for l in _nb:
    _t = _t.replace(l, "", 1)
open(os.path.join(PROC, "RbmkLibZnoNb.c2m"), "w").write(
    "*----\n*  GENERATED by decks/scripts/gen_meth.py from RbmkLibZ.c2m: Nb-93 removed\n"
    "*  (A6a bound).  Edit the generator, not this file.\n*----\n" + _t)

TEMPLATE = """*----
*  METHOD STUDY {vid} -- hypothesis {hyp}: {desc}
*
*  GENERATED by decks/scripts/gen_meth.py -- edit that, not this file.
*  Fresh fuel, dca 0.72 / 0.35 / 0.02, TF {tf:.0f} K, TG {tg:.0f} K, coolant {tc:.0f} K.
*  Output:  METHTAB {num} <dca> <k-inf>
*----
LINKED_LIST LIBRARY LIBSS GEOSS GEOFL TRKSS TRK SYS FLUX DONNEES ;
SEQ_BINARY  FTRKSS FTRK ;
MODULE      LIB: GEO: NXT: USS: ASM: FLU: GREP: DELETE: UTL: END: {mods};
PROCEDURE   {lib} {geoproc} ;

REAL tfuel := {tf:.1f} ;
REAL tgrap := {tg:.1f} ;
REAL tcool := {tc:.1f} ;
INTEGER ndc := 3 ;
INTEGER iv ;
REAL dca kinf ;

DONNEES := UTL: :: CREA 'dca' <<ndc>> = 0.72 0.35 0.02 ;

{geo}
TRKSS FTRKSS := NXT: GEOSS ::
  EDIT 0 TITLE 'METH-SS' ALLG BATCH 100 {ss} ;
TRK FTRK := NXT: GEOFL ::
  EDIT 0 TITLE 'METH-FLUX' ALLG BATCH 100 {fl} ;
{mccg}
EVALUATE iv := 0 ;
WHILE iv ndc < DO
  EVALUATE iv := iv 1 + ;
  GREP: DONNEES :: GETVAL 'dca' <<iv>> >>dca<< ;
  LIBRARY := {lib} :: <<dca>> <<tfuel>> <<tgrap>> <<tcool>> ;
  LIBSS := USS: LIBRARY TRKSS FTRKSS :: EDIT 0 {uss} ;
  SYS   := ASM: LIBSS TRK FTRK :: EDIT 0{arm} ;
  FLUX  := FLU: LIBSS TRK{ftrk} SYS :: TYPE K EXTE 1.0E-6 ;
  GREP: FLUX :: GETVAL 'K-INFINITY' 1 >>kinf<< ;
  ECHO "METHTAB" {num} dca kinf ;
  LIBRARY LIBSS SYS FLUX := DELETE: LIBRARY LIBSS SYS FLUX ;
ENDWHILE ;

ECHO "rbmk_meth_{vid} completed" ;
END: ;
QUIT .
"""

# Library binding and USS: options.  GRMIN 18 is a 172-group index (and was
# shown bit-identical to the library default there); on the SHEM structures
# the default is used instead.
ACCESS = {"shem281": "shem281.access", "shem295": "shem295.access",
          "zrshem": "shem281.access", "allfix": "shem281.access"}
ACCESS["shem361"] = ACCESS["zr361"] = ACCESS["best361"] = "shem361.access"
for k in (*MOC, "rim361", "rim361t2", "rim361t4", "best361k8", "zr361nonb", "tgrid",
          "omc10", "omc15", "rim361s"):
    ACCESS[k] = "shem361.access"
ACCESS["zr370"] = "shem370.access"
USS_OPT = {k: "PASS 2" for k in ACCESS}
# SHEM-295/361 hit USSIT1's default 50-iteration cap (convergence test is a
# relative 1e-4, USSIT1.f:413).  MAXS is the USS: keyword for the cap (USS.f:265).
for k in ("shem295", "shem361", "zr361", "best361", *MOC, "rim361", "zr370", "best361k8",
          "zr361nonb", "tgrid", "rim361t2", "rim361t4", "omc10", "omc15", "rim361s"):
    USS_OPT[k] = "PASS 2 MAXST 300"

for vid, (num, hyp, desc, lib, geo, ss, fl) in VARIANTS.items():
    geoproc = geo.split(":=")[1].split()[0]
    moc = MOC.get(vid, 0)
    if moc >= 2:
        fl = f"ANIS {moc} {fl}"
    deck = os.path.join(DATA, f"rbmk_meth_{vid}.x2m")
    with open(deck, "w") as f:
        f.write(TEMPLATE.format(vid=vid, hyp=hyp, desc=desc, lib=lib, geo=geo,
                                geoproc=geoproc, ss=ss, fl=fl, num=num,
                                **dict(zip(("tf", "tg", "tc"), TEMPS.get(vid, (900.0, 750.0, 573.0)))),
                                mods="MCCGT: " if moc else "",
                                mccg=(f"TRK := MCCGT: TRK FTRK GEOFL :: {MOC_OPTS} ;\n"
                                      if moc else ""),
                                arm=" ARM" if moc else "", ftrk=" FTRK" if moc else "",
                                uss=USS_OPT.get(vid, "PASS 2 GRMIN 18")))
    acc = os.path.join(DATA, f"rbmk_meth_{vid}.access")
    if os.path.lexists(acc):
        os.remove(acc)
    os.symlink("../../common/" + ACCESS.get(vid, "dlib99.access"), acc)
    print("wrote", os.path.relpath(deck, HERE))

# ---------------------------------------------------------------------------
# Burnup variants: rbmk_a5_void.x2m with ONE procedure swapped.  The control
# is rbmk_a5_void.x2m itself (its VOIDTAB rows).  Derived by substitution so
# the depletion and branch logic stays byte-identical to the production deck.
BU_VARIANTS = {
    "puss": ("H8", "depletion heavy nuclides self-shielded", "RbmkLib", "RbmkLibP"),
    "buzr361": ("H7+H9", "Zr self-shielded on SHEM-361 (production mesh)",
                "RbmkLib", "RbmkLibZ"),
}
# Burnup variants that also change the library binding / USS: options.
BU_ACCESS = {"buzr361": "shem361.access"}
BU_USS = {"buzr361": ("PASS 2 GRMIN 18", "PASS 2 MAXST 300")}
src = open(os.path.join(DATA, "rbmk_a5_void.x2m")).read()
for vid, (hyp, desc, old, new) in BU_VARIANTS.items():
    n = src.count(f"{old} ")
    assert n >= 3, f"expected every {old} call to be replaced, found {n}"
    body = src.replace(f"PROCEDURE   {old} ", f"PROCEDURE   {new} ")
    body = body.replace(f":= {old} ::", f":= {new} ::")
    assert f":= {old} ::" not in body
    if vid in BU_USS:
        u_old, u_new = BU_USS[vid]
        assert body.count(u_old) >= 3, f"expected every USS: call to use {u_old}"
        body = body.replace(u_old, u_new)
    head = (f"*----\n*  METHOD STUDY {vid} -- hypothesis {hyp}: {desc}\n"
            f"*  GENERATED by decks/scripts/gen_meth.py from rbmk_a5_void.x2m with\n"
            f"*  {old} -> {new}.  Edit the generator, not this file.\n*----\n")
    deck = os.path.join(DATA, f"rbmk_meth_{vid}.x2m")
    open(deck, "w").write(head + body)
    acc = os.path.join(DATA, f"rbmk_meth_{vid}.access")
    if os.path.lexists(acc):
        os.remove(acc)
    os.symlink("../../common/" + BU_ACCESS.get(vid, "dlib99.access"), acc)
    print("wrote", os.path.relpath(deck, HERE))
