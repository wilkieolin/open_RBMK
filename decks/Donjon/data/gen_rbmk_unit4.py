#!/usr/bin/env python3
"""A6.5 -- the Chernobyl Unit 4 core, generated from the sourced channel map.

    python decks/Donjon/data/gen_rbmk_unit4.py    # -> rbmk_unit4_core.don

WHY THIS REPLACES gen_rbmk_realistic.py.  That generator picked the 1661 cells
nearest the centre of a 590 cm circle and pasted in IAEA PWR constants.  Neither
survives contact with the real reactor: Unit 4 has 1888 channel positions on a
staircase outline that no centred circle reproduces (circle cell counts step by
8, and the nearest fit is one channel off), the rods are interspersed with the
fuel rather than set outside it, and the cross sections have to come from the
MULTICOMPOs.  `sources/derived/unit4_channel_map.csv` settles which position
holds what -- see the A6d section of PROGRESS.md for how it was established and
what in it is still an assumption.

WHAT IS REAL HERE AND WHAT IS NOT.  Being explicit, because A2's core deck was
misread as physics once already:

  * REAL: the outline, the 1888 positions, which of them hold fuel and which
    hold a CPS channel, the 25 cm pitch, and the fuel cross sections (from
    `_ACompo` through NCR:, per channel, at the burnup the fuel map carries).
  * REAL: the CPS water-column cross sections, from `_CCompoWAT`.
  * REAL: the graphite stack boundary and the four reflector rings, from
    _RCompo zones 5-8.  Measured 2026-10-01: the radial reflector is worth
    131 pcm in this core and only 2.6 pcm leaks past it, so the 7152 pcm
    homogenisation error Phase 1b measured on a 4-fuel/4-reflector strip
    cannot propagate -- the whole band the dataset can move k in is ~130 pcm
    wide, and collapsing all four rings onto one dataset moves k by 3.9 pcm.
    tools/u4_leakage.sh regenerates that table.
  * FLAT, PENDING A6d: the burnup.  Every fuel channel is at 10900 MWd/t, the
    Unit 4 core average, because the burnup PLACEMENT map does not exist yet.
    The per-channel route (INST-BURN off the fuel map) is wired but unfed.
    Channel-power peaking is therefore 1.90 max/avg against a design ~1.4.
  * NOT YET HERE: the rods.  Every CPS channel is modelled as a full-height
    water column, i.e. all rods withdrawn.  Rods arrive as DEVINI:/DSET:
    devices, carrying A6.4's measured one-signed bias: a rod inserted with
    today's CPS data is 7-10 % short on worth.
  * NOT YET HERE: xenon, and any thermal-hydraulic feedback.

k FROM THIS DECK IS REPORTED, NOT ASSERTED.  k = 1.018278 as of 2026-10-01
with the flat burnup, no rods and no xenon.  The gate for this increment is
that the geometry, the fuel map and the solver chain are right and FLUD:
converges, not the eigenvalue.

SOLVER.  TRIVAT DUAL 1 1, not the MCFD 1 that A2 chose and TIER_A_WORKPLAN A2.3
still recommends.  Measured 2026-09-28: MCFD 1 loses 31-34 % of the absorber
worth on the A6.4 gate and cannot carry a converged SPH equivalence at all,
while DUAL 1 1 costs 8 % more wall clock (2.11 s vs 1.95 s) and 17 MB on this
same geometry, and the two agree to 0.7 pcm when no absorber is present.
"""
import csv
import math
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", ".."))
MAP = os.path.join(ROOT, "sources", "derived", "unit4_channel_map.csv")
# U4_REFL=0 strips the radial reflector -- the stack boundary collapses onto
# the core outline and the VOID boundary condition applies there.  The pair
# measures what the reflector is worth in THIS core, which is the number the
# strip-level interface error (PROGRESS.md, Phase 1b) has to be read against.
WITH_REFL = os.environ.get("U4_REFL", "1") != "0"
_RODS0 = os.environ.get("U4_RODS", "wat")
# A7 (U4_THM=1): couple the flux solve to THM: in a Picard loop.  The flow
# distribution is bracketed rather than chosen, because no total core flow is
# sourced yet:
#   U4_FLOW=prop  every channel valved to its own power, normalised on
#                 [D] p.95's pairing of 3100 kW with 30 t/h.  This is what an
#                 RBMK does -- 1661 individually valved channels, set to
#                 equalise exit quality -- so it is the design intent, and it
#                 makes the exit quality flat by construction.
#   U4_FLOW=unif  one velocity everywhere, at the core-average of the same
#                 normalisation.  The hot channels then boil much harder.
# The real reactor is between the two, and the pair bounds it.  'prop' needs
# the channel powers, which come from a previous run's POWER-CHAN dump.
WITH_THM = os.environ.get("U4_THM", "0") != "0"
FLOW = os.environ.get("U4_FLOW", "prop")
PCHAN = os.environ.get("U4_PCHAN", "")
_TILT0 = os.environ.get("U4_TILT", "0")
_DCA0 = os.environ.get("U4_DCA", "0.72")
_BURN0 = os.environ.get("U4_BURNMAP", "flat")
# U4_VOIDB=1 stages _ACompoVB (tools/compo_voidB.py: bracket B's OpenMC void
# worth written into the fuel COMPO as a thermal-absorption edit) in place of
# _ACompo.  Keyed on the file's content, so a rebuilt correction can never be
# served a deck generated against an older one (standing rule 7).
VOIDB = os.environ.get("U4_VOIDB", "0") != "0"
_VBFILE = os.path.join(ROOT, "5.1", "Dragon", "compo", "_ACompoVB")
if VOIDB:
    if not os.path.exists(_VBFILE):
        raise SystemExit(f"U4_VOIDB=1: {_VBFILE} not found; run tools/compo_voidB.py")
    import hashlib as _hl
    _VSFX = "_vB" + _hl.md5(open(_VBFILE, "rb").read()).hexdigest()[:6]
else:
    _VSFX = ""
# U4_CPSB=1 stages _CCompoABScB/_CCompoDSPcB (tools/compo_cpsB.py) in place of
# the ABS and DSP CPS COMPOs: mixture 5 rebuilt as WAT + f (T - WAT) so the
# core-equivalent A64V supercell carries OpenMC's absorber and displacer worth
# at the core's CPS state (PROGRESS (35)).  Keyed on both files' content.
CPSB = os.environ.get("U4_CPSB", "0") != "0"
_CBFILES = [os.path.join(ROOT, "5.1", "Dragon", "compo", f"_CCompo{t}cB")
            for t in ("ABS", "DSP")]
if CPSB:
    for _f in _CBFILES:
        if not os.path.exists(_f):
            raise SystemExit(f"U4_CPSB=1: {_f} not found; run tools/compo_cpsB.py fit")
    import hashlib as _hl
    _VSFX += "_cB" + _hl.md5(b"".join(open(_f, "rb").read()
                                      for _f in _CBFILES)).hexdigest()[:6]
_BSFX = _VSFX + ("" if _BURN0 == "flat" else "_b" + _BURN0) + (
    "" if os.environ.get("U4_XEBINS", "1") == "1"
    else "_n" + os.environ.get("U4_XEBINS", "1")
         + ("" if os.environ.get("U4_XEAX", "0") == "0" else "ax")
         # the field is built from these channel powers (chan_power), so the
         # stem carries their content whenever a field exists (rule 7)
         + ("" if not os.environ.get("U4_PCHAN") else
            "p" + __import__("hashlib").md5(
                open(os.environ["U4_PCHAN"], "rb").read()).hexdigest()[:6])
         + ("" if os.environ.get("U4_XEHIST", "0123") == "0123"
            else "_h" + os.environ.get("U4_XEHIST", "0123").replace(".", ""))) + (
    "" if os.environ.get("U4_XENON", "stored") == "stored"
    else "_xe" + os.environ.get("U4_XENON", "stored").replace(".", "").replace("+", "")[:8])
# content-addressed on the depth file, so a solved pattern can never be served
# a deck built from a different one (standing rule 7)
_RD0 = os.environ.get("U4_RODDEPTH", "")
if _RD0:
    import hashlib as _hl
    _BSFX += "_rd" + _hl.md5(open(_RD0, "rb").read()).hexdigest()[:8]
# U4_DEV=1 builds the 211 CPS rods as DONJON ROD-DEVICES (DEVINI:/NEWMAC:)
# instead of writing their absorber and displacer into the GEO: MIX map.  A8
# needs this: a base-map rod cannot move, and the mixture map is fixed once
# GEO:/USPLIT:/TRIVAT: have run.  See devices() for the geometry and for why
# each rod costs TWO single-part devices rather than one three-part one.
_DEV0 = os.environ.get("U4_DEV", "0")
DEV = _DEV0 != "0"
# U4_DEVQ=0 lets a device sit off the 25 cm plane boundary, which is the whole
# reason A8 needs devices.  It stays ON for the static comparison against the
# base map, because a base-map rod CAN only sit on a boundary and the two
# routes have to be asked the same question.
DEVQ = os.environ.get("U4_DEVQ", "1") != "0"
# U4_RODFULL=1 tracks the rods over ALL 32 planes instead of the 28 active
# ones, i.e. it lets a parked absorber sit in the axial reflector above the
# core and a driven displacer sit in the one below.  That is what the DEVICE
# route does unavoidably (NEWMVF.f:78-82 clips a part to the mesh, not to the
# core), so this is how the two routes are made to describe the SAME geometry
# and compared exactly.  It is also the more faithful model -- the base map's
# "rods are not tracked outside the active core" is an approximation -- but it
# is off by default so that every A6d result stands as published.
RODFULL = os.environ.get("U4_RODFULL", "0") != "0"
# --- A8.  U4_KIN=<n> appends n KINSOL: steps to the steady solve.
#
# U4_VROD is the rod speed in cm/s.  0.4 m/s is SOURCED: INSAG-7 p. 103 gives
# the EPS insertion speed, and it is consistent with the ~18 s the AZ-5 rods
# are reported to have taken over the 7 m travel.  U4_VROD=0 moves no rod,
# which is the null transient the kinetics assembly is checked with -- and it
# also avoids MOVPOS.f:80, which aborts on a speed <= 0.
#
# The DELAYED-NEUTRON DATA IS DELIBERATELY NOT GIVEN HERE.  KINRD1.f:130-141
# reads BETA-D and LAMBDA-D from the macrolib when BETA and LAMBDA are absent
# from the input, and KINXSD.f:106-146 then uses the macrolib's per-precursor
# NUSIGF01..06 and CHI01..06 directly (LFISD branch) instead of forming
# SGF*beta with a single scalar.  Our COMPO carries all of it -- NDEL=6 reaches
# the macrolib through NCRMAC.f:151-169 and MACINI.f:256-259 -- so leaving the
# keywords out keeps A5b's MEASURED beta as a burnup-dependent FIELD.  Passing
# BETA would replace that field with one core-uniform scalar (KINXSD.f:131).
KIN = int(os.environ.get("U4_KIN", "0"))
KINDT = float(os.environ.get("U4_DT", "0.001"))
VROD = float(os.environ.get("U4_VROD", "40.0"))
# U4_MOVGRP selects which device groups move, so the scram can be decomposed:
# "123" is the whole CPS (the default, kept so earlier results reproduce), "13" moves
# the absorbers while every displacer stays put, "2" moves only the displacers.
# The last two are NOT configurations of a real reactor -- the absorber and its
# displacer are one rigid rod -- they are the controls that say which part of
# the rod the reactivity came from.
# "12" is the 1986 AZ-5: the EPS signal did NOT drive the 21 bottom-entry USP
# rods.  INSAG-7 p. 46 lists "to insert shortened absorber rods into the core
# in response to an emergency protection signal" among proposals made before
# the accident and only implemented after it.  Driving them upward puts
# absorber exactly where the displacers' positive reactivity is (PROGRESS (29)).
# U4_MOVDIR=-1 withdraws instead of inserting, which is the sign control.
MOVGRP = os.environ.get("U4_MOVGRP", "123")
# U4_DEVADV="<abs>,<dsp>,<usp>" advances each device GROUP's position by its
# own amount, in cm, at generation time.  It exists to decompose the ramp
# statically: advancing only the absorbers, or only the displacers, separates
# the two contributions for the price of one static solve instead of a whole
# transient.  Neither single-group case is a configuration of a real reactor --
# a rod's absorber and its displacer are one rigid body -- so they are controls
# and are named as such in the deck header.
DEVADV = os.environ.get("U4_DEVADV", "")
_ADV = [0.0, 0.0, 0.0]
if DEVADV:
    _p = [float(x) for x in DEVADV.split(",")]
    if len(_p) != 3:
        raise SystemExit("U4_DEVADV wants three comma-separated cm advances: "
                         "absorbers,displacers,USP")
    _ADV = _p
MOVDIR = int(os.environ.get("U4_MOVDIR", "1"))
if MOVDIR not in (1, -1):
    raise SystemExit("U4_MOVDIR must be 1 (insert) or -1 (withdraw)")


def lambda_d():
    """The six precursor decay constants, READ OUT OF THE COMPO rather than
    transcribed, so they cannot drift from the library the cross sections came
    from (standing rules 1 and 7).

    They have to be given to INIKIN: explicitly, and the reason is an
    inconsistency in DONJON that only shows up when NBFIS > 1: NCRMAC.f:165
    stores LAMBDA-D with NDEL values, while MACINI.f:226-231 only propagates
    it when the length is NDEL*NF.  With our 18 fissile isotopes it looks for
    108 numbers, finds 6, and silently carries none -- so KINRD1.f:138 then
    stops with 'MISSING DATA FOR THE PRECURSOR DECAY CONSTANTS'.

    Supplying LAMBDA is exact, unlike supplying BETA: LLAD only fills PD, a
    6-vector either way, while LNUD would replace the macrolib's per-precursor
    NUSIGF01..06 with SGF*beta for one scalar beta (KINXSD.f:127-134).

    Both the fuel COMPO and the CPS COMPO are checked to agree, because
    MACINI: would otherwise have had a choice to make between them.
    """
    import itertools
    out = {}
    for name in ("_ACompo", "_CCompoABS"):
        f = os.path.join(ROOT, "5.1", "Dragon", "compo", name)
        if not os.path.exists(f):
            raise SystemExit(f"{f}: not found, and U4_KIN needs its LAMBDA-D")
        vals = None
        with open(f) as fh:
            for line in fh:
                if line.strip() == "LAMBDA-D":
                    vals = []
                    for nxt in fh:
                        if nxt.lstrip().startswith("->"):
                            break
                        vals.extend(float(x) for x in nxt.split())
                    break
        if not vals:
            raise SystemExit(f"{name}: no LAMBDA-D record found")
        out[name] = vals
    a, b = out["_ACompo"], out["_CCompoABS"]
    if len(a) != len(b) or max(abs(x - y) for x, y in zip(a, b)) > 1e-10:
        raise SystemExit(f"LAMBDA-D differs between the COMPOs: {a} vs {b}")
    return a


if KIN and not DEV:
    raise SystemExit("U4_KIN needs U4_DEV=1: a base-map rod cannot move")
# ONE definition of the device/kinetics part of the stem, used by both the
# core stem and the A7 stem below (standing rule 6).
_DEVSFX = (("" if not DEV else "_dev")
           + ("" if not os.environ.get("U4_DEVADV", "")
              else "_a" + os.environ.get("U4_DEVADV", "")
              .replace(",", "_").replace(".", ""))
           + ("" if os.environ.get("U4_RODFULL", "0") == "0" else "_rf")
           + ("" if not os.environ.get("U4_AXBURN", "") else "_ax"
              + __import__("hashlib").md5(os.environ["U4_AXBURN"].encode()
                                          + (open(os.environ["U4_AXBURN"][5:],
                                                  "rb").read()
                                             if os.environ["U4_AXBURN"]
                                             .startswith("file:") else b""))
              .hexdigest()[:6])
           + ("" if not KIN else "_kin%dv%g" % (KIN, VROD)
    + ("" if os.environ.get("U4_MOVGRP", "123") == "123"
       else "g" + os.environ.get("U4_MOVGRP", "123"))
    + ("" if os.environ.get("U4_MOVDIR", "1") == "1" else "out")
    + ("" if os.environ.get("U4_KINFB", "1") != "0" else "nofb")
    + ("" if not os.environ.get("U4_KINSHAPE") else "sh")
    + ("" if os.environ.get("U4_KINVOID", "0") == "0" else "vd")
    + ("" if float(os.environ.get("U4_FRLX", "1.0")) == 1.0
       else "fr" + os.environ["U4_FRLX"].replace(".", ""))
    + ("" if os.environ.get("U4_FLOWIT", "30") == "30"
       else "fi" + os.environ["U4_FLOWIT"])
    + ("" if os.environ.get("U4_CYCCAP", "1.0E-2") == "1.0E-2"
       else "cc" + os.environ["U4_CYCCAP"].replace(".", "").replace("-", "m"))
    + ("" if os.environ.get("U4_ERMAXC", "1.0E-3") == "1.0E-3"
       else "ec" + os.environ["U4_ERMAXC"].replace(".", "").replace("-", "m"))
    + ("" if os.environ.get("U4_NCRCLAMP", "0") == "0" else "cl")
    + ("" if os.environ.get("U4_DT", "0.001") == "0.001"
       else "dt" + os.environ.get("U4_DT", "0.001").replace(".", "").replace("-", ""))))
