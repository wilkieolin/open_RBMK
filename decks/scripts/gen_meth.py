"""Generate the DRAGON method-study decks (PROGRESS.md, "Method gap").

Every deck runs the FRESH cell at dca 0.72 / 0.35 / 0.02 (TF 900 K, TG 750 K,
coolant 573 K, bound hydrogen) and prints

    METHTAB <variant-id> <dca> <k-inf>

Each variant changes exactly one thing relative to 'ctrl', which is the
pre-Phase-C production cell (172 groups, Zr unshielded: RbmkLibU) and reproduces
rbmk_h2otest.x2m's bound-hydrogen branch as it was before 2026-09-25 (3)
(k-inf 1.304123).  Since Phase C, production (RbmkLib on SHEM-361) is zr361.
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
              "RbmkLibU", GEO, SS_TRK, FL_TRK),
    "fine1": (1, "H3", "RbmkGeoFine k=1 -- must equal ctrl",
              "RbmkLibU", "GEOSS GEOFL := RbmkGeoFine :: 1 ;", SS_TRK, FL_TRK),
    "fine2": (2, "H3", "flat-flux regions split 2x, tracking densified to match",
              "RbmkLibU", "GEOSS GEOFL := RbmkGeoFine :: 2 ;", SS_TRK, "TISO 20 60.0"),
    "fine4": (3, "H3", "flat-flux regions split 4x, tracking densified to match",
              "RbmkLibU", "GEOSS GEOFL := RbmkGeoFine :: 4 ;", SS_TRK, "TISO 30 120.0"),
    "trk2":  (4, "H4", "flux tracking 30 angles / 60 per cm",
              "RbmkLibU", GEO, SS_TRK, "TISO 30 60.0"),
    "trk4":  (5, "H4", "flux tracking 60 angles / 120 per cm",
              "RbmkLibU", GEO, SS_TRK, "TISO 60 120.0"),
    "tspc":  (6, "H2", "specular (mirror) boundary on the flux solution",
              "RbmkLibU", GEO, SS_TRK, "TSPC 20 30.0"),
    "zrfine4": (8, "H7+H3", "Zr self-shielded AND flat-flux regions split 4x",
              "RbmkLib", "GEOSS GEOFL := RbmkGeoFine :: 4 ;", SS_TRK, "TISO 30 120.0"),
    "sstrk": (9, "H6'", "self-shielding tracking 20 angles / 40 per cm (flux unchanged)",
              "RbmkLibU", GEO, "TISO 20 40.0", FL_TRK),
    "shem281": (10, "H9", "SHEM-281 library (fine groups through U-238 resonances)",
              "RbmkLibU", GEO, SS_TRK, FL_TRK),
    "shem295": (11, "H9", "SHEM-295 library, subgroup iteration cap raised to 300",
              "RbmkLibU", GEO, SS_TRK, FL_TRK),
    "shem361": (14, "H9", "SHEM-361 library, subgroup iteration cap raised to 300",
              "RbmkLibU", GEO, SS_TRK, FL_TRK),
    "zr361": (15, "H7+H9", "Zr self-shielded on SHEM-361",
              "RbmkLib", GEO, SS_TRK, FL_TRK),
    "best361": (16, "H7+H9+H3", "Zr self-shielded, SHEM-361, flat-flux regions split 4x",
              "RbmkLib", "GEOSS GEOFL := RbmkGeoFine :: 4 ;", SS_TRK, "TISO 30 120.0"),
    "zrshem": (12, "H7+H9", "Zr self-shielded on SHEM-281",
              "RbmkLib", GEO, SS_TRK, FL_TRK),
    "allfix": (13, "H7+H9+H3", "Zr self-shielded, SHEM-281, flat-flux regions split 4x",
              "RbmkLib", "GEOSS GEOFL := RbmkGeoFine :: 4 ;", SS_TRK, "TISO 30 120.0"),
    "zrss":  (7, "H7", "Zr self-shielded (RbmkLib since C1; Nb93 has no subgroup data)",
              "RbmkLib", GEO, SS_TRK, FL_TRK),
    # H5: method of characteristics on zr361.  moc1 keeps the CP physics
    # (isotropic + transport correction) and must reproduce zr361; moc2 / moc3
    # carry P1 / P2 scattering explicitly with the transport correction off.
    "moc1": (17, "H5", "MOC flux, isotropic + transport correction (zr361 physics)",
              "RbmkLib", GEO, SS_TRK, FL_TRK),
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
    # A4 on the MOC lineage: CP at 8x did not finish its first ASM: in 3 h.
    "bestmoc8": (37, "H3", "bestmoc with flat-flux regions split 8x",
              "RbmkLibZN2", "GEOSS GEOFL := RbmkGeoFine :: 8 ;", SS_TRK, "TISO 40 240.0"),
    # Gate B, transport only: bestmoc settings on OpenMC's energy-deposition fuel,
    # against openmc/accident_ref.json (same fuel, 10P graphite).
    "oedbest10": (38, "B3", "bestmoc on OpenMC fuel (energy-deposition) at 10 MWd/kg",
              "RbmkOED10N2", "GEOSS GEOFL := RbmkGeoFine :: 4 ;", SS_TRK, "TISO 30 120.0"),
    "oedbest15": (39, "B3", "bestmoc on OpenMC fuel (energy-deposition) at 15 MWd/kg",
              "RbmkOED15N2", "GEOSS GEOFL := RbmkGeoFine :: 4 ;", SS_TRK, "TISO 30 120.0"),
    "omc10moc": (31, "H10+H5", "omc10 with MOC P1 flux (is the H5 shift burnup-independent?)",
              "RbmkOMC10N2", GEO, SS_TRK, FL_TRK),
    "omc15moc": (32, "H10+H5", "omc15 with MOC P1 flux",
              "RbmkOMC15N2", GEO, SS_TRK, FL_TRK),
    "oed10": (33, "H10", "zr361 with OpenMC's fuel at 10 MWd/kg, depletion normalised on deposited energy",
              "RbmkLibOED10", GEO, SS_TRK, FL_TRK),
    "oed15": (34, "H10", "zr361 with OpenMC's fuel at 15 MWd/kg, depletion normalised on deposited energy",
              "RbmkLibOED15", GEO, SS_TRK, FL_TRK),
    # H12: the self-shielding method itself, for the nominal residual that no
    # other hypothesis closes.  zr361 with USS: (subgroups) swapped for SHI:
    # (Stamm'ler, Livolant-Jeanpierre) or TONE: (tone method).
    "shi361": (35, "H12", "zr361 self-shielded by SHI: (Stamm'ler + Livolant-Jeanpierre)",
              "RbmkLib", GEO, SS_TRK, FL_TRK),
    "tone361": (36, "H12", "zr361 self-shielded by TONE:",
              "RbmkLib", GEO, SS_TRK, FL_TRK),
    "zr370": (21, "H9", "SHEM-370 library (group convergence, 361 -> 370)",
              "RbmkLib", GEO, SS_TRK, FL_TRK),
    "best361k8": (22, "H3", "best361 with flat-flux regions split 8x",
              "RbmkLib", "GEOSS GEOFL := RbmkGeoFine :: 8 ;", SS_TRK, "TISO 40 240.0"),
    "zr361nonb": (23, "A6a", "zr361 with Nb-93 removed (bounds leaving it unshielded)",
              "RbmkLibZnoNb", GEO, SS_TRK, FL_TRK),
    "tgrid": (24, "H11", "zr361 at library-grid temperatures, fuel 900 / graphite 800 / coolant 600 K",
              "RbmkLib", GEO, SS_TRK, FL_TRK),
}
# Temperature overrides (fuel, graphite, coolant) in K; default 900 / 750 / 573.
TEMPS = {"tgrid": (900.0, 800.0, 600.0)}

# MOC order per variant (absent = collision probabilities).  Options follow
# upstream RegtestCNG_mccg.x2m; the same string is in openmc/srp94_common.py.
MOC = {"moc1": 1, "moc2": 2, "moc3": 3, "bestmoc": 2, "bestmoc8": 2, "oedbest10": 2, "oedbest15": 2, "omc10moc": 2, "omc15moc": 2}
# Self-shielding module per variant (absent = USS: with USS_OPT).
SSMOD = {"shi361": ("SHI:", "LJ"), "tone361": ("TONE:", "")}
MOC_OPTS = "EDIT 0 LCMD 3 MAXI 1 EPSI 1E-5 HDD 0. MCU 400000 KRYL 0 SCR 0 AAC 100 TMT"

# Library procedures for the anisotropic MOC variants: RbmkLib with the
# transport correction off and the Legendre order raised.  Derived by
# substitution, so they cannot drift from RbmkLib (standing rule 6).
PROC = os.path.join(DATA, "rbmk_proc")
_libz = open(os.path.join(PROC, "RbmkLib.c2m")).read()
for name, anis in (("RbmkLibZN2", 2), ("RbmkLibZN3", 3)):
    assert _libz.count("  CTRA APOL\n  ANIS 2\n") == 1
    body = _libz.replace("  CTRA APOL\n  ANIS 2\n", f"  CTRA NONE\n  ANIS {anis}\n")
    open(os.path.join(PROC, f"{name}.c2m"), "w").write(
        f"*----\n*  GENERATED by decks/scripts/gen_meth.py from RbmkLib.c2m with\n"
        f"*  CTRA APOL / ANIS 2 -> CTRA NONE / ANIS {anis}.  For the H5 MOC variants\n"
        f"*  only: collision-probability decks must keep the transport correction.\n*----\n"
        + body)

# The OpenMC-isotopics libraries (written by openmc/isotopics_to_dragon.py) with
# the transport correction off, for the MOC P1 variants at burnup.  Named
# RbmkOMC<bu>N2: CLE-2000 procedure names are limited to 12 characters.
for src_, bu in [(p, b) for p in ("OMC", "OED") for b in (10, 15)]:
    f = os.path.join(PROC, f"RbmkLib{src_}{bu}.c2m")
    if os.path.exists(f):
        t = open(f).read()
        assert t.count("  CTRA APOL\n  ANIS 2\n") == 1
        open(os.path.join(PROC, f"Rbmk{src_}{bu}N2.c2m"), "w").write(
            f"*----\n*  GENERATED by decks/scripts/gen_meth.py from RbmkLib{src_}{bu}.c2m with\n"
            f"*  CTRA NONE (MOC P1 variants only).\n*----\n"
            + t.replace("  CTRA APOL\n  ANIS 2\n", "  CTRA NONE\n  ANIS 2\n"))

# H6: the pellet in 4 equal-volume rings, each its own mixture and self-shielding
# set, so U-238's radial self-shielding profile (the rim) is resolved.  Derived
# from RbmkGeo / RbmkLib by substitution.  Rings: 0.1000-0.30026-0.412689-
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
_derive("RbmkLib.c2m", "RbmkLibRimS.c2m", [
    ("  NMIX 9\n", "  NMIX 15\n"),
    ("     Nb93    = Nb93    4.24560E-4\n;\n", "     Nb93    = Nb93    4.24560E-4\n" + _fuel_s + ";\n"),
    ], "pellet rings as MIX 10-15 sharing sets 1 / 2 (H6 control).")
_derive("RbmkLib.c2m", "RbmkLibRim.c2m", [
    ("  NMIX 9\n", "  NMIX 15\n"),
    ("     Nb93    = Nb93    4.24560E-4\n;\n", "     Nb93    = Nb93    4.24560E-4\n" + _fuel + ";\n"),
    ], "pellet rings as MIX 10-15 (H6).")
# A6a: Nb-93 has no subgroup data, so it can only be left unshielded; removing
# it outright bounds what that approximation can be worth.
_t = open(os.path.join(PROC, "RbmkLib.c2m")).read()
_nb = [l for l in _t.splitlines(keepends=True) if l.startswith("     Nb93    = Nb93 ")]
assert len(_nb) == 3, _nb
for l in _nb:
    _t = _t.replace(l, "", 1)
open(os.path.join(PROC, "RbmkLibZnoNb.c2m"), "w").write(
    "*----\n*  GENERATED by decks/scripts/gen_meth.py from RbmkLib.c2m: Nb-93 removed\n"
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
  {ssline}
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
          "omc10", "omc15", "rim361s", "omc10moc", "omc15moc", "oed10", "oed15",
          "shi361", "tone361", "bestmoc8", "oedbest10", "oedbest15"):
    ACCESS[k] = "shem361.access"
ACCESS["zr370"] = "shem370.access"
USS_OPT = {k: "PASS 2" for k in ACCESS}
# SHEM-295/361 hit USSIT1's default 50-iteration cap (convergence test is a
# relative 1e-4, USSIT1.f:413).  MAXS is the USS: keyword for the cap (USS.f:265).
for k in ("shem295", "shem361", "zr361", "best361", *MOC, "rim361", "zr370", "best361k8",
          "zr361nonb", "tgrid", "rim361t2", "rim361t4", "omc10", "omc15", "rim361s",
          "omc10moc", "omc15moc", "oed10", "oed15",
          "bestmoc8", "oedbest10", "oedbest15"):
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
                                mods=("MCCGT: " if moc else "")
                                     + (SSMOD[vid][0] + " " if vid in SSMOD else ""),
                                # SHI: / TONE: modify a library in place (upstream:
                                # LIBRARY := TONE: LIBRARY ...), so copy first.
                                ssline=(f"LIBSS := LIBRARY ;\n  LIBSS := {SSMOD[vid][0]} LIBSS TRKSS FTRKSS"
                                        f" :: EDIT 0 {SSMOD[vid][1]} ;" if vid in SSMOD else
                                        f"LIBSS := USS: LIBRARY TRKSS FTRKSS :: EDIT 0 "
                                        f"{USS_OPT.get(vid, 'PASS 2 GRMIN 18')} ;"),
                                mccg=(f"TRK := MCCGT: TRK FTRK GEOFL :: {MOC_OPTS} ;\n"
                                      if moc else ""),
                                arm=" ARM" if moc else "", ftrk=" FTRK" if moc else "",
                                ))
    acc = os.path.join(DATA, f"rbmk_meth_{vid}.access")
    if os.path.lexists(acc):
        os.remove(acc)
    os.symlink("../../common/" + ACCESS.get(vid, "dlib99.access"), acc)
    print("wrote", os.path.relpath(deck, HERE))

# ---------------------------------------------------------------------------
# Burnup variants (puss, buzr361) were retired 2026-09-25 (3), when Phase C made
# RbmkLib Zr-self-shielded on SHEM-361: rbmk_a5_void.x2m IS buzr361 now.  The
# decks are in git history (commit a07157f).

# ---------------------------------------------------------------------------
# Depletion step-size convergence (2026-09-26): rbmk_a5_void.x2m with only the
# burnup list (and, for dstep50x, the EVO: extrapolation) changed.  Found when
# the rebuilt COMPO deck (2.5 MWd/kg steps through 5-15) gave k-inf 1.097439 at
# 10 MWd/kg against a5_void's 1.099025 (5 MWd/kg steps).  Compare VOIDTAB rows.
A5 = open(os.path.join(DATA, "rbmk_a5_void.x2m")).read()
A5_GRID = "INTEGER nbu := 7 ;"
A5_BURN = "   0.0   500.0  2000.0  5000.0  10000.0  15000.0  20000.0 ;"
assert A5.count(A5_GRID) == 1 and A5.count(A5_BURN) == 1 and A5.count(" NOEX ") == 1


def _grid(step):
    """a5_void's nodes, each interval split evenly so no step exceeds `step`."""
    nodes = [0.0, 500.0, 2000.0, 5000.0, 10000.0, 15000.0, 20000.0]
    g = [0.0]
    for lo, hi in zip(nodes, nodes[1:]):
        n = max(1, -(-int(hi - lo) // int(step)))
        g += [lo + (hi - lo) * i / n for i in range(1, n + 1)]
    return g


DSTEP = {
    "dstep25": ("steps <= 2.5 MWd/kg (NOEX)", _grid(2500.0), "NOEX"),
    "dstep125": ("steps <= 1.25 MWd/kg (NOEX)", _grid(1250.0), "NOEX"),
    "dstep50x": ("a5_void's 5 MWd/kg steps, linear rate extrapolation (EXTR 1)",
                 [0.0, 500.0, 2000.0, 5000.0, 10000.0, 15000.0, 20000.0], "EXTR 1"),
}
for vid, (desc, grid, extr) in DSTEP.items():
    body = A5.replace(A5_GRID, f"INTEGER nbu := {len(grid)} ;")
    lines, row = [], "  "
    for x in grid:
        if len(row) > 60:
            lines.append(row); row = "  "
        row += f" {x:.1f}"
    lines.append(row + " ;")
    body = body.replace(A5_BURN, "\n".join(lines))
    body = body.replace(" NOEX ", f" {extr} ")
    head = (f"*----\n*  DEPLETION STEP STUDY {vid}: {desc}\n"
            f"*  GENERATED by decks/scripts/gen_meth.py from rbmk_a5_void.x2m.\n*----\n")
    open(os.path.join(DATA, f"rbmk_meth_{vid}.x2m"), "w").write(head + body)
    acc = os.path.join(DATA, f"rbmk_meth_{vid}.access")
    if os.path.lexists(acc):
        os.remove(acc)
    os.symlink("../../common/rbmk.access", acc)
    print("wrote", f"rbmk_meth_{vid}.x2m")