_STEM = ("rbmk_unit4_core" if WITH_REFL else "rbmk_unit4_norefl") + (
    "" if _RODS0 == "wat" else "_" + _RODS0) + (
    "" if _TILT0 == "0" else "_t" + _TILT0) + (
    "" if _DCA0 == "0.72" else "_d" + _DCA0.replace(".", "")) + _DEVSFX + _BSFX
if WITH_THM:
    # The A7 stem is built separately, but it MUST carry the same device,
    # kinetics and advance suffixes the non-THM stem does.  It did not, so a
    # U4_THM=1 U4_DEV=1 U4_KIN=5 deck was named plain "rbmk_unit4_a7" and
    # silently overwrote the A7 deck and invalidated its result -- standing
    # rule 7 exactly ("a cache without a key is a silent substitution"), and
    # the same provenance hazard section (20) was bitten by once already.
    _STEM = ("rbmk_unit4_a7" + ("" if _RODS0 == "wat" else "_" + _RODS0)
             + ("" if FLOW == "prop" else "_" + FLOW)
             + ("" if os.environ.get("U4_VOIDFB", "1") != "0" else "_nvf"
                + ("" if _DCA0 == "0.72" else "_d" + _DCA0.replace(".", "")))
             + ("" if os.environ.get("U4_TH", "nom") == "nom" else
                "_" + os.environ["U4_TH"]
                + ("" if os.environ.get("U4_SUBC", "3.0") == "3.0" else
                   "s" + os.environ["U4_SUBC"].replace(".", ""))
                + ("" if os.environ.get("U4_PACC", "200") == "200" else
                   "p" + os.environ["U4_PACC"].replace(".", ""))
                + ("" if os.environ.get("U4_QFRAC", "1.0") == "1.0" else
                   "q" + os.environ["U4_QFRAC"].replace(".", "")))
             # the channel powers 'prop' valves the flow by are an input too
             # (standing rule 7): key the stem on their content when given
             + ("" if not os.environ.get("U4_PCHAN") or FLOW != "prop" else
                "_pc" + __import__("hashlib").md5(
                    open(os.environ["U4_PCHAN"], "rb").read()).hexdigest()[:6])
             + ("" if os.environ.get("U4_THDUMP", "0") == "0" else "_thd")
             + _DEVSFX + _BSFX)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), _STEM + ".don")

PITCH = 25.0            # cm, the lattice pitch ([D], closed in the A6.1 sources)
NREF = 4                # radial reflector, columns (100 cm) -- [D] p.9, sourced
NPAD = int(os.environ.get("U4_NPAD", "5"))   # grid padding each side; 5 holds R_STACK
R_STACK = 28.14         # cells from the centroid: the graphite stack's outer
                        # radius, set so the column count matches [D]'s 2488
NZ_ACTIVE = 28          # 28 x 25 cm = 700 cm active height
NZ_REFL = 2             # axial graphite reflector, planes each end (50 cm)

# SOURCING NOTE, closed 2026-10-01.  NREF = 2 is too thin; NZ_REFL = 2 is right.
#
#   [D] p.9 is explicit and primary: "Активная зона имеет форму вертикального
#   цилиндра эквивалентным диаметром 11,8 и высотой 7 м.  Она окружена боковым
#   отражателем толщиной 1 м и торцевыми отражателями толщиной по 0,5 м."
#   -- core 11.8 m equivalent diameter and 7 m high, surrounded by a LATERAL
#   reflector 1 m thick and END reflectors 0.5 m thick each.  So:
#       NZ_ACTIVE = 28  (700 cm)            confirmed
#       NZ_REFL   = 2   (50 cm each end)    confirmed
#       NREF      = 4   (100 cm)            NREF = 2 IS WRONG
#   [D] says it twice: the graphite rods sit "в отверстия четырёх рядов
#   периферийных колонн (бокового отражателя)" -- four rows of peripheral
#   columns, which are the lateral reflector.
#
#   Three counts close against each other, from sources that were not used to
#   build this map:
#       [D]      graphite stack        2488 columns of 250 x 250 mm, rho 1.65
#       [D]      reflector cooling     156 channels
#       [BEH96]  radial reflector      444 pure graphite + 156 water-cooled
#       2488 - 1888 (this map)       =  600 reflector columns
#   and 444 + 156 = 600.  The outermost ring carries the 156 cooled channels,
#   so the reflector is TWO materials, not one.
#
#   Geometry to use when the reflector dataset lands: the stack is a cylinder
#   in the vault, so bound it by a circle rather than by dilating this map's
#   ragged outline.  R = 28.14 cells (704 cm) about the centroid gives 592
#   reflector columns and a 2480-column stack, matching [D]'s 2488 to 0.3 %;
#   dilating the outline by 4 rings instead gives 833, which is 39 % too many
#   because the corners grow faster than the vault allows.  That radius needs
#   the grid to grow from 52 x 52 to at least 58 x 58 (107 648 nodes against
#   86 528 -- about 2.6 s per DUAL 1 1 flux solve, still affordable).
#
#   TRAP, recorded because it nearly went in: [BEH96] and [ALX98] both say
#   "32 cm of axial graphite reflector above and below the core" in
#   RBMK-sounding language.  It is not this reactor.  Both sentences sit in
#   the CRITICAL FACILITY section -- an 18 x 18 array of graphite blocks 4.1 m
#   tall holding a 346 cm fuel column ([BEH96] II.A).  Unit 4 is 700 cm
#   active with 50 cm ends, per [D] above.

# DONJON mixtures.  Reflector mixtures come FIRST and the fuel LAST, which is
# upstream's convention (1Sap_vs_3Sap.x2m: RMIX 1 2 3, FMIX 4) and matters:
# MACINI: indexes the non-fuel macrolib by material number, so MACREF's NMIX is
# max(RMIX) and leaving a gap would leave that mixture undefined in it.
# USPLIT: additionally demands NREFL + NFUEL == the highest material index
# (USPLIT.f, "WRONG NUMBER OF REFLECTOR OR FUEL TYPES"), so the numbering has
# to close up when U4_REFL=0 drops the four rings rather than leaving a hole.
# 0 is void, outside the stack.
#
# The radial reflector is FOUR rings because _RCompo resolves the spectrum by
# depth.  Measured 2026-10-01: at core level that resolution is worth 3.9 pcm,
# so it is kept because it is free, not because it is needed.
M_WAT, M_ABS, M_DSP = 1, 2, 3            # the three CPS channel states
M_REFL = [4, 5, 6, 7] if WITH_REFL else []   # ring 1 at the core .. ring 4, cooled
M_FUEL = 4 + len(M_REFL)
# U4_XEBINS: how many fuel mixtures to split the fuel into, so that a
# PER-CHANNEL xenon field can be carried.  NCR:'s MICRO clause sets one
# concentration per MIX (NCRRGR.f:326 -> :919, CONC indexed by mixture, with no
# channel index on that path), so a field costs mixtures and not an axis.  The
# fuel mixtures are M_FUEL .. M_FUEL+XEBINS-1 and must leave no gap below them,
# because USPLIT.f:180 requires NREFL + NFUEL to equal the highest material
# index exactly.
XEBINS = int(os.environ.get("U4_XEBINS", "1"))
# U4_XEAX=1 makes the xenon field PER BUNDLE instead of per channel: each
# bundle's frozen power ratio is its channel's radial share times the MEASURED
# t = 0 axial shape (INSAG-7 Fig. II-9, sources/derived/insag7_fig_II9_axial.csv),
# so the field does not depend on the burnup profile it is used to separate
# from.  INSAG-7 p. 64 names "xenon poisoning higher in the central parts than
# at the edge of the core" as one cause of the double-humped field.
XEAX = os.environ.get("U4_XEAX", "0") != "0"
if XEBINS < 1:
    raise SystemExit("U4_XEBINS must be >= 1")
M_FUEL_HI = M_FUEL + XEBINS - 1
NMIX = M_FUEL_HI
fmixlist = " ".join(str(m) for m in range(M_FUEL, M_FUEL_HI + 1))
FUEL_TYPES = {"FUEL"}

# Which lattice positions hold what.  The rod classes differ in construction,
# not just in where they sit, so they are separated here rather than lumped.
ROD_DSP = {"RR", "AZ"}          # top-entry: 5 m absorber, 1.25 m water, 4.5 m displacer
ROD_BANK = {"AZOC"}             # same construction, driven separately by U4_TILT
ROD_ABS = {"AR"}                # top-entry, absorber only -- no graphite displacer
ROD_BOT = {"USP"}               # bottom-entry, 3.5 m absorber, no displacer
DET_TYPES = {"DKEV", "KD"}      # not CPS at all: water-filled tubes in graphite,
                                # modelled as the CPS water column (approximation)
CPS_TYPES = ROD_DSP | ROD_BANK | ROD_ABS | ROD_BOT | DET_TYPES

# U4_RODS: what the ROD_DSP channels hold, as a stack of (mixture, planes)
# read BOTTOM-UP over the 28 active planes.  Every other CPS position stays a
# water column in every variant, so a difference between two variants is the
# displacer and absorber alone.
#
# THE WITHDRAWN GEOMETRY IS SELF-CHECKING.  A6_CPS_PLAN gives the RR/AZ rod as
# 5 m absorber + 1.25 m water + 4.5 m displacer.  With the rod fully up the
# absorber sits above the core, so what is left in the channel is
# 1.25 m water, 4.5 m displacer, 1.25 m water -- and 1.25 + 4.50 + 1.25 is
# exactly the 7.00 m core height.  Three independently-quoted lengths filling
# the core exactly is a check on all three, and it is also the configuration
# the positive-scram mechanism needs: a water column at the BOTTOM, which the
# displacer sweeps out as the rod starts down.
#
# 'dsp' isolates that sweep: the displacer moves down 1.25 m and nothing else
# changes.  'scram1' is the same motion with the 1.25 m of absorber that
# really does enter the top at the same time, so the pair separates the
# displacer's contribution from the net first step.
RODS = os.environ.get("U4_RODS", "wat")
TILT = int(os.environ.get("U4_TILT", "0"))
_W, _D, _A = "W", "D", "A"
M_OF = {"W": M_WAT, "D": M_DSP, "A": M_ABS}

# The rod as built: absorber 5 m, water gap 1.25 m, graphite displacer 4.5 m,
# measured top-down, i.e. 20 + 5 + 18 = 43 planes of 25 cm.
N_ABS, N_GAP, N_DSP = 20, 5, 18
# USP is the shortened absorber that enters from BELOW and carries no
# displacer: 3.5 m, i.e. 14 planes (INSAG-7 Sec. 2.2, Fig. 1; A6_CPS_PLAN
# "Rod types"/"Axial design").  AR is top-entry absorber only, same 5 m
# absorber as RR/AZ but no graphite under it.
N_USP = 14


def stack(n):
    """What a ROD_DSP channel holds, plane by plane bottom-up over the active
    core, with the rod inserted n planes from fully withdrawn.

    Fully withdrawn puts the absorber above the core and leaves, bottom-up,
    1.25 m water / 4.5 m displacer / 1.25 m water -- and 1.25 + 4.50 + 1.25 is
    exactly the 7.00 m core.  Three independently-quoted lengths filling the
    core exactly is a check on all three, and it is the configuration the
    positive-scram mechanism needs: a water column at the BOTTOM that the
    displacer sweeps out as the rod starts down.

    Anything the rod does not occupy is coolant, so the fallback is water --
    both below the displacer's lower end and above the absorber's upper end.
    """
    d0, d1 = 1 + N_GAP - n, N_GAP + N_DSP - n          # displacer, bottom-up
    g0, g1 = d1 + 1, d1 + N_GAP                        # water gap above it
    a0, a1 = g1 + 1, g1 + N_ABS                        # absorber above that
    out = []
    for q in range(1, NZ_ACTIVE + 1):
        if a0 <= q <= a1:
            out.append(_A)
        elif d0 <= q <= d1:
            out.append(_D)
        else:
            out.append(_W)                             # gap, or beyond either end
    return out


def stack_abs(n):
    """An AR channel: 5 m of absorber entering from the TOP, no displacer.

    Fully withdrawn (n = 0) the absorber sits above the core and the channel is
    all water, so an AR rod contributes nothing until it is moved -- unlike
    RR/AZ, whose displacer is in the core even when the rod is up.  That
    difference is the whole reason the classes are kept apart.
    """
    hi = NZ_ACTIVE - n + N_ABS
    lo = NZ_ACTIVE - n + 1
    return [_A if lo <= q <= hi else _W for q in range(1, NZ_ACTIVE + 1)]


def stack_bot(n):
    """A USP channel: 3.5 m of absorber entering from BELOW, no displacer.

    Withdrawn means parked under the core, so again the channel is all water at
    n = 0.  Entering from below it suppresses the bottom of the flux, which is
    the opposite end from everything else in the CPS.
    """
    hi, lo = n, n - N_USP + 1
    return [_A if lo <= q <= hi else _W for q in range(1, NZ_ACTIVE + 1)]


NZ_TOT = NZ_ACTIVE + 2 * NZ_REFL


def col32(t, d):
    """The mixture in every one of the 32 planes of a CPS channel, from the
    rod's ABSOLUTE position at depth d -- the same geometry devices() hands to
    DEVINI: as MAXPOS and LEVEL, but arrived at by writing a MIX map instead.

    The two paths share only the lengths (N_ABS/N_GAP/N_DSP/N_USP) and the
    parked positions; everything after that is independent, which is what
    makes agreement between them a real check rather than a tautology.  The
    asserts below tie this to stack()/stack_abs()/stack_bot() over the active
    core, so the new path cannot drift from the one every A6d result used.
    """
    zlo = 0.0
    ztop = NZ_TOT * PITCH                       # 800
    zc_hi = (NZ_REFL + NZ_ACTIVE) * PITCH       # 750, absorber bottom parked
    dsp_top = zc_hi - N_GAP * PITCH             # 625, displacer top parked
    usp_top = NZ_REFL * PITCH                   # 50,  USP top parked
    out = []
    for k in range(1, NZ_TOT + 1):
        zc = (k - 0.5) * PITCH                  # plane centre
        m = _W
        if t in ROD_DSP or t in ROD_BANK or t in ROD_ABS:
            if zc_hi - d <= zc <= zc_hi - d + N_ABS * PITCH:
                m = _A
            elif (t not in ROD_ABS) and (
                    dsp_top - d - N_DSP * PITCH <= zc <= dsp_top - d):
                m = _D
        elif t in ROD_BOT:
            if usp_top + d - N_USP * PITCH <= zc <= usp_top + d:
                m = _A
        out.append(m)
    assert len(out) == NZ_TOT
    return out


# col32 must reproduce the three hand-derived stacks over the active core at
# every depth the 25 cm mesh allows, or it is not the same rod.
for _n in range(0, NZ_ACTIVE + 1):
    _d = _n * PITCH
    _act = slice(NZ_REFL, NZ_REFL + NZ_ACTIVE)
    assert col32("RR", _d)[_act] == stack(_n), ("RR", _n)
    assert col32("AR", _d)[_act] == stack_abs(_n), ("AR", _n)
    assert col32("USP", _d)[_act] == stack_bot(_n), ("USP", _n)


def runs(col):
    """A plane-by-plane column as (mixture, count) runs, for the deck header."""
    out = []
    for c in col:
        if out and out[-1][0] == c:
            out[-1][1] += 1
        else:
            out.append([c, 1])
    return [(c, n) for c, n in out]


# The hand-derived configurations, kept as names, and ASSERTED against stack()
# rather than trusted alongside it.  'wat' is not a rod state at all -- it is
# the water-everywhere reference the displacer's worth is measured from.
NAMED = {
    "out":    0,            # rods fully withdrawn
    "scram1": N_GAP,        # the real first 1.25 m of travel
    "in":     NZ_ACTIVE,    # rods fully in -- SEE THE CAVEAT
}
assert [c for c, _ in runs(stack(0))] == [_W, _D, _W]
assert [n for _, n in runs(stack(0))] == [N_GAP, N_DSP, N_GAP]
assert runs(stack(5)) == [(_D, 18), (_W, 5), (_A, 5)]
assert runs(stack(NZ_ACTIVE)) == [(_A, 20), (_W, 8)]

# Two half-steps of the sweep, which stack() cannot express because they move
# only one END of the displacer.  They decompose 'dsp': botD is graphite
# replacing water at the displacer's lower end, topW is water replacing
# graphite at its upper end, and the sweep is both at once.  Which one wins is
# decided by the axial flux shape, and that is the whole mechanism.
# 'dsp' is the gate's own test -- "inserting ONLY the displacer from below" --
# so the absorber is suppressed.  It is not a physical rod position; it is the
# isolation the gate asks for, and 'scram1' is the same motion with the
# absorber that really does enter the top at the same time.
HALVES = {
    "dsp":  [_D] * N_DSP + [_W] * (NZ_ACTIVE - N_DSP),
    "botD": [_D] * (N_GAP + N_DSP) + [_W] * N_GAP,
    "topW": [_W] * N_GAP + [_D] * (N_DSP - N_GAP) + [_W] * (2 * N_GAP),
}
assert all(len(v) == NZ_ACTIVE for v in HALVES.values())

# U4_RODS=insag drives every CPS channel to its OWN sourced depth instead of
# driving one bank uniformly.  The depths are in the channel map's depth_cm
# column, digitised from INSAG-7 Fig. II-6 at 01:22:30 and registered against
# Dollezhal Fig. 2.3 (PROGRESS.md "A6d"): 211 rods, 47 of them inserted,
# 4346 cm of total insertion.  Each class gets its own construction -- RR, AZ
# and AZOC carry the displacer, AR is absorber only, USP enters from below --
# because at this state the inserted rods are spread across all four.
INSAG_RODS = RODS == "insag"
CPS_RODS = ROD_DSP | ROD_BANK | ROD_ABS | ROD_BOT

# U4_RODDEPTH=<file> replaces the sourced depth_cm of the TOP-ENTRY rods with
# solved ones, keeping every rod's sourced TYPE and SITE.  The file holds one
# depth in cm per CPS row, in the channel map's row order, so it is checked for
# length and for leaving the non-solved classes alone before it is trusted --
# the same discipline U4_BURNMAP=file applies to the burnup histogram.  This is
# an inverse problem (tools/a6d_rods.py), not a sourced state: the target is
# [D]'s channel-power limit, and what is being asked is whether ANY pattern
# meets it, not which pattern history used.
RODDEPTH = os.environ.get("U4_RODDEPTH", "")
_RDMAP = {}
if RODDEPTH:
    if RODS != "insag" and not DEV:
        raise SystemExit("U4_RODDEPTH needs U4_RODS=insag (or U4_DEV=1) -- it "
                         "overrides that construction's depths and keeps its types")
    _rd = [float(x) for x in open(RODDEPTH).read().split()]
    _rrows = [r for r in csv.DictReader(open(MAP)) if r["type"] in CPS_RODS]
    if len(_rd) != len(_rrows):
        raise SystemExit(f"{RODDEPTH}: {len(_rd)} depths, {len(_rrows)} CPS rods")
    for _r, _d in zip(_rrows, _rd):
        if _d < 0.0 or _d > 700.0:
            raise SystemExit(f"{RODDEPTH}: depth {_d} outside the 0-700 cm travel")
        _RDMAP[(int(_r["i"]), int(_r["j"]))] = _d

def rod_depth_raw(r):
    """A CPS rod's depth in cm: the override file if one was given, else the
    sourced depth_cm column."""
    return float(_RDMAP.get((int(r["i"]), int(r["j"])), r["depth_cm"]) or 0)


def rod_depth(r):
    """The same depth quantised to the 25 cm axial mesh.  ONE definition,
    shared by insag_col(), the RODFULL map and devices(), because three copies
    of a rounding rule is three chances for the routes being compared to be
    describing different rods.  28 planes over the 700 cm travel means
    insertions of 20 and 30 cm round to one plane and to zero; that is a real
    loss of resolution, reported by the generator rather than hidden, and it is
    exactly what U4_DEVQ=0 lifts for the transient."""
    return round(rod_depth_raw(r) / PITCH) * PITCH


_COLCACHE = {}


def insag_col(r):
    """The axial column of one CPS channel at its own sourced depth."""
    _d = rod_depth(r)
    key = (r["type"], _d)
    if key not in _COLCACHE:
        # 28 planes over the 700 cm active height -> 25 cm a plane, so the
        # sourced depths quantise to the axial mesh.  Insertions of 20 and
        # 30 cm round to one plane and 0 respectively; that is a real loss of
        # resolution and is reported by the generator rather than hidden.
        n = int(round(_d / PITCH))
        t = r["type"]
        if t in ROD_DSP or t in ROD_BANK:
            col = stack(n)
        elif t in ROD_ABS:
            col = stack_abs(n)
        elif t in ROD_BOT:
            col = stack_bot(n)
        else:
            col = [_W] * NZ_ACTIVE
        _COLCACHE[key] = col
    return _COLCACHE[key]


if RODS == "wat" or INSAG_RODS:
    RODCOL = [_W] * NZ_ACTIVE
elif RODS in HALVES:
    RODCOL = HALVES[RODS]
elif RODS in NAMED:
    RODCOL = stack(NAMED[RODS])
elif RODS.startswith("d") and RODS[1:].isdigit():
    RODCOL = stack(int(RODS[1:]))
else:
    raise SystemExit(f"U4_RODS={RODS!r}: expected wat, insag, d<n>, or one of "
                     f"{sorted(set(NAMED) | set(HALVES))}")

# U4_TILT inserts the 36 AZOC channels n planes from the top, as their own
# bank.  It exists to tilt the axial flux downward, because the displacer
# sweep's SIGN depends on the tilt and nothing else in this deck provides one:
# the burnup is flat and there is no xenon.  A partially-inserted scram bank
# is a real configuration, but THIS pattern is not the 01:23 pattern and is
# not offered as one.
#
# CORRECTED 2026-10-04.  This used to read `stack(TILT) if TILT else [_W]*N`,
# which made the 36 AZOC channels PURE WATER whenever the tilt was off -- i.e.
# in every core run to date bar the tilt studies.  AZOC is the same hardware
# as RR/AZ (ROD_BANK above, and A6_CPS_PLAN "Rod types"), so a withdrawn AZOC
# channel contains its 4.5 m graphite displacer exactly as a withdrawn RR does.
# stack(0) IS the withdrawn configuration, so the special case was not a
# simplification, it was 36 missing displacers.  Found by comparing the
# uniform-bank deck against the per-rod INSAG-7 pattern, which builds every CPS
# channel from its own class and depth and so never had the hole.
BANKCOL = stack(TILT)
# ...EXCEPT under U4_DEV, where the devices supply every absorber and every
# displacer themselves and the base map must therefore hold NO rod material at
# all.  U4_RODS=wat is not that: it leaves RODCOL water but keeps BANKCOL at
# stack(0), so the 36 AZOC channels still carry their withdrawn displacer --
# correct for the base-map route and the whole point of the 2026-10-04 fix
# above, but a DOUBLE COUNT for the device route, which then adds its own
# (displacer - water) delta on top of a node that already holds the displacer.
# Measured before this guard existed: NTOT0 went 0.391106 + (-0.175640) =
# 0.215466 against a thermal SIGW00 of 0.390100, i.e. a NEGATIVE removal cross
# section, and TRIVAA: stopped with 'TRISYS: NEGATIVE XS IN GROUP 2'.
if DEV:
    BANKCOL = [_W] * NZ_ACTIVE
    if TILT:
        raise SystemExit("U4_DEV=1 and U4_TILT are two ways to say the same "
                         "thing; put the AZOC bank depth in the depth file")


# --- A7's thermal-hydraulic inputs.  Every one of these is either sourced or
# derived in A7a (PROGRESS.md "A7a"), and the derivations live in
# decks/Donjon/data/gen_rbmk_a7a.py so there is one copy of each.
KGF = 98066.5                   # Pa per kgf/cm2, exact
P_OUT = 75.3 * KGF              # [D] p.95 outlet pressure
T_IN = 265.0 + 273.15           # [D] p.95 inlet temperature
TH_PITCH = 1.7639E-2            # m, flow-area-matched CLUSTER pitch (A7a)
TH_NPIN = 18
R_PELLET, R_GAP, R_CLAD = 5.750E-3, 5.850E-3, 6.790E-3     # m, A6.1 cell
TH_HGAP = 2.80E+3               # W/m2/K: bare He conduction over the sourced
                                # 100 um gap, k/delta with k = 0.28 at 700 K.
                                # THM:'s own correlation implies a far tighter
                                # gap and lands 780 K low on [D]'s centreline.
V_REF, P_REF = 4.7713, 3100.0   # m/s at kW: THM:'s OWN inlet velocity for
                                # [D]'s 30 t/h at 3100 kW, measured in A7a, so
                                # no steam table of ours enters the scaling
PTOT_MW = 3200.0                # [D]: nominal thermal rating


def tsat_if97(p_pa):
    """Saturation temperature, K, from IAPWS-IF97 region 4 (the backward
    equation, eq. 31).  THM:'s steam tables are freesteam, which IS IF97, so
    this is THM:'s own saturation line and a subcooling quoted against it is
    the subcooling THM: sees.  Checked: 7.0 MPa -> 558.98 K (285.83 C)."""
    n = [0.11670521452767E4, -0.72421316703206E6, -0.17073846940092E2,
         0.12020824702470E5, -0.32325550322333E7, 0.14915108613530E2,
         -0.48232657361591E4, 0.40511340542057E6, -0.23855557567849,
         0.65017534844798E3]
    b = (p_pa / 1.0E6) ** 0.25
    e = b * b + n[2] * b + n[5]
    f = n[0] * b * b + n[3] * b + n[6]
    g = n[1] * b * b + n[4] * b + n[7]
    d = 2.0 * g / (-f - (f * f - 4.0 * e * g) ** 0.5)
    return (n[9] + d - ((n[9] + d) ** 2 - 4.0 * (n[8] + n[9] * d)) ** 0.5) / 2.0


assert abs(tsat_if97(7.0E6) - 558.98) < 0.01

# --- U4_TH=acc: the 01:23 thermal-hydraulic state instead of nominal.  All
# three numbers are INSAG-7 p. 64 (the Commission's initial condition "at
# 01:23"): power 200 MW(th); coolant flow 56 000 m3/h (eight MCPs instead of
# six, so ABOVE the full-power flow); subcooling at the core inlet 3 C, citing
# its ref. [28].  The pressure is NOT given for 01:23: the design outlet
# pressure above is kept and the inlet is placed 3 K below THM:'s own
# saturation at it, because the subcooling, not the absolute temperature, is
# what decides where boiling starts.  INSAG-7 p. 6 says "7 MPa"; 7.0 against
# 7.38 MPa moves T_sat by 3.6 K but the subcooling not at all.
# The flow is VOLUMETRIC, so the inlet velocity needs no density: 56 000 m3/h
# over 1661 fuel channels through A7a's 22.427 cm2 flow area.  All of it is
# taken through the fuel channels -- the CPS channels have their own circuit.
TH_STATE = os.environ.get("U4_TH", "nom")
if TH_STATE not in ("nom", "acc"):
    raise SystemExit(f"U4_TH={TH_STATE!r}: want nom or acc")
SUBC = float(os.environ.get("U4_SUBC", "3.0"))
A_FLOW_M2 = 22.427082E-4        # m2, gen_rbmk_a7a.py's A_FLOW
Q_ACC = 56000.0                 # m3/h, INSAG-7 p. 64
# U4_QFRAC scales that flow for the state at AZ-5 rather than at 01:23.  The
# 56 000 m3/h is the Commission's value immediately BEFORE the test (p. 64);
# INSAG-7 Sec. 1-4.6.2 (PDF p. 65): "Thirty-five seconds after the start of
# the transient it had fallen by 10-15% of the initial value" -- i.e. at
# 01:23:39, one second before EPS-5.  So 0.85-0.90 is a sourced band for the
# A8 initial state, not a fitted constant.  Power is kept at 200 MW: the same
# section says there was no power increase during the rundown.
QFRAC = float(os.environ.get("U4_QFRAC", "1.0"))
Q_ACC *= QFRAC
QNOTE = ("" if QFRAC == 1.0 else
         f"*  [U4_QFRAC={QFRAC:g}: 56000 m3/h x {QFRAC:g}, the flow at AZ-5 after the\n"
         f"*  10-15 % rundown fall of INSAG-7 Sec. 1-4.6.2.]\n")
# U4_PACC overrides the 200 MW only to measure the static power coefficient of
# the 01:23 state (flow and inlet held); it is not a state of the accident.
PACC = os.environ.get("U4_PACC", "200")
if TH_STATE == "acc":
    PTOT_MW = float(PACC)
    T_IN = tsat_if97(P_OUT) - SUBC
    V_ACC = Q_ACC / 3600.0 / 1661.0 / A_FLOW_M2
# THM:'s inner temperature tolerance, in K.  Upstream's value is 0.5.
# 0.05 was adopted on 2026-10-01 on the theory that the outer Picard test --
# a max over 46 508 bundles -- could not be tighter than what the inner solve
# guarantees per bundle.  The reasoning is sound and the conclusion was wrong:
# measured 2026-10-02, tightening it ten-fold changed neither the eigenvalue
# nor the residual plateau, because the plateau is a limit cycle (see the
# convergence block below) and not a tolerance floor.  It is kept because an
# inner solve should be tighter than anything the outer loop tests, not
# because it fixed anything.
ERMAXT = os.environ.get("U4_ERMAXT", "0.05")
ERMAXC_TR = os.environ.get("U4_ERMAXC", "1.0E-3")     # transient flow tolerance
CYCCAP = os.environ.get("U4_CYCCAP", "1.0E-2")       # limit-cycle cap, patch 0005
# THMTRS flow iterations (CONV's third integer, passed as MAXITC).  A channel
# on the limit cycle uses ALL of them before patch 0005 accepts it, so this
# is a cost knob: measured 2026-10-06, ~300 cycling channels a step cost
# ~40 s/step at 100.  Converging channels take < 10.
FLOWIT = os.environ.get("U4_FLOWIT", "30")
KINFB = os.environ.get("U4_KINFB", "1") != "0"
# Density under-relaxation in THMTRS's flow iteration, local patch 0006.
# Not a physics knob: it changes the path to the fixed point, not the point.
FRLX = os.environ.get("U4_FRLX", "1.0")
KINSHAPE = [float(x) for x in os.environ.get("U4_KINSHAPE", "").split(",") if x]
KINVOID = os.environ.get("U4_KINVOID", "0") != "0"
# THM: relaxes ALL FIVE local feedback fields with one factor (THM.f:1187,
# 1207-1245): FLOT = RELAX*new + (1-RELAX)*old.  So the residual THM reports
# is already scaled by it.  RELAX is a solver parameter, not a physical one,
# and the converged answer must not depend on it -- measured 2026-10-02 at
# 1.0, 0.5 and 0.2, keff came out bit-identical at 1.039735 all three times.
RELAX = os.environ.get("U4_RELAX", "0.5")

# [PAV] Table 1: the Unit 4 core as loaded on 26 April 1986 -- 1659 assemblies
# in eight burnup groups, averaging 10.9 MWd/kgU.  COUNTS AND VALUES ARE
# SOURCED; WHERE EACH GROUP SITS IS NOT.  [PAV] gives no spatial map and none
# has been found, so the placement is an explicit assumption and the point of
# U4_BURNMAP is to measure what that assumption is worth rather than to hide it.
PAV_BURNUP = [(721, 13.7), (392, 12.3), (154, 10.5), (101, 8.8),
              (35, 7.0), (43, 5.4), (41, 3.5), (172, 1.2)]
#   flat  every channel at the core average -- what everything before A6d used
#   rand  the histogram scattered at random (seeded, so the deck is reproducible)
#   cent  most-burnt fuel in the middle, freshest at the edge
#   edge  the reverse, freshest in the middle
#   ring  burnup rising monotonically with radius in bands -- the smooth version
BURNMAP = os.environ.get("U4_BURNMAP", "flat")
# U4_AXBURN redistributes each channel's burnup ALONG the channel, keeping
# the channel average exactly.  It exists because the axial flux shape decides
# the sign of the scram (gate A6.5; PROGRESS (24)) and the axial shape follows
# the axial burnup and xenon -- which INST-BVAL CHAN holds uniform.
# RESPAR.f:518-531 reads INST-BVAL BUND as one value per channel PER BUNDLE,
# bundle-major (IB outer, ICH inner), and RESPFM.f:65-72 counts IB upward in
# IZ over the fuel-bearing planes, so bundle 1 is the core BOTTOM (z 50-75 cm)
# and bundle 28 the top.
#
#   cos:<a>    1 + a*cos(pi*(z - mid)/H)  -- more burnup at mid-height, the
#              shape a channel accumulates under a centre-peaked flux
#   tilt:<t>   1 + t*(z - mid)/(H/2)      -- t > 0 burns the TOP harder
#   file:<p>   28 multipliers, bottom to top
#
# Every form is renormalised to a mean of exactly 1 over the 28 equal
# bundles.  THESE ARE SENSITIVITIES, NOT SOURCED PROFILES: no axial burnup
# map for Unit 4 has been found.  The sourced target is the axial FLUX
# shape, INSAG-7 Fig. II-9 at t = 0.
AXBURN = os.environ.get("U4_AXBURN", "")


def axial_shape():
    """The 28 per-bundle burnup multipliers, bottom to top, mean exactly 1."""
    import math
    if not AXBURN:
        return None
    kind, _, arg = AXBURN.partition(":")
    zc = [(k + 0.5) / NZ_ACTIVE for k in range(NZ_ACTIVE)]   # 0..1, bottom up
    if kind == "cos":
        f = [1.0 + float(arg) * math.cos(math.pi * (z - 0.5)) for z in zc]
    elif kind == "tilt":
        f = [1.0 + float(arg) * (z - 0.5) * 2.0 for z in zc]
    elif kind == "file":
        f = [float(x) for line in open(arg)
             for x in line.split("#", 1)[0].split()]
        if len(f) != NZ_ACTIVE:
            raise SystemExit(f"{arg}: {len(f)} values, want {NZ_ACTIVE}")
    else:
        raise SystemExit(f"U4_AXBURN={AXBURN!r}: want cos:<a>, tilt:<t> "
                         "or file:<path>")
    if min(f) <= 0.0:
        raise SystemExit(f"U4_AXBURN={AXBURN!r} makes a burnup <= 0")
    m = sum(f) / len(f)
    return [x / m for x in f]
BURNSEED = int(os.environ.get("U4_BURNSEED", "20260404"))

# XENON.  The COMPO's MICR list carries Xe135 and I135 (rbmk_a5b_compo.x2m:263),
# so their densities can be overridden per MIX at run time without a branch
# axis -- NCRLIB.f:45-48 takes the user value whenever it is not the '*'
# sentinel, and the ALL form keeps every other depleted isotope (NCRLIB.f:364
# shows ONLY would DISCARD the unlisted ones, which is not what is wanted).
#
#   stored   leave the depleted densities alone.  That is EQUILIBRIUM xenon at
#            the depletion power, 16.7 MW/t, not the 01:23 state.
#   none     Xe135 and I135 set to zero, so `stored` minus `none` measures what
#            the equilibrium xenon is worth in this core.
#   <value>  an explicit Xe135 density, for a level taken from the I/Xe solve
#            over INSAG-7's run-down.
#
# MICRO HAS TO COME LAST in the MIX clause: NCRRGR.f:316-335 reads
# isotope/value pairs until it sees ENDMIX, so anything after it is eaten.
XENON = os.environ.get("U4_XENON", "stored")


def burnup_list(cells, nx, ny):
    """Per-channel burnup in MWd/t, in channel order.

    `cells` is the list of (i, j) lattice positions in the order the fuel map
    numbers them.  The histogram holds 1659 assemblies and the sourced channel
    map holds 1661 fuel positions; INSAG-7 (pp. 67, 107) accounts for the
    difference with one extra absorber and one empty channel, so the two
    channels the histogram cannot fill are given the core average and that is
    stated rather than smeared.
    """
    import random
    pool = []
    for n, bu in PAV_BURNUP:
        pool.extend([bu * 1000.0] * n)          # MWd/kgU -> MWd/t
    mean = sum(pool) / len(pool)
    while len(pool) < len(cells):
        pool.append(mean)
    pool = pool[:len(cells)]

    if BURNMAP == "flat":
        return [10900.0] * len(cells), "every channel at the core average"
    if BURNMAP == "file":
        # A placement SOLVED FOR rather than assumed -- tools/a6d_place.py
        # writes this file.  The histogram is still [PAV]'s; only the pairing
        # of groups to channels is being determined, so the file is checked
        # against the pool as a multiset before it is trusted.
        src = os.environ.get("U4_BURNFILE", "")
        if not src:
            raise SystemExit("U4_BURNMAP=file needs U4_BURNFILE=<path>")
        got = [float(x) for x in open(src).read().split()]
        if len(got) != len(cells):
            raise SystemExit(f"{src}: {len(got)} values, {len(cells)} channels")
        # Compared as a sorted multiset with a tolerance, not for exact
        # equality: the file carries one decimal and the padding value is a
        # mean that does not round-trip.  0.1 MWd/t is far below anything that
        # matters and still catches a value that was invented rather than
        # moved.
        a, b = sorted(got), sorted(pool)
        if max(abs(x - y) for x, y in zip(a, b)) > 0.1:
            raise SystemExit(f"{src}: not a permutation of [PAV]'s histogram "
                             "-- the placement may be rearranged, not invented")
        return got, f"solved placement from {os.path.basename(src)}"
    cx, cy = (nx - 1) / 2.0, (ny - 1) / 2.0
    rad = {c: ((c[0] - cx) ** 2 + (c[1] - cy) ** 2) ** 0.5 for c in cells}
    if BURNMAP == "rand":
        rng = random.Random(BURNSEED)
        rng.shuffle(pool)
        order = list(cells)
        why = f"histogram scattered at random, seed {BURNSEED}"
    elif BURNMAP in ("cent", "ring"):
        order = sorted(cells, key=lambda c: rad[c])
        pool.sort(reverse=True)                 # most burnt nearest the centre
        why = "most-burnt fuel in the middle, freshest at the edge"
    elif BURNMAP == "chess":
        # Locally balanced: adjacent channels take opposite ends of the
        # distribution, so the burnup varies on the LATTICE scale rather than
        # the core scale.  The neutron migration length is comparable to the
        # 25 cm pitch, so the flux cannot resolve a channel-to-channel
        # alternation and sees something close to the mean -- which is what an
        # operator avoiding clustered fresh assemblies is really doing.
        rng = random.Random(BURNSEED)
        pool.sort()
        half = len(pool) // 2
        fresh, burnt = pool[:half], pool[half:]
        even = [c for c in cells if (c[0] + c[1]) % 2 == 0]
        odd = [c for c in cells if (c[0] + c[1]) % 2 == 1]
        # the halves and the parities are not exactly equal in size; put the
        # overflow wherever there is room rather than silently dropping it
        if len(even) > len(fresh):
            burnt, fresh = burnt[len(even) - len(fresh):], fresh + burnt[:len(even) - len(fresh)]
        elif len(odd) > len(burnt):
            fresh, burnt = fresh[len(odd) - len(burnt):], burnt + fresh[:len(odd) - len(burnt)]
        rng.shuffle(fresh); rng.shuffle(burnt)
        order = even + odd
        pool = fresh + burnt
        why = ("locally balanced -- fresh and burnt alternate between "
               "neighbouring channels")
    elif BURNMAP == "edge":
        order = sorted(cells, key=lambda c: rad[c])
        pool.sort()                             # freshest nearest the centre
        why = "freshest fuel in the middle, most-burnt at the edge"
    else:
        raise SystemExit(f"U4_BURNMAP={BURNMAP!r} is not one of "
                         "flat|rand|cent|edge|ring|chess|file")
    byc = dict(zip(order, pool))
    return [byc[c] for c in cells], why

DKTOL = os.environ.get("U4_DKTOL", "1.0E-6")
MAXIT = os.environ.get("U4_MAXIT", "40")
# U4_DCA: the coolant density fed to the fuel interpolation in the SINGLE-PASS
# deck.  It exists to price the COMPO's DCA axis ceiling: the axis is
# 0.72 0.60 0.45 0.30 0.15 0.05 0.02 g/cm3 (rbmk_a5b_compo.x2m:99) and 0.72 is
# its TOP, but THM: computes 0.778 g/cm3 at a 265 C channel inlet -- so the
# real unvoided state is off the end of the axis and A7 cannot interpolate it.
DCA_SET = os.environ.get("U4_DCA", "0.72")
# U4_VOIDFB=0 overrides the map's coolant density with DCA_SET inside the
# Picard loop, which switches the VOID feedback off and leaves the Doppler
# feedback live.  It exists only because the COMPO's DCA axis stops at 0.72
# while the real channel inlet is 0.778 g/cm3, so the fully-coupled loop
# cannot interpolate its own second iterate.  Measured cost of the override,
# applied core-wide: 103 pcm (dk/dDCA = -0.01779 from the 0.60 and 0.72 grid
# points, extrapolated 0.058 past the axis end) -- an UPPER bound, because
# only the subcooled lower part of each channel is above 0.72.
VOID_FB = os.environ.get("U4_VOIDFB", "1") != "0"


def xenon_bins(cells, nfuel):
    """Per-channel xenon bin index, and the Xe-135 density each bin carries.

    With one bin there is nothing to do and the deck keeps whatever U4_XENON
    asked for.  With several, the field comes from the I/Xe history solve run
    per channel at that channel's own power ratio -- tools/a6b_xenon.py, which
    is imported rather than copied so there is one set of physics.

    THE ASSUMPTION IS STATED IN THAT MODULE and bears repeating here: each
    channel is taken to hold its present power RATIO throughout the run-down,
    so only the global level moves.  The real 01:23 field is not that, because
    the shape itself reshaped -- which is exactly what INSAG-7 says the
    operators could not control, and what it records was never calculated.
    This measures a FROZEN-SHAPE field, which is a first estimate and a lower
    bound on the spread.

    Binning is equal-population on the density, each bin carrying its members'
    mean, so the within-bin error is as small as a given bin count allows.
    """
    if XEBINS == 1:
        return [0] * nfuel, [0.0], "one fuel mixture -- no xenon field"
    import sys as _sys
    _sys.path.insert(0, os.path.join(ROOT, "tools"))
    import a6b_xenon as _xe
    pw, psrc = chan_power()
    if len(pw) != nfuel:
        raise SystemExit(f"{len(pw)} channel powers, {nfuel} channels")
    mean = sum(pw) / len(pw)
    scales = [q / mean for q in pw]
    if XEAX:
        ax = measured_axial_t0()
        prod = [sc * a_ for sc in scales for a_ in ax]       # channel-major
        m_ = sum(prod) / len(prod)
        scales = [x / m_ for x in prod]
    # UNDER-RELAXATION, and it is not optional.  Rebuilding the field from the
    # latest power each pass diverges: measured 2026-10-05, the peak channel
    # went 5609 -> 4137 -> 5870 -> 4561 -> 6568 kW.  The loop gain exceeds one
    # because the field over-corrects a peaked power, the flattened power then
    # gives a flat field, and so on.  It is also not the physics -- xenon has a
    # 9.14 h time constant and cannot respond to a power it has just changed.
    # U4_XESTATE carries a running mean of the power ratios between passes, so
    # the sequence converges on the SELF-CONSISTENT field: the one the core
    # would settle into if 200 MW were held until xenon equilibrated with its
    # own shape.  That is a bounding question, not the 01:23 state, which
    # section (15) measures at 8 % of the way into that transition.
    st = os.environ.get("U4_XESTATE", "")
    w = float(os.environ.get("U4_XERELAX", "0.35"))
    if st and os.path.exists(st):
        old_s = [float(x) for x in open(st).read().split()]
        if len(old_s) == len(scales):
            scales = [(1.0 - w) * o + w * n for o, n in zip(old_s, scales)]
    if st:
        with open(st, "w") as f:
            f.write("\n".join(f"{x:.6f}" for x in scales))
    # the ODE is only ~25 distinct solves wide: Xe is smooth in the power
    # ratio, so solve on a grid spanning the real range and interpolate rather
    # than integrate 1661 times
    lo, hi = min(scales), max(scales)
    grid = [lo + (hi - lo) * j / 24.0 for j in range(25)]
    # WHICH FIELD.  U4_XEHIST=0123 (default) runs the sourced power history to
    # 01:23, which is the accident state.  U4_XEHIST=equil<f> instead takes the
    # equilibrium field for the core held at f x 3200 MW -- a bounding question,
    # and the only one relevant to a channel-power limit, which binds at full
    # power and not at 200 MW.  The two differ by more than their level: the
    # shape sensitivity dlnXe/dlns is 0.84 at 200 MW and 0.25 at 3200, because
    # burnout saturates the poison, so the equilibrium field is the weaker
    # flattener by ~3.4x.  See xenon_equilibrium() for the arithmetic.
    _hist = os.environ.get("U4_XEHIST", "0123")
    if _hist.startswith("equil"):
        _pf = float(_hist[5:] or "1.0")
        gval = [_xe.xenon_equilibrium(g, _pf) for g in grid]
    else:
        gval = [_xe.xenon_at_0123(g) for g in grid]

    def interp(x):
        if x <= grid[0]:
            return gval[0]
        for j in range(1, len(grid)):
            if x <= grid[j]:
                f = (x - grid[j - 1]) / (grid[j] - grid[j - 1])
                return gval[j - 1] + f * (gval[j] - gval[j - 1])
        return gval[-1]

    dens = [interp(x) for x in scales]
    nval = len(dens)                  # nfuel, or nfuel * NZ_ACTIVE with XEAX
    order = sorted(range(nval), key=lambda c: dens[c])
    xebin = [0] * nval
    vals = []
    for b in range(XEBINS):
        a = b * nval // XEBINS
        z = (b + 1) * nval // XEBINS
        members = order[a:z]
        for c in members:
            xebin[c] = b
        vals.append(sum(dens[c] for c in members) / len(members))
    if XEAX:                          # [channel][bundle from the bottom]
        xebin = [xebin[c * NZ_ACTIVE:(c + 1) * NZ_ACTIVE] for c in range(nfuel)]
    why = (f"{XEBINS} equal-population bins over a frozen-shape "
           f"{'per-bundle (measured t=0 axial shape) ' if XEAX else ''}field from "
           f"{os.path.basename(psrc)}; Xe spans "
           f"{min(dens) / _xe.XE_EQ:.3f} to {max(dens) / _xe.XE_EQ:.3f} "
           f"x equilibrium")
    return xebin, vals, why


def measured_axial_t0():
    """INSAG-7 Fig. II-9 at t = 0, linearly interpolated to the 28 bundle
    mid-planes (bottom first, as RESPFM.f numbers them), flat beyond the end
    markers, normalised to mean 1."""
    pts = []
    for line in open(os.path.join(ROOT, "sources", "derived", "insag7_fig_II9_axial.csv")):
        f = line.strip().split(",")
        if len(f) >= 4 and f[0] == "0":
            pts.append((float(f[2]), float(f[3])))
    pts.sort()
    out = []
    for kb in range(NZ_ACTIVE):                  # kb 0 = bottom bundle
        d = NZ_ACTIVE * PITCH - (kb + 0.5) * PITCH
        if d <= pts[0][0]:
            out.append(pts[0][1])
            continue
        if d >= pts[-1][0]:
            out.append(pts[-1][1])
            continue
        for (d0, v0), (d1, v1) in zip(pts, pts[1:]):
            if d0 <= d <= d1:
                out.append(v0 + (d - d0) / (d1 - d0) * (v1 - v0))
                break
    m = sum(out) / len(out)
    return [v / m for v in out]


def chan_power():
    """The 1661 channel powers in CHANNEL ORDER, from a previous run's
    POWER-CHAN dump.  Channel order is what RESPFM.f:74-82 finds and what
    THMINP reads a per-channel list in, so the flat block is the right one and
    FLPOW:'s radial-plane table is not."""
    import re as _re
    src = PCHAN or os.path.join(
        ROOT, "5.1", "Donjon", "Linux_aarch64",
        "rbmk_unit4_core_out.don.result")
    txt = open(src, "rb").read().decode("latin1").splitlines()
    for i, l in enumerate(txt):
        if "CONTENT OF BLOCK 'POWER-CHAN" not in l:
            continue
        v = []
        for q in txt[i + 1:]:
            if "CONTENT OF BLOCK" in q or "DRVUTL" in q or "LEAVING" in q:
                break
            v += [float(x) for x in q.split()
                  if _re.match(r"^[-+]?\d*\.?\d+E[-+]\d+$", x)]
        return v, src
    raise SystemExit(f"no POWER-CHAN block in {src}; run the core deck first")


def load():
    rows = list(csv.DictReader(open(MAP)))
    g = {(int(r["i"]), int(r["j"])): r for r in rows}
    ni = max(i for i, _ in g) + 1
    nj = max(j for _, j in g) + 1
    return g, ni, nj


def mesh(n):
    """MESHX/MESHY edges, cm, as a wrapped CLE-2000 list."""
    return fmt([f"{k * PITCH:.1f}" for k in range(n + 1)], 10)


def fmt(items, per, indent="    "):
    out, line = [], []
    for it in items:
        line.append(it)
        if len(line) == per:
            out.append(indent + " ".join(line))
            line = []
    if line:
        out.append(indent + " ".join(line))
    return "\n".join(out)


def wrap(cells, indent="  "):
    """CLE-2000 reads columns 1-120 only (clelog.c:31), and a 52-wide row of
    4-character fields is 208.  The reader is free-form, so a row may be split
    across lines; keep one core row per group of lines so the map stays legible."""
    per = max(1, (118 - len(indent)) // (len(cells[0]) + 1))
    out = []
    for k in range(0, len(cells), per):
        out.append(indent + " ".join(cells[k:k + per]))
    return "\n".join(out)


def rings(g, ni, nj):
    """Which reflector ring each non-channel stack position belongs to.

    The stack is a cylinder in the vault, so it is bounded by a circle rather
    than by dilating the core's ragged outline: R_STACK = 28.14 cells gives
    2480 columns against [D]'s 2488, while four rings of dilation give 2721,
    because the corners grow faster than the vault allows.

    Inside that circle, two different things decide the ring:

      * ring 4 is the stack's OUTER LAYER -- every column with a FACE
        neighbour outside the circle.  That is the cooled ring, and it is
        defined geometrically rather than by depth because the core outline
        is a staircase: dilating from it puts far too few columns in the
        outermost shell near the flats and far too many at the corners.
        THIS CLOSES A THIRD COUNT.  The layer comes out at exactly 156
        columns, and [BEH96] gives exactly 156 water-cooled reflector
        channels -- from a source that played no part in fixing R_STACK,
        which came from [D]'s 2488-column stack and 1 m lateral reflector.
        The remaining three rings total 436 against [BEH96]'s 444 pure
        graphite columns, the same 2 % the stack count is low by.
      * rings 1-3 are depth into the reflector, measured by dilation from the
        core.  Depth is the variable _RCompo resolves, because it is the
        spectrum that changes with it.

    Where the reflector is thinner than four columns the outer layer wins: a
    cooled column is cooled whatever its depth.
    """
    core = set(g)
    if not WITH_REFL:
        return {}, core
    ci = cj = (ni - 1) / 2.0
    stack = {(i, j) for i in range(-NPAD, ni + NPAD)
             for j in range(-NPAD, nj + NPAD)
             if math.hypot(i - ci, j - cj) <= R_STACK}
    # face neighbours, not the 8-neighbourhood: a diagonal step is 1.41 cells
    # and inflates both the skin (220 columns) and the corners of each shell.
    nbr = lambda i, j: [(i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)]
    skin = {q for q in stack - core if any(n not in stack for n in nbr(*q))}

    out, cur = {}, set(core)
    for step in range(1, NREF):           # depth 1 .. NREF-1
        new = {n for q in cur for n in nbr(*q)} - cur
        for q in new & stack:
            out[q] = step
        cur |= new
    for q in stack - core - set(out):     # deeper than NREF-1
        out[q] = NREF - 1
    out.update({q: NREF for q in skin})   # the cooled layer overrides depth
    return out, stack


def plane(g, ni, nj, k, cell, width=3):
    """One radial plane, as DONJON reads it: row j = nj-1 first (y decreasing)."""
    rows = []
    for j in range(nj + 2 * NPAD - 1, -1, -1):
        row = [f"{cell(i - NPAD, j - NPAD, k, g.get((i - NPAD, j - NPAD))):>{width}d}"
               for i in range(ni + 2 * NPAD)]
        rows.append(wrap(row))
    return "\n".join(rows)


def planes(g, ni, nj, nz, cell):
    """All nz PLANE blocks, with identical planes collapsed onto SAME.

    De-duplication is by CONTENT, not by a rule about which planes ought to
    match: the rod stacks make most active planes distinct, and a rule would
    have to be rewritten every time a stack changes.
    """
    out, seen = [], {}
    for k in range(1, nz + 1):
        body = plane(g, ni, nj, k, cell)
        if body in seen:
            out.append(f"PLANE {k} SAME {seen[body]}")
        else:
            seen[body] = k
            out.append(f"PLANE {k}\n{body}")
    return "\n".join(out), len(seen)


# ---------------------------------------------------------------- A8 devices
# Geometry of the rod as a DONJON ROD-DEVICE, derived from the SAME constants
# the base-map stacks are built from (N_ABS/N_GAP/N_DSP/N_USP) so the two
# routes cannot drift apart.
Z_LO = 0.0                                    # the mesh, not the core
Z_HI = (NZ_ACTIVE + 2 * NZ_REFL) * PITCH      # 800 cm
ZC_LO = NZ_REFL * PITCH                       # 50 cm, active core bottom
ZC_HI = (NZ_REFL + NZ_ACTIVE) * PITCH         # 750 cm, active core top
L_ABS, L_GAP, L_DSP, L_USP = (n * PITCH for n in (N_ABS, N_GAP, N_DSP, N_USP))
# The withdrawn displacer's top, two independent ways: down from the core top
# by the water gap, and up from the core bottom through gap + displacer.  Three
# separately-sourced lengths filling a separately-sourced core height exactly
# is the same check stack() makes, restated here because the device route needs
# the ABSOLUTE coordinates rather than a plane count.
assert abs((ZC_HI - L_GAP) - (ZC_LO + L_GAP + L_DSP)) < 1.0E-9
DSP_TOP0 = ZC_HI - L_GAP                      # 625 cm, displacer top, rod up
ABS_BOT0 = ZC_HI                              # 750 cm, absorber bottom, rod up
USP_TOP0 = ZC_LO                              # 50 cm, USP absorber top, rod down


# LEVEL is a FRACTION, not a depth (DEVGET.f:79-80 rejects anything outside
# [0,1]).  DEVGET.f:216-223 fixes what it means, and the two forms differ:
#
#   FROM H+ : DELH = LIMIT(2) - LEVEL*(LIMIT(2) - LENG(1))   -- DELH is the
#             rod's BOTTOM, and MOVCHK stacks the parts upward from it
#   FROM H- : DELH = LEVEL*(LENG(2) - LIMIT(1)) + LIMIT(1)   -- DELH is the
#             rod's TOP, and MOVCHK stacks the parts downward from it
#
# and in both cases DELH is CLAMPED to the mesh.  That clamp is why each part
# is declared from the end it never leaves through: an absorber declared H+
# clamps at the bottom, which it never reaches (its deepest bottom is the core
# bottom at 50 cm), while a displacer declared H+ would clamp the moment it
# started leaving through the bottom and simply stop, 525 cm short.  Declaring
# the displacer H- puts its clamp at the TOP, which it never reaches, and lets
# it slide out of the bottom correctly.  This is a parameterisation of one
# rigid rod by two devices, not a claim that the displacer enters from below.
def lev_abs(d):
    """Top-entry absorber: LEVEL such that the absorber's bottom is at
    ABS_BOT0 - d.  With MAXPOS z = [0, L_ABS], LENG(1) = 0."""
    return (Z_HI - (ABS_BOT0 - d)) / (Z_HI - Z_LO)


def lev_dsp(d):
    """Displacer: LEVEL such that its top is at DSP_TOP0 - d.  With
    MAXPOS z = [Z_HI - L_DSP, Z_HI], LENG(2) = Z_HI.  Clamped at 0, which is
    the displacer fully out of the bottom (reached at d = 625 cm, inside the
    700 cm travel) -- NEWMDV.f:92 then skips the device entirely, which is
    exactly right because it occupies no node."""
    return max(0.0, (DSP_TOP0 - d) / (Z_HI - Z_LO))


def lev_usp(d):
    """USP: a bottom-entry absorber whose top is at USP_TOP0 + d.  Genuinely
    FROM H-, unlike the displacer."""
    return (USP_TOP0 + d) / (Z_HI - Z_LO)


def devices(g, nx, ny):
    """The DEVINI: block for every CPS rod, and the group lists.

    Two devices per RR/AZ/AZOC rod (absorber + displacer) and one for each AR
    and USP.  Not one three-part rod, because the real rod is
    5.00 + 1.25 + 4.50 = 10.75 m and DEVGET.f:119-133 rejects any MAXPOS
    coordinate outside the 8 m mesh.  Splitting it also sidesteps a known bug:
    MOVDEV: stores ROD-POS as 6 reals (MOVPOS.f:159) where DEVGET: stored
    6*NPART (DEVGET.f:246), so it silently truncates a multi-part rod to its
    first part -- harmless here only because every device has NPART = 1.
    """
    rods, blocks = [], []
    grp = {1: [], 2: [], 3: []}
    for r in (x for x in csv.DictReader(open(MAP)) if x["type"] in CPS_RODS):
        i, j, t = int(r["i"]), int(r["j"]), r["type"]
        d = rod_depth_raw(r)
        if DEVQ:
            # the base map can only place a rod on a 25 cm plane boundary
            # (insag_col rounds the depth to one), so the comparison between the
            # two routes has to ask them the same question.  Off by default is
            # NOT available for the static gate and IS the point for A8.
            d = rod_depth(r)
        if d < 0.0 or d > NZ_ACTIVE * PITCH:
            raise SystemExit(f"rod at ({i},{j}): depth {d} outside the travel")
        I, J = i + NPAD, j + NPAD
        x0, x1 = I * PITCH, (I + 1) * PITCH
        # GEOMIX.f:212-222 reads the MIX rows with IY = 1 FIRST, and MESHY(1)
        # is the lowest y -- but plane() writes the highest map j first, so the
        # map's j axis is MIRRORED onto DONJON's y.  Harmless for the geometry
        # (a mirrored core is the same reactor, and NXNAME/NYNAME are written in
        # the same order so RESINI's printed cartogram stays self-consistent),
        # but the devices are the first thing in this deck that needs an
        # ABSOLUTE y coordinate, so the mirror has to be undone here.
        iy = ny - J                                  # 1-based DONJON row
        y0, y1 = (iy - 1) * PITCH, iy * PITCH
        parts = []
        if t in ROD_DSP or t in ROD_BANK:
            parts.append(("A", "H+", Z_LO, Z_LO + L_ABS, M_ABS, lev_abs(d), 1))
            parts.append(("D", "H-", Z_HI - L_DSP, Z_HI, M_DSP, lev_dsp(d), 2))
        elif t in ROD_ABS:
            parts.append(("A", "H+", Z_LO, Z_LO + L_ABS, M_ABS, lev_abs(d), 1))
        elif t in ROD_BOT:
            parts.append(("A", "H-", Z_HI - L_USP, Z_HI, M_ABS, lev_usp(d), 3))
        else:
            raise SystemExit(f"rod at ({i},{j}): unhandled CPS type {t}")
        # apply the per-group static advance, by recomputing the LEVEL at the
        # advanced depth rather than by nudging the LEVEL, so the two routes
        # (advance here vs. a depth file) cannot disagree
        if any(_ADV):
            parts = [(tg, fr, z0, z1, mx,
                      {1: lev_abs, 2: lev_dsp, 3: lev_usp}[g](
                          min(NZ_ACTIVE * PITCH, d + _ADV[g - 1])), g)
                     for tg, fr, z0, z1, mx, lv, g in parts]
        for tag, frm, z0, z1, mix, lev, gid in parts:
            rid = len(rods) + 1
            rods.append((rid, t, i, j, d, tag, lev))
            grp[gid].append(rid)
            blocks.append(
                f"ROD {rid}\n"
                f"  ROD-NAME {t}{tag}{len(rods):04d}\n"
                f"  AXIS Z FROM {frm}\n"
                f"  LEVEL {lev:.6f}\n"
                f"  MAXPOS {x0:9.3f} {x1:9.3f} {y0:9.3f} {y1:9.3f}"
                f" {z0:9.3f} {z1:9.3f}\n"
                # DMIX mix1 mix2: mix1 is the PERTURBED state and mix2 the
                # REFERENCE (SectDEVINI).  NEWMXS.f:61 then does
                # sigma(node) += XFAC*VF*(sigma(mix1) - sigma(mix2)), so with
                # the node already holding M_WAT, VF = 1 and XFAC = 1 this
                # lands exactly on sigma(mix1) -- which is what makes the
                # device route reproduce the base map rather than approximate
                # it.  XFAC DEFAULTS TO 2.0 and must be set.
                f"  DMIX {mix} {M_WAT}\n"
                "ENDROD")
    gtext = "\n".join(
        f"GROUP-ID {k} ROD-ID\n" + wrap([f"{n:4d}" for n in v], "  ")
        for k, v in sorted(grp.items()) if v)
    return rods, "\n".join(blocks), gtext, {k: len(v) for k, v in grp.items()}


def main():
    g, ni, nj = load()
    ring, stack = rings(g, ni, nj)
    nx, ny = ni + 2 * NPAD, nj + 2 * NPAD
    nz = NZ_ACTIVE + 2 * NZ_REFL
    nel = nx * ny * nz

    # the axial mixture a ROD_DSP channel holds, plane by plane (1-based k over
    # the whole 32-plane stack; the active region is NZ_REFL+1 .. NZ_REFL+28)

    def core_mix(i, j, k, r):
        """Mixture at column (i, j) in plane k (1-based)."""
        if r is None:
            ring_k = ring.get((i, j))
            return M_REFL[ring_k - 1] if ring_k else 0
        active = NZ_REFL < k <= NZ_REFL + NZ_ACTIVE
        if RODFULL and r["type"] in CPS_RODS:
            return M_OF[col32(r["type"], rod_depth(r))[k - 1]]
        if not active:
            # Above and below the core the graphite columns continue unchanged,
            # but every channel loses its fuel and becomes a coolant tube in
            # graphite, which is what the CPS water column already is.  An
            # approximation: the real end region holds the Zr/steel transition
            # piece.  Rods are not tracked outside the active core.
            return M_WAT
        if r["type"] in FUEL_TYPES:
            return M_FUEL + xbin(num[(i + NPAD, j + NPAD)] - 1, k)
        if INSAG_RODS and r["type"] in CPS_RODS:
            return M_OF[insag_col(r)[k - NZ_REFL - 1]]
        if r["type"] in ROD_DSP:
            return M_OF[RODCOL[k - NZ_REFL - 1]]
        if r["type"] in ROD_BANK:
            return M_OF[BANKCOL[k - NZ_REFL - 1]]
        return M_WAT

    def fmap_mix(i, j, k, r):
        active = NZ_REFL < k <= NZ_REFL + NZ_ACTIVE
        return (M_FUEL + xbin(num[(i + NPAD, j + NPAD)] - 1, k)
                if (active and r is not None
                    and r["type"] in FUEL_TYPES) else 0)

    # the fuel map numbers only the fuel channels, 1..NCOMB, in the same raster
    # order the B-ZONE block is written in
    nfuel = 0
    num = {}
    cells = []
    for j in range(ny - 1, -1, -1):
        for i in range(nx):
            r = g.get((i - NPAD, j - NPAD))
            if r is not None and r["type"] in FUEL_TYPES:
                nfuel += 1
                num[(i, j)] = nfuel
                cells.append((i, j))
    bulist, buwhy = burnup_list(cells, nx, ny)
    assert len(bulist) == nfuel
    xebin, xeval, xewhy = xenon_bins(cells, nfuel)
    assert len(xebin) == nfuel and len(xeval) == XEBINS

    def xbin(c, k):
        """Xenon bin of fuel channel c (0-based) in plane k (1-based)."""
        if XEAX:
            return xebin[c][k - NZ_REFL - 1]
        return xebin[c]

    _axf = axial_shape()
    if _axf is not None:
        # bundle-major, IB = 1 (bottom) .. 28 (top) outer, channels inner in
        # B-ZONE order -- RESPAR.f:518-531
        _vals = [f"{b * f:8.1f}" for f in _axf for b in bulist]
        assert len(_vals) == NZ_ACTIVE * nfuel
        _chk = [sum(bulist[c] * _axf[k] for k in range(NZ_ACTIVE)) / NZ_ACTIVE
                for c in range(nfuel)]
        assert max(abs(a - b) for a, b in zip(_chk, bulist)) < 1e-6
        _axlabel = (AXBURN if not AXBURN.startswith("file:")
                    else "file:" + os.path.basename(AXBURN[5:]))
        INSTB = (
            # a file: path can be long enough to break the 120-column limit;
            # its basename identifies it and the multipliers are printed below
            f"*  PER-BUNDLE BURNUP (U4_AXBURN={_axlabel}): each channel's burnup\n"
            "*  redistributed along the channel with its average kept exactly.\n"
            "*  A SENSITIVITY, not a sourced profile.  Multipliers bottom to top:\n"
            + "".join("*   " + " ".join(f"{x:.3f}" for x in _axf[i:i + 14]) + "\n"
                      for i in range(0, NZ_ACTIVE, 14))
            + "  INST-BVAL BUND\n" + wrap(_vals, "    "))
    elif BURNMAP == "flat":
        INSTB = "  INST-BVAL SAME 10900.0"
    else:
        # fixed field width: wrap() sizes its rows from the FIRST element,
        # so a list mixing "1200.0" with "13700.0" overruns 120 columns
        # whenever the first value happens to be a short one.
        _bu = wrap([f"{b:8.1f}" for b in bulist], "    ")
        INSTB = (
            "*  PER-CHANNEL BURNUP, in the same channel order as B-ZONE.\n"
            f"*  [PAV] Table 1's eight groups over 1659 assemblies, placed by\n"
            f"*  U4_BURNMAP={BURNMAP}: {buwhy}.\n"
            "*  The counts and the values are sourced; the PLACEMENT is not, and no\n"
            "*  spatial map has been found, so it is an assumption whose worth is\n"
            "*  measured by running the variants rather than argued.\n"
            f"*  mean {sum(bulist)/len(bulist):.0f} MWd/t, range {min(bulist):.0f}"
            f" to {max(bulist):.0f}.\n"
            "  INST-BVAL CHAN\n" + _bu)

    mixmap, ndistinct = planes(g, ni, nj, nz, core_mix)
    fmapmap, _ = planes(g, ni, nj, nz, fmap_mix)
    # B-ZONE is NOT an nx-by-ny map: RESDRV.f:347-356 reads exactly NCH integers,
    # one per fuel channel, in the order RESPFM.f:74-82 finds them -- ascending
    # flat radial index over the map, which is the order the MIX planes above are
    # written in, and therefore the order `num` was assigned in.  Each channel is
    # its own combustion zone, so the list is 1..NCOMB; it is laid out in the
    # shape of the core only to stay readable and checkable against the cartogram.
    bz = []
    for j in range(ny - 1, -1, -1):
        row = [f"{num[(i, j)]:>4d}" for i in range(nx) if (i, j) in num]
        if row:
            bz.append(wrap(row))
    bzone = "\n".join(bz)
    assert sum(len(r.split()) for r in bz) == nfuel

    # the cartogram's own labels, so the printed fuel map can be read against it
    ci = {int(r["i"]): r["col"] for r in g.values()}
    rj = {int(r["j"]): r["row"] for r in g.values()}
    lab = lambda v: f"'{v}'".ljust(5)      # uniform width keeps wrap() honest
    nxname = "\n".join(wrap([lab(ci.get(i - NPAD, "-")) for i in range(nx)],
                            indent="         ").splitlines()).lstrip()
    nyname = "\n".join(wrap([lab(rj.get(j - NPAD, "-")) for j in range(ny - 1, -1, -1)],
                            indent="         ").splitlines()).lstrip()

    zedges = [f"{k * PITCH:.1f}" for k in range(nz + 1)]
    ncps = sum(1 for r in g.values() if r["type"] in CPS_TYPES)
    assert nfuel + ncps == len(g), f"{nfuel} + {ncps} != {len(g)}"
    assert nfuel == 1661, nfuel

    if DEV and RODS != "wat":
        raise SystemExit("U4_DEV=1 needs U4_RODS=wat: the devices ARE the rods, "
                         "and DMIX's reference mixture is the water column the "
                         "base map must therefore hold")
    devrods, devblk, devgrp, devn = (devices(g, nx, ny) if DEV
                                     else ([], "", "", {}))
    # NEWMAC: rebuilds the macrolib with each device's delta sigmas folded in,
    # so it has to run AFTER MACINI: (which sizes the extended macrolib from
    # MATEX, one mixture per region -- MACCRE.f's own words) and BEFORE
    # TRIVAA:.  DEVINI: must in turn run before MACINI:, because it APPENDS
    # 2*NPART mixtures per device to MATEX and NEWMAC.f:130-133 aborts if the
    # macrolib and MATEX disagree on the count.
    macsys = "MACRD" if DEV else "MACRO"
    macrd = " MACRD" if DEV else ""
    newmac = ("" if not DEV else
              "MACRD MATEX := NEWMAC: MATEX MACRO DEVICE :: EDIT 0 XFAC 1.0 ;\n")
    newmac_i = "" if not DEV else "  " + newmac
    # TRIVAA: must build the unitary weighting matrix for anything feeding
    # INIKIN:/KINSOL: -- TRIVAA.f:174 -- and it only adds that matrix, so the
    # same SYSTEM still serves FLUD:.
    tvopt = " UNIT" if KIN else ""
    # U4_PBUND=1 prints POWER-BUND (NCH*NB, FLPDRV.f:209) so the AXIAL power
    # shape can be read back; tools/a8_axial.py sums it plane by plane.
    # U4_THDUMP=1 prints every channel's converged axial profiles (void
    # fraction, flow quality, density, power) for tools/a8_thcheck.py: the
    # check that the steam is where the sources put it, not just how much.
    thdump = ("" if os.environ.get("U4_THDUMP", "0") == "0" else f"""
INTEGER ich := 0 ;
WHILE ich {nfuel} < DO
  EVALUATE ich := ich 1 + ;
  ECHO "THDUMP" ich ;
  UTL: THER :: STEP UP 'HISTORY-DATA' STEP UP 'TIMESTEP0000'
               STEP UP 'CHANNEL' STEP AT <<ich>>
    IMPR EPSILON * IMPR XFL * IMPR DENSITY * IMPR POWER * IMPR ENTHALPY * ;
ENDWHILE ;""")
    pbund = ("" if os.environ.get("U4_PBUND", "0") == "0" else
             "\nUTL: POWER :: IMPR POWER-BUND * ;")
    # group 2 is the displacers, declared FROM H-, so INSERTING the rod is EXTR
    # for them; MOVDIR flips every sense at once.
    _sense = {1: ("INSR", "EXTR", "INSR"), -1: ("EXTR", "INSR", "EXTR")}[MOVDIR]
    _glines = "\n".join(f"    GROUP {g} {_sense[g - 1]} SPEED {VROD:.4f}"
                         for g in (1, 2, 3) if str(g) in MOVGRP)
    if not _glines:
        raise SystemExit(f"U4_MOVGRP={MOVGRP!r} selects no group")
    _mv = "" if not VROD else f"""  DEVICE := MOVDEV: DEVICE :: EDIT 0 DELT <<dt>>
*   The absorbers insert; the displacers FOLLOW THEM DOWN, which is EXTR
*   because they are declared FROM H- (see devices()); the bottom-entry USP
*   absorbers insert upward.  One statement per group, each rod moving from
*   its own 01:22:30 depth at the same sourced speed.
{_glines} ;
"""
    _lamd = lambda_d() if KIN else []
    kin_block = "" if not KIN else f"""
*==============================================================
*  A8: THE TRANSIENT
*
*  {KIN} steps of {KINDT:g} s = {KIN * KINDT:g} s.
*  {f"Rods at {VROD:g} cm/s = {VROD / 100.0:g} m/s, which is SOURCED: INSAG-7 p. 103" if VROD else "NO ROD MOVES (U4_VROD=0): this is the null transient."}
*  {"gives the EPS insertion speed." if VROD else ""}
*
*  NO BETA/LAMBDA/CHID IS GIVEN: the macrolib carries NDEL=6 with
*  per-precursor NUSIGF01..06 and CHI01..06 from the COMPO, and KINRD1.f
*  reads BETA-D/LAMBDA-D from there when the keywords are absent.  That keeps
*  A5b's measured beta as a burnup-dependent field; passing BETA would flatten
*  it to one scalar everywhere (KINXSD.f:131).
*
*  NEWMAC: is re-run every step because the device positions moved, which is
*  what its own documentation requires, and TRIVAA: is re-assembled and
*  re-factored every step because the cross sections changed.  Phase 0
*  measured that cost: 0.430 s/step with the macrolib moving.
*
*  {'THE CHECK: no rod moves, so the power MUST hold constant.  Drift means the' if not VROD else 'The power is reported, not asserted: what it does is the result.'}
*  {'kinetics assembly is wrong, not that the reactor did something.' if not VROD else ''}
*==============================================================
KINET := INIKIN: {macsys} TRACK SYSTEM FLUX ::
  EDIT 1
  NDEL {len(_lamd)}
*  LAMBDA, read out of the COMPO by lambda_d() -- see it for WHY this has to
*  be given at all (NCRMAC: stores NDEL values, MACINI: only forwards
*  NDEL*NF of them, and NF is 18 here).  Half-lives {" ".join("%.1f" % (0.693147 / x) for x in _lamd)} s.
*  BETA and CHID are deliberately absent so the macrolib's own per-precursor
*  NUSIGF01..06 / CHI01..06 are used instead of one scalar beta.
  LAMBDA {" ".join("%.6E" % x for x in _lamd)}
  NORM POWER-INI {PTOT_MW:.1f}
;

REAL dt pw pw0 tt := {KINDT:.6E} 0.0 0.0 0.0 ;
INTEGER istep := 0 ;@@KIN_DECL@@
GREP: KINET :: GETVAL E-POW 1 >>pw0<< ;
ECHO "A8INIT POWER" pw0 ;

REPEAT
  EVALUATE istep := istep 1 + ;
@@KIN_T0@@  EVALUATE tt := tt dt + ;
{_mv}  MACRD SYSTEM := DELETE: MACRD SYSTEM ;
@@KIN_NCR@@  MACRD MATEX := NEWMAC: MATEX MACRO DEVICE :: EDIT 0 XFAC 1.0 ;
  SYSTEM := TRIVAA: MACRD TRACK :: EDIT 0 UNIT ;
  KINET := KINSOL: KINET MACRD TRACK SYSTEM ::
    EDIT 0 DELTA <<dt>> SCHEME FLUX THETA 0.8 PREC THETA 0.8 ;
  GREP: KINET :: GETVAL E-POW 1 >>pw<< ;
  ECHO "A8STEP" istep "T" tt "POWER" pw "P/P0" pw pw0 / ;@@KIN_THM@@
UNTIL istep {KIN} >= ;

ECHO "A8DONE steps {KIN} dt {KINDT:g} vrod {VROD:g} power-ini" pw0 "power-fin" pw ;

*--- THE STATIC EIGENVALUE OF THE FINAL ROD GEOMETRY.
*    MOVDEV: advances each device's own LEVEL step by step, and nothing in the
*    transient trace says whether it put the rods where the elapsed time and
*    the speed imply.  Solving the final macrolib statically does: k here must
*    equal a static deck built with every depth advanced by vrod * nstep * dt,
*    and the reactivity 1 - k0/k must match what the power trace implies.
*    SYSTEM carries TRIVAA:'s unitary weighting matrix, which FLUD: ignores.
FLUX := DELETE: FLUX ;
FLUX := FLUD: SYSTEM TRACK :: EDIT 0 ADI 2 EXTE 300 1.0E-6 ;
GREP: FLUX :: GETVAL 'K-EFFECTIVE' 1 >>keff<< ;
ECHO "A8KFINAL travel-cm" {VROD * KIN * KINDT:.4f} "keff" keff ;
"""
    dev_block = "" if not DEV else f"""*--- A8: the {len(devrods)} rod-devices.  THIS MUST PRECEDE RESINI:.
*    DEVINI: appends its device mixtures to MATEX's MAT-INIT (DEVDRV.f:143),
*    while RESINI: builds the MAT record from MAT-INIT at whatever length it
*    has when RESINI: runs (RESIND.f:118-126) -- and the fuel-map form of
*    MACINI: reads MAT, not MAT-INIT (MACINI.f:202).  With DEVINI: after
*    RESINI:, MAT is 778 entries short, every device mixture is read as a
*    virtual region, and MACCRE: then packs the macrolib at a stride 778
*    smaller than the NMIX every reader indexes it by: the device cross
*    sections come out ZERO and the fission records come out MIS-STRIDED.
*    Nothing aborts.  The bundled Example1.x2m has the order right; this deck
*    did not, and the NBFIS guard in our NEWMAC: patch is what caught it.  Each RR/AZ/AZOC rod is TWO devices,
*    its absorber and its displacer, because the real rod is 10.75 m and
*    DEVGET.f:119-133 rejects a MAXPOS outside the 8 m mesh; see devices().
*    MOVE, not the default FADE: a fading rod scales its delta sigmas in place
*    instead of moving, which is not what a scram does.
DEVICE MATEX := DEVINI: MATEX :: EDIT 0 NUM-ROD {len(devrods)} MOVE
{devblk}
*--- groups, so MOVDEV: can scram the whole core in three statements: the
*    {devn.get(1, 0)} top-entry absorbers insert, the {devn.get(2, 0)} displacers follow them down
*    (declared FROM H-, so EXTR is what moves them downward), and the
*    {devn.get(3, 0)} bottom-entry USP absorbers insert upward.
CREATE ROD-GR {len([k for k, v in devn.items() if v])}
{devgrp}
;

"""

    nrefl_col = len(ring)
    ncol = len(stack)
    per_ring = [sum(1 for v in ring.values() if v == k + 1) for k in range(NREF)]
    # [D]: the graphite stack is 2488 columns.  This is a geometric consequence
    # of R_STACK, not a tuned number -- the radius came from [D]'s 1 m lateral
    # reflector, and the count is the check on it.
    if WITH_REFL:
        assert abs(ncol - 2488) / 2488 < 0.01, \
            f"{ncol} columns against [D]'s 2488"

    nring = len(M_REFL)
    nrod = sum(1 for r in g.values() if r["type"] in ROD_DSP)
    nar = sum(1 for r in g.values() if r["type"] in ROD_ABS)
    nusp = sum(1 for r in g.values() if r["type"] in ROD_BOT)
    ndet = sum(1 for r in g.values() if r["type"] in DET_TYPES)
    stackline = " ".join(f"{m}x{n}" for m, n in runs(RODCOL))
    bankline = " ".join(f"{m}x{n}" for m, n in runs(BANKCOL))
    nbank = sum(1 for r in g.values() if r["type"] in ROD_BANK)
    tag = (("UNIT4" if WITH_REFL else "U4NOREF")
           + ("" if RODS == "wat" else "_" + RODS.upper())
           + ("" if not TILT else f"_T{TILT}")
           + ("" if DCA_SET == "0.72" else f"_D{DCA_SET.replace('.','')}"))[:12]
    stem = os.path.basename(OUT)[:-4]
    rcpo_arg = " RCpo" if WITH_REFL else ""
    rcpo_seq = ("\nSEQ_ASCII   _RCompo    :: FILE './_RCompo' ;"
                if WITH_REFL else "")
    rcpo_asg = "\nRCpo := _RCompo ;" if WITH_REFL else ""
    # ---------------------------------------------------------------- A7
    # BURNUP is a GLOBAL value while the map is flat, and read PER BUNDLE out of
    # the map once it is not.  NCRRGR.f:203-217 takes the burnup's PARKEY as the
    # token straight after the directory name, and INST-BURN inside the MIX
    # clause (NCRRGR.f:651 -> IBTYP=2, used at :804) makes it read BRN0 per
    # bundle -- which is exactly what RESINI's INST-BVAL CHAN wrote.  Without
    # the PARKEY the keyword has nothing to bind to; without INST-BURN the
    # per-channel values sit in the map and are silently ignored.
    _perb = BURNMAP != "flat" or bool(AXBURN)
    _bkey = " 'burnup'" if _perb else ""
    _bmix = "INST-BURN" if _perb else "SET 'burnup' 10900.0"
    if XENON == "stored":
        _xe = ""
    elif XENON == "none":
        _xe = "\n               MICRO ALL Xe135 0.0 I135 0.0"
    else:
        # Only Xe135 is overridden.  I135 keeps its stored density: its own
        # absorption is negligible, and in a STATIC calculation its only role
        # would be as the Xe precursor, which does not act.  Zeroing it as well
        # would be a second, unrelated perturbation smuggled into the answer.
        _xe = f"\n               MICRO ALL Xe135 {float(XENON):.6E}"
    _setrest = ("" if WITH_THM else
                "\n               SET 'DCA' %s SET 'TF' 900.0 SET 'TG' 750.0" % DCA_SET)
    _mixes = ""
    for _b in range(XEBINS):
        # With one bin the clause is whatever U4_XENON asked for.  With several
        # the bin's own density always wins, because that is the whole point.
        # XEBINS > 1 with U4_XENON set to a number is the CONTROL: every bin
        # carries the same density, so splitting the fuel into several
        # identical mixtures must reproduce the single-mixture answer exactly.
        # It is the only way to show the binning itself adds nothing.
        _c = (_xe if (XEBINS == 1 or XENON != "stored")
              else "\n               MICRO ALL Xe135 %.6E" % xeval[_b])
        _mixes += "  MIX %d %s%s%s ENDMIX\n" % (M_FUEL + _b, _bmix, _setrest, _c)
    NCRFUEL = ("""MACFUEL := NCR: FCpo FMAP :: EDIT 0 MACRO LINEAR
  TABLE FCpo 'EDIRBMK'%s
%s  ;""" % (_bkey, _mixes))
    # U4_NCRCLAMP=1 (patch 0014): a map parameter beyond the COMPO's axis is
    # held at the axis edge instead of aborting the run.  Needed past the
    # peak of the steepest A8 cases, where the hottest bundle's effective
    # fuel temperature passes the TF axis top (2000 K): Doppler is then
    # frozen at its 2000 K value, which UNDER-states the feedback, so the
    # power and fuel enthalpy after that point are upper estimates.
    if os.environ.get("U4_NCRCLAMP", "0") != "0":
        NCRFUEL = NCRFUEL.replace("EDIT 0 MACRO LINEAR\n",
                                  "EDIT 0 MACRO LINEAR CLAMP\n", 1)
    # With THM:, 'DCA' and 'TF' are NOT set here: the fuel map carries them as
    # local parameters and NCR: picks a parameter up from the map whenever it
    # is not SET (NCRRGR.f:714-722 prints which ones SET overrides).  'TG' is
    # not in the map because nothing in DONJON computes a graphite temperature,
    # so it stays pinned -- Phase 2c.
    if WITH_THM:
        NCRFUEL = NCRFUEL.replace(
            "ENDMIX",
            ("SET 'TG' 750.0 ENDMIX" if VOID_FB else
             f"SET 'DCA' {DCA_SET} SET 'TG' 750.0 ENDMIX"))
    fbdoc = ("" if VOID_FB else
             "*  U4_VOIDFB=0: the coolant density is NOT taken from the map, it is pinned\n"
             f"*  at {DCA_SET} g/cm3, so this loop carries the DOPPLER feedback only.  Not a\n"
             "*  choice: the COMPO's DCA axis tops out at 0.72 g/cm3 and THM: computes\n"
             "*  0.778 at a 265 C channel inlet, so the fully-coupled loop cannot\n"
             "*  interpolate its own second iterate.  Core-wide cost of the override,\n"
             "*  measured: 103 pcm, and that is an upper bound.  The fix is to extend the\n"
             "*  DCA axis to ~0.80, which is one more value in a 7-value list and belongs\n"
             "*  in the A6b rebuild.\n")
    NCRFUEL_IND = "\n".join("  " + l for l in NCRFUEL.splitlines())
    # A8.3: THM feedback inside the kinetics loop.  Operator-split and
    # EXPLICIT in the feedback: step n's cross sections come from the TH
    # state at t(n-1), KINSOL: advances the flux over the step, and THM:
    # then advances the TH state over the same step with the power at t(n).
    # The lag is one step, which is why the timestep has to be converged
    # with feedback on, not inherited from the frozen-TH runs.
    #   TIME t0 dt   THMTRS, the transient driver; ITIME=1 forces RELAX=1
    #                (THM.f:622), so no Picard damping leaks into time.
    #   HISTORY 2    local patch 0004: keep two time steps, not all of them.
    #                Upstream keeps every step, ~11 MB each here, which is
    #                77 GB at 7000 steps on a 110 GB unified-memory machine.
    #   CONV ... ERMAXC  the flow tolerance.  ONLY the transient driver reads
    #                it (THMTRS.f:494; THMDRV never does), so the steady loop's
    #                1.0E-6 was never tested until A8.3 -- where THMTRS could not
    #                meet it in 100 iterations on the first step.  1.0E-6
    #                relative is within a decade of single-precision epsilon.
    #                Upstream's default is 1.0E-3; this is set tighter, and
    #                the answer's dependence on it is measured, not assumed.
    #   CYCLE-OK cap  local patch 0005: a channel whose flow iteration ends
    #                on the boiling-onset limit cycle (THMTRS's K0 switch) is
    #                accepted if the cycle's error is under the cap, and COUNTED
    #                -- every step reports how many and the worst.  Over the
    #                cap it aborts exactly as upstream does.
    #   U4_KINFB=0   the CONTROL: same deck, same steady state, but the TH
    #                state is frozen through the transient (no THM:, so the
    #                fuel map never changes and NCR: need not re-run).  The
    #                difference from KINFB=1 is the feedback and nothing else.
    #   FLOW-RELAX w  local patch 0006.  THMTRS's flow pass is a fixed point
    #                on the coolant density whose gain grows as 1/dt and 1/G;
    #                in a low-flow boiling channel it exceeds one and the pass
    #                oscillates (measured: channel 1433, 1.33 m/s, errors
    #                0.07-0.13 for 30 passes at t = 0.345 s).  w < 1 damps
    #                the carried density; the fixed point is unchanged.
    _frlx = "" if float(FRLX) == 1.0 else f" FLOW-RELAX {FRLX}"
    if KIN and WITH_THM and KINFB:
        _kncr = ("  MACFUEL MACRO := DELETE: MACFUEL MACRO ;\n"
                 + "\n".join("  " + l for l in NCRFUEL_IND.splitlines()) + "\n"
                 "    MACRO MATEX := MACINI: MATEX MACREF MACFUEL :: EDIT 0 ;\n")
        _kthm = f'''  POWER := DELETE: POWER ;
  POWER FMAP := FLPOW: FMAP KINET TRACK MATEX :: EDIT 0 ;
  THER FMAP := THM: THER FMAP :: EDIT 0 TIME <<t0>> <<dt>> HISTORY 2
    CONV 100 100 {FLOWIT} {ERMAXT} {ERMAXC_TR} CYCLE-OK {CYCCAP}{_frlx} ;
  GREP: THER :: GETVAL 'MAX-T-FUEL' 1 >>tmaxf<< ;
  GREP: THER :: GETVAL 'MIN-D-COOL' 1 >>dmin<< ;
  GREP: THER :: GETVAL 'FLOW-NCYCLE' 1 >>ncyc<< ;
  GREP: THER :: GETVAL 'FLOW-ERRCYC' 1 >>ecyc<< ;
  ECHO "A8THM" istep "T" tt "TMAXFUEL" tmaxf "DCOOLMIN" dmin
       "NCYC" ncyc "ERRCYC" ecyc ;
'''
    else:
        _kncr = _kthm = ""
    # U4_KINSHAPE=4,6,7 prints POWER-BUND at those times (s), for the
    # comparison against INSAG-7 Fig. II-9's 4/6/7 s curves.  The in-loop
    # FLPOW: refreshes it from the kinetics flux every step.
    if _kthm and KINSHAPE:
        for _ts in KINSHAPE:
            _k = int(round(_ts / KINDT))
            if 1 <= _k <= KIN:
                # U4_KINVOID=1 also prints the fuel map's D-COOL (PARAM 2,
                # NCH x NB like POWER-BUND, bottom bundle first): where the
                # steam is during the transient, for tools/a8_voidz.py
                _kvd = ("    UTL: FMAP :: STEP UP PARAM STEP AT 2 IMPR P-VALUE * ;\n"
                        if KINVOID else "")
                _kthm += (f'  IF istep {_k} = THEN\n    ECHO "A8SHAPE" istep "T" tt ;\n'
                          f'    UTL: POWER :: IMPR POWER-BUND * ;\n{_kvd}  ENDIF ;\n')
    _kthm = ("\n" + _kthm.rstrip("\n")) if _kthm else ""
    _kdecl = ("\nINTEGER ncyc := 0 ;\nREAL ecyc t0 := 0.0 0.0 ;" if (KIN and WITH_THM and KINFB) else "")
    _kt0 = "  EVALUATE t0 := tt ;\n" if (KIN and WITH_THM and KINFB) else ""
    kin_block = (kin_block.replace("@@KIN_NCR@@", _kncr).replace("@@KIN_THM@@", _kthm)
                 .replace("@@KIN_DECL@@", _kdecl).replace("@@KIN_T0@@", _kt0))

    param_block = "" if not WITH_THM else """*  THM: writes back by P-NAME and recognises exactly T-FUEL, D-COOL, T-COOL,
*  T-SURF, P-COOL (THM.f:1172-1174); NCR: reads by PARKEY, which is the
*  COMPO's own axis name.  Hence two names per parameter.  LOCAL is per
*  bundle, and SET-PARAM addresses by P-NAME and needs SAME before a value
*  for a LOCAL parameter (RESPAR.f:139-176).
  ADD-PARAM PNAME 'T-FUEL' PARKEY 'TF'  LOCAL
  ADD-PARAM PNAME 'D-COOL' PARKEY 'DCA' LOCAL
  SET-PARAM 'T-FUEL' SAME 900.0
  SET-PARAM 'D-COOL' SAME 0.72
"""
    param_block = param_block + INSTB + "\n"

    if WITH_THM:
        if FLOW == "prop":
            pw, psrc = chan_power()
            assert len(pw) == nfuel, f"{len(pw)} channel powers, {nfuel} channels"
            vel = ([V_REF * q / P_REF for q in pw] if TH_STATE == "nom" else
                   [V_ACC * q * len(pw) / sum(pw) for q in pw])
            speed = ("  SPEED CHAN\n"
                     + fmt([f"{v:.4f}" for v in vel], 12, "    "))
            flowdoc = (f"*  U4_FLOW=prop: every channel valved to its own power, so each gets\n"
                       f"*  {V_REF:.4f} m/s x P/{P_REF:.0f} kW -- [D] p.95's 30 t/h at 3100 kW, with the\n"
                       f"*  velocity taken from THM:'s OWN answer for that point (A7a) so that no\n"
                       f"*  steam table of ours enters the scaling.  Channel powers from\n"
                       f"*  {os.path.relpath(psrc, ROOT)}\n"
                       f"*  (POWER-CHAN, channel order): {min(pw):.0f} to {max(pw):.0f} kW, mean {sum(pw)/len(pw):.0f}.\n"
                       f"*  Velocities {min(vel):.3f} to {max(vel):.3f} m/s; total flow\n"
                       f"*  {sum(pw)/P_REF*30.0:.0f} t/h against a real RBMK's ~37 500.\n"
                       f"*  THIS MAKES THE EXIT QUALITY FLAT BY CONSTRUCTION, which is the design\n"
                       f"*  intent and therefore also the uninformative end of the bracket.\n")
        else:
            pw, psrc = chan_power()
            vbar = (V_REF * (sum(pw) / len(pw)) / P_REF if TH_STATE == "nom"
                    else V_ACC)
            speed = f"  SPEED {vbar:.4f}"
            flowdoc = (f"*  U4_FLOW=unif: one velocity everywhere, {vbar:.4f} m/s, the core-average\n"
                       f"*  of the same normalisation.  No valving at all, so the hot channels\n"
                       f"*  boil much harder than the cold ones -- the other end of the bracket.\n")
        if TH_STATE == "acc":
            flowdoc = (
                f"*  U4_TH=acc -- THE 01:23 STATE, INSAG-7 p. 64: {PTOT_MW:.0f} MW(th), coolant\n"
                f"*  {Q_ACC:.0f} m3/h (8 MCPs), inlet subcooling {SUBC:g} K.  Inlet at THM:'s own\n"
                f"{QNOTE}"
                f"*  (IF97) T_sat {tsat_if97(P_OUT):.2f} K at {P_OUT / KGF:.1f} kgf/cm2 less {SUBC:g} K = {T_IN:.2f} K;\n"
                f"*  the 01:23 pressure is not sourced, the subcooling is.  Mean inlet\n"
                f"*  velocity {V_ACC:.4f} m/s = the volumetric flow over 1661 x 22.427 cm2.\n"
                f"*  The NOMINAL normalisation text below is superseded by this: under\n"
                f"*  prop each channel gets {V_ACC:.4f} m/s x P/<P>; under unif all get it.\n"
                + flowdoc)
        thm_block = f"""{flowdoc}  THER FMAP := THM: FMAP ::
    EDIT 1
*   CONV is <conduction its> <centre-pellet its> <flow its> <ERMAXT> <ERMAXC>
*   (THM.f).  ERMAXT is THM:'s OWN inner temperature tolerance in K, kept an
*   order of magnitude below upstream's 0.5 so the inner solve is tighter than
*   anything the outer loop tests.  It is NOT why the loop converges: that was
*   the 2026-10-01 diagnosis and it was disproved the next day -- tightening
*   this ten-fold left both the eigenvalue and the residual plateau unchanged,
*   because the plateau is a limit cycle.  See the convergence block below.
    CONV 100 100 100 {ERMAXT} 1.0E-6
    INLET {P_OUT:.6E} {T_IN:.4f}
{speed}
    CLUSTER {TH_PITCH:.6E} {TH_NPIN}
    RADIUS {R_PELLET:.6E} {R_GAP:.6E} {R_CLAD:.6E} 0.0
    RODMESH 15 20
    CRITFL 1.80E+6
*   SAHA, not the default Bowring: Bowring's XFL never reverts to the
*   thermodynamic quality once the bulk saturates (THMH2O.f:161).
    SAHA
*   HGAP set, not computed: THM:'s correlation implies a far tighter gap than
*   this fuel's 100 um and lands 780 K low on [D]'s centreline (A7a).
    HGAP {TH_HGAP:.4E}
*   DFM 0 because THMTRS.f:157 forces it in the transient; converging the
*   steady state with drift flux would change void model at t = 0.
    DFM 0
    RELAX {RELAX}
    ;"""
        solver = f"""TRACK := TRIVAT: GEO2 :: EDIT 0 MAXR {nel} DUAL 1 1 ;

{fbdoc}*--- A7: Picard loop.  Flux -> power -> thermal-hydraulics -> coolant density
*    and fuel temperature back into the cross-section interpolation, until the
*    fuel temperature stops moving.
REAL errt errd kprev dk := 1.0E+10 1.0E+10 0.0 1.0E+10 ;
INTEGER iter := 0 ;
LOGICAL conv ;
REPEAT
  EVALUATE iter := iter 1 + ;
{NCRFUEL_IND}
  MACRO MATEX := MACINI: MATEX MACREF MACFUEL :: EDIT 0 ;
{newmac_i}  SYSTEM := TRIVAA: {macsys} TRACK :: EDIT 0{tvopt} ;
  FLUX := FLUD: SYSTEM TRACK :: EDIT 0 ADI 2 EXTE 300 1.0E-6 ;
  GREP: FLUX :: GETVAL 'K-EFFECTIVE' 1 >>keff<< ;
  POWER FMAP := FLPOW: FMAP FLUX TRACK MATEX :: EDIT 0 PTOT {PTOT_MW:.1f} ;
  IF iter 1 = THEN
{thm_block}
  ELSE
    THER FMAP := THM: THER FMAP :: EDIT 1 ;
  ENDIF ;
  GREP: THER :: GETVAL 'ERROR-T-FUEL' 1 >>errt<< ;
*   ERROR-D-COOL is the residual that actually matters here.  Measured
*   2026-10-02: at RELAX 0.5 T-FUEL plateaus around 2 K while D-COOL plateaus
*   around 0.02 g/cc, both bounded away from zero, with the field EXTREMA frozen to
*   the thousandth and keff bit-stable.  That is a limit cycle at the
*   boiling-onset node, not an unconverged solve, so the loop has to report
*   the density residual rather than infer it from the temperature one.
  GREP: THER :: GETVAL 'ERROR-D-COOL' 1 >>errd<< ;
  EVALUATE dk := keff kprev - ABS ;
  EVALUATE kprev := keff ;
  ECHO "{tag} ITER" iter "KEFF" keff "DK" dk "ERRT" errt "ERRD" errd ;
*   CONVERGENCE IS TESTED ON THE EIGENVALUE, NOT ON THE TEMPERATURE FIELD,
*   and the reason is measured rather than assumed.  THM: reports the
*   pass-to-pass residual of each field it writes back (THM.f:1211); the
*   fuel-temperature one does not go to zero.  It plateaus, with the field
*   EXTREMA frozen to the thousandth of a degree and keff bit-stable for
*   twenty passes -- bit-stable keff means bit-stable power, so a converged
*   field would give exactly zero.  It is a limit cycle, and the mechanism is
*   in the source: K0 is an INTEGER node index set by the Saha-Zuber onset
*   test IF(TCALO.GE.TSAT-DTSUB) K0=K (THMH2O.f:383), reset to 0 at :276,
*   and it gates the whole two-phase block at :147.  A node sitting within
*   rounding of that threshold flips the branch on and off, moving its
*   density by a finite step each pass, and DTSUB depends on the heat flux,
*   so the switch lives INSIDE the Picard loop.  No tolerance removes it.
*   Measured 2026-10-02 at RELAX 1.0 / 0.5 / 0.2, the plateau falls -- about
*   7, 2 and 0.6 K, and it is noisy from pass to pass because it is a cycle
*   and not a residual -- faster than RELAX itself, so under-relaxation both
*   rescales the step and partly damps the switching; but it never reaches
*   zero, and keff came out BIT-IDENTICAL at all three, 1.039735.  The
*   relaxation factor is a solver parameter and the answer does not depend on
*   it.  So the loop converges what converges, and reports the rest.
  EVALUATE conv := iter 0 < ;
  IF dk {DKTOL} < THEN
    IF iter 10 > THEN
      EVALUATE conv := iter 0 > ;
    ENDIF ;
  ENDIF ;
  IF iter {MAXIT} > THEN
    EVALUATE conv := iter 0 > ;
  ENDIF ;
  MACFUEL MACRO{macrd} SYSTEM FLUX POWER := DELETE:
    MACFUEL MACRO{macrd} SYSTEM FLUX POWER ;
UNTIL conv ;
ECHO "{tag} CONVERGED keff" keff "after" iter "iterations, errt" errt "errd" errd ;

*--- ONE FINAL SOLVE ON THE CONVERGED FIELD.
*    The loop deletes FLUX at the end of every pass, so everything below it
*    used to reference an object that no longer existed -- the deck died with
*    kernel error 666 (LINKED_LIST *FLUX* IS NOT DEFINED) after printing the
*    loop's own results, and the power-shape block had never once run.
*    Rebuilding here is also the more correct order: inside the loop the power
*    is computed BEFORE that pass's THM: update, so the last in-loop power
*    belongs to the previous temperature field, not the converged one.
{NCRFUEL}
MACRO MATEX := MACINI: MATEX MACREF MACFUEL :: EDIT 0 ;
{newmac}SYSTEM := TRIVAA: {macsys} TRACK :: EDIT 0{tvopt} ;
FLUX := FLUD: SYSTEM TRACK :: EDIT 0 ADI 2 EXTE 300 1.0E-6 ;
GREP: FLUX :: GETVAL 'K-EFFECTIVE' 1 >>keff<< ;
ECHO "{tag} FINAL keff" keff ;

*--- the converged state, for the comparison against [D] p.95 and for A8
UTL: THER :: STEP UP 'HISTORY-DATA' STEP UP 'TIMESTEP0000'
             STEP UP 'CHANNEL' STEP AT 1
  IMPR XFL * IMPR COOLANT-TEMP * IMPR DENSITY * IMPR VELOCITIES * ;
GREP: THER :: GETVAL 'MAX-T-FUEL' 1 >>tmaxf<< ;
GREP: THER :: GETVAL 'MIN-D-COOL' 1 >>dmin<< ;
GREP: THER :: GETVAL 'MAX-D-COOL' 1 >>dmax<< ;
ECHO "{tag} TMAXFUEL" tmaxf "DCOOL" dmin dmax ;{thdump}"""
    else:
        solver = f"""{NCRFUEL}

MACRO MATEX := MACINI: MATEX MACREF MACFUEL :: EDIT 0 ;

TRACK := TRIVAT: GEO2 :: EDIT 0 MAXR {nel} DUAL 1 1 ;
{newmac}SYSTEM := TRIVAA: {macsys} TRACK :: EDIT 0{tvopt} ;
FLUX := FLUD: SYSTEM TRACK :: EDIT 1 ADI 2 EXTE 300 1.0E-6 ;
GREP: FLUX :: GETVAL 'K-EFFECTIVE' 1 >>keff<< ;
ECHO "{tag} KEFF" keff ;"""

    refl_line = (f"{nrefl_col} radial reflector columns in {nring} rings "
                 f"(mix {M_REFL[0]}..{M_REFL[-1]}), {per_ring} per ring "
                 f"from the core outward." if WITH_REFL else
                 "NO RADIAL REFLECTOR (U4_REFL=0): the VOID boundary sits on "
                 "the core outline.")
    ther_obj = " THER" if WITH_THM else ""
    dev_obj = (" DEVICE MACRD" if DEV else "") + (" KINET" if KIN else "")
    dev_mod = ((" DEVINI: DSET: NEWMAC: MOVDEV:" if DEV else "")
               + (" INIKIN: KINSOL:" if KIN else ""))
    thm_mod = " THM:" if WITH_THM else ""
    extra_reals = " tmaxf dmin dmax" if WITH_THM else ""
    refl_mixes = ("  COMPO RCpo 'EDIREFL'\n" + "".join(
        f"  MIX {m} FROM {5 + k} SET 'burnup' 10900.0 SET 'DCA' 0.72 ENDMIX\n"
        for k, m in enumerate(M_REFL))) if WITH_REFL else ""

    deck = f"""*----
*  CHERNOBYL UNIT 4 CORE (A6.5) -- GENERATED by decks/Donjon/data/gen_rbmk_unit4.py.
*  Edit the generator, not this file.
*
*  {nx} x {ny} x {nz} nodes at {PITCH:.0f} cm.  {ni} x {nj} channel positions from
*  sources/derived/unit4_channel_map.csv inside a graphite stack of {ncol}
*  columns ([D]: 2488), bounded by a circle of radius {R_STACK} cells.  Outside
*  that circle the mixture is 0 -- a virtual volume (USPMIX.f:52), not graphite.
*
*  {nfuel} fuel channels (mix {M_FUEL}), {ncps} CPS/detector channels.
*  {refl_line}
*  {NZ_ACTIVE} active planes ({NZ_ACTIVE * PITCH:.0f} cm) and {NZ_REFL} reflector planes each end;
*  {ndistinct} distinct PLANE blocks, the rest written as SAME.
*
*  RODS: U4_RODS={RODS}.  {nrod} RR/AZ channels carry the stack
*  {stackline}
*  read bottom-up over the active planes (W water, D graphite displacer,
*  A B4C absorber).  The other {ncps - nrod} CPS positions -- {nar} AR, {nusp} USP and
*  {ndet} detector tubes -- are a water column in every variant, so a
*  difference between two variants is the displacer and absorber alone.
*
*  CROSS SECTIONS.  Fuel from _ACompo; the three CPS channel states from
*  _CCompoWAT / _CCompoABS / _CCompoDSP zone 5; reflector rings from _RCompo
*  zones 5..8 (3 graphite + 1 cooled).  All at a UNIFORM burnup of
*  10900 MWd/t, the Unit 4 core average: the burnup PLACEMENT map is still an
*  open A6d item, so a flat field is the honest stand-in and the per-channel
*  route (INST-BURN off the fuel map) is wired but not yet fed.
*
*  The rod cells carry A6.4's measured one-signed bias: an inserted absorber
*  is 7-10 % short on worth, because the eight fuel cells around it are drawn
*  from the infinite-lattice COMPO and the real ones are perturbed.  Absorber
*  worths from this deck are therefore LOWER BOUNDS, and that bias does not
*  touch the displacer, which is graphite.
*
*  k FROM THIS DECK IS REPORTED, NOT ASSERTED.  The reflector carries a
*  measured homogenisation error (PROGRESS.md, Phase 1b) and the burnup is
*  flat; the gate here is that the geometry, the fuel map and the solver chain
*  are right and FLUD: converges.
*----
LINKED_LIST GEOM GEO2 MATEX FMAP MACREF MACFUEL MACRO{dev_obj}
            TRACK SYSTEM FLUX POWER{ther_obj} FCpo CCpo ACpo DCpo{rcpo_arg} ;
SEQ_ASCII   _ACompo    :: FILE './_ACompo' ;
SEQ_ASCII   _CCompoWAT :: FILE './_CCompoWAT' ;
SEQ_ASCII   _CCompoABS :: FILE './_CCompoABS' ;
SEQ_ASCII   _CCompoDSP :: FILE './_CCompoDSP' ;{rcpo_seq}
MODULE      GEO: USPLIT: RESINI: NCR: MACINI: TRIVAT: TRIVAA: FLUD:
            FLPOW:{thm_mod}{dev_mod} UTL: GREP: DELETE: END: ;
REAL keff{extra_reals} ;

FCpo := _ACompo ;
CCpo := _CCompoWAT ;
ACpo := _CCompoABS ;
DCpo := _CCompoDSP ;{rcpo_asg}

*--- core geometry: one node per column, mixture 0 outside the graphite stack
GEOM := GEO: :: CAR3D {nx} {ny} {nz}
  EDIT 0
  X- VOID X+ VOID  Y- VOID Y+ VOID  Z- VOID Z+ VOID
  MIX
{mixmap}
  MESHX
{mesh(nx)}
  MESHY
{mesh(ny)}
  MESHZ
{fmt(zedges, 10)}
  ;

GEO2 MATEX := USPLIT: GEOM :: EDIT 0
  NGRP 2 MAXR {nel}
  NREFL {3 + nring} RMIX {M_WAT} {M_ABS} {M_DSP} {" ".join(str(m) for m in M_REFL)}
  NFUEL {XEBINS} FMIX {fmixlist} ;

{dev_block}*--- the fuel map: {nfuel} channels, numbered in the B-ZONE block below
FMAP MATEX := RESINI: MATEX ::
  ::: GEO: CAR3D {nx} {ny} {nz}
      EDIT 0
      X- VOID X+ VOID  Y- VOID Y+ VOID  Z- VOID Z+ VOID
      MIX
{fmapmap}
      MESHX
{mesh(nx)}
      MESHY
{mesh(ny)}
      MESHZ
{fmt(zedges, 10)}
      ;
  NXNAME {nxname}
  NYNAME {nyname}
  NCOMB {nfuel}
  B-ZONE
{bzone}
{param_block}  ;

*--- non-fuel constants: the CPS water column and the four reflector rings.
*    MACINI: indexes this macrolib by MATERIAL number, so mixture k here is
*    material k and the order must match RMIX above (1Sap_vs_3Sap.x2m:29).
MACREF := NCR: CCpo ACpo DCpo{rcpo_arg} :: EDIT 0 MACRO LINEAR NMIX {3 + nring}
  COMPO CCpo 'EDICPS'
  MIX {M_WAT} FROM 5 SET 'burnup' 10900.0 SET 'DCA' 0.72 SET 'TF' 900.0 ENDMIX
  COMPO ACpo 'EDICPS'
  MIX {M_ABS} FROM 5 SET 'burnup' 10900.0 SET 'DCA' 0.72 SET 'TF' 900.0 ENDMIX
  COMPO DCpo 'EDICPS'
  MIX {M_DSP} FROM 5 SET 'burnup' 10900.0 SET 'DCA' 0.72 SET 'TF' 900.0 ENDMIX
{refl_mixes}  ;


{solver}

*--- power shape.  PTOT is the nominal thermal rating; the shape, not the
*    normalisation, is what this increment checks.
POWER FMAP := FLPOW: FMAP FLUX TRACK MATEX ::
  EDIT 2 PTOT {PTOT_MW:.1f} PRINT DISTR POWER ;

*--- the {nfuel} channel powers in CHANNEL ORDER -- the order RESPFM.f:74-82
*    finds them, which is the order B-ZONE above is written in and the order
*    THMINP reads a per-channel list in.  A7b sets each channel's coolant flow
*    from its power, so this is the handover and it has to be the flat list
*    rather than the radial-plane table FLPOW: prints.
UTL: POWER :: IMPR POWER-CHAN * ;{pbund}

{kin_block}
ECHO "UNIT4 geometry {nx} x {ny} x {nz}, {nfuel} fuel, {ncps} CPS, {nrefl_col} reflector" ;
ECHO "{stem} completed" ;
END: ;
QUIT .
"""
    # CLE-2000 reads columns 1-120 only (clelog.c:31) and says only "ERROR
    # NUMBER (5000)" when it does not; name the offending line here instead.
    over = [l for l in deck.splitlines() if len(l) > 120]
    assert not over, f"{len(over)} line(s) over 120 columns, first: {over[0][:80]!r}"
    open(OUT, "w").write(deck)
    acc = OUT + ".access"
    open(acc, "w").write("#!/bin/sh\n"
                         "# Generated by gen_rbmk_unit4.py: stage the MULTICOMPOs into the\n"
                         "# scratch run directory, as the A6.4 gate decks do.\n"
                         'src="$1"/../Dragon/compo\n'
                         + ('cp "$src"/_ACompoVB ./_ACompo || exit 1\n' if VOIDB else
                            'cp "$src"/_ACompo . || exit 1\n')
                         + 'cp "$src"/_CCompoWAT . || exit 1\n'
                         + ('cp "$src"/_CCompoABScB ./_CCompoABS || exit 1\n'
                            'cp "$src"/_CCompoDSPcB ./_CCompoDSP || exit 1\n' if CPSB else
                            'cp "$src"/_CCompoABS . || exit 1\n'
                            'cp "$src"/_CCompoDSP . || exit 1\n')
                         + ('cp "$src"/_RCompo . || exit 1\n' if WITH_REFL else ""))
    os.chmod(acc, 0o755)
    print(f"wrote {os.path.relpath(OUT, ROOT)}")
    print(f"  grid {nx} x {ny} x {nz} = {nel} nodes, "
          f"{nx * PITCH:.0f} x {ny * PITCH:.0f} x {nz * PITCH:.0f} cm")
    print(f"  {nfuel} fuel + {ncps} CPS = {len(g)} channels")
    print(f"  stack {ncol} columns ([D]: 2488), {nrefl_col} reflector, "
          f"rings {per_ring}")
    print(f"  non-virtual volumes {ncol * nz} of {nel}")


if __name__ == "__main__":
    main()
