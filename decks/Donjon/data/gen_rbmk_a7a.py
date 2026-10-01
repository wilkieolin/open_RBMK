#!/usr/bin/env python3
"""A7a -- the RBMK fuel channel against published operating data.

    python decks/Donjon/data/gen_rbmk_a7a.py     # -> rbmk_a7a.don

WHY A SINGLE CHANNEL FIRST.  `docs/report.html`'s first known gap is "no
comparison against measurement, at any level": everything in this project so
far is DRAGON against OpenMC, two codes on the same geometry.  [D p.95] breaks
that, and it does so for the thermal-hydraulics rather than the neutronics:

    channel power        3000-3200 kW
    coolant flow         29.5-30.5 t/h
    exit quality         19.6 %
    inlet                79.6 kgf/cm2  /  265 C
    outlet               75.3 kgf/cm2  /  289.3 C
    max coolant velocity 18.5 m/s
    clad surface         295 C,  clad inner 323 C
    pellet centreline    2100 C
    axial peaking        1.4,  radial 1.06
    max linear rating    360-385 W/cm

Those are one self-consistent operating point for one channel, and they
over-determine it: given the power, the flow and the inlet state, the exit
quality and the outlet temperature follow from an energy balance and nothing
else.  So this deck prescribes power, flow and inlet state, and COMPARES the
quality, the outlet temperature and the temperatures against the rest.
Nothing is tuned to them -- the channel geometry comes from the A6.1 cell,
closed against eight sources, and the equivalent pitch is derived below.

WHAT IS BEING TESTED, AND WHAT IS NOT.  The exit quality and the outlet
temperature are integrals of the total channel power, so they test the FLOW
AREA and the coolant property package and are nearly independent of the axial
shape.  The clad-surface and centreline temperatures are local, so they test
the heat-transfer correlation, the hydraulic diameter and the axial shape
together.  Read them as two separate results.

THE EQUIVALENT PITCH IS THE MODELLING CHOICE HERE, AND IT IS NOT FREE.
`THM:`'s `CLUSTER <pitch> <npins>` models a rod bundle as an infinite
TRIANGULAR array (THM.f:963-971: a hexagon of three Wigner-Seitz cells, three
rod areas subtracted, perimeter 6*pi*R).  An RBMK channel is 18 rods on two
rings inside a 4 cm tube, around a central carrier tube -- so one pitch cannot
reproduce the flow area, the hydraulic diameter and the heated perimeter at
once.  It is also not even close: the real channel has an unheated outer
annulus and an unheated central tube, which a triangular array has no room
for.  Both candidate pitches are therefore derived and BOTH ARE RUN:

    U4A_FIT=area   match the flow area  -> hydraulic diameter comes out high
    U4A_FIT=dh     match the diameter   -> flow area comes out low

The flow area is the one that sets the coolant enthalpy rise, and so the void
distribution, which is the dominant feedback in this reactor; the hydraulic
diameter only sets the film coefficient, and so the fuel temperature, which is
a weaker and already-bracketed feedback.  So `area` is the nominal and `dh` is
the bracket -- stated, not fitted, and the published quality settles which was
the better choice rather than being used to pick it.

KNOWN APPROXIMATIONS, all in `THM:` rather than in the inputs:
  * THE PELLET IS SOLID.  `RADIUS` takes the pellet radius and integrates the
    conduction from r=0 (THM.f:458-470); there is no hollow-pellet option.
    The real RBMK pellet has a 2 mm central hole, so the predicted centreline
    temperature is biased HIGH -- a solid pellet has nowhere to put the heat
    generated where the hole is.
  * `CLUSTER` has no unheated perimeter, so all of the wetted perimeter is
    treated as heated.  That is the other half of the pitch problem above.
  * `DFM 0`.  Transient `THM:` assigns IDFM = 0 unconditionally
    (THMTRS.f:157), so a steady state converged with drift flux would change
    void model the instant A8 starts.  Homogeneous flow throughout, with
    drift flux left as a steady-state sensitivity.
"""
import math
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", ".."))
CELL = os.path.join(ROOT, "openmc", "rbmk_cell.py")
FIT = os.environ.get("U4A_FIT", "area")
_T = os.environ.get("U4A_TAG", "")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "rbmk_a7a.don" if (FIT == "area" and not _T)
                   else f"rbmk_a7a_{_T or FIT}.don")

# ---------------------------------------------------------------- the channel
# Read the geometry out of openmc/rbmk_cell.py rather than restating it: that
# file is the one closed against eight sources in A6.1 and it is what the
# OpenMC cross-check runs on, so a divergence here would be a silent second
# geometry.  Parsed, not imported, because importing it pulls in openmc.
def cell_consts():
    src = open(CELL).read()
    want = ("R_CHANNEL", "R_CTUBE_OUT", "R_HOLE", "R_PELLET", "R_GAP", "R_CLAD")
    out = {}
    for name in want:
        m = re.search(rf"^{name}\s*=\s*([0-9.]+)", src, re.M)
        assert m, f"{name} not found in {CELL}"
        out[name] = float(m.group(1))
    return out


G = cell_consts()
NPIN = 18                       # [D] p.11: 18 rods on a central Zr tube
PI = math.pi

# flow area, cm2: the tube bore less the rods and the central carrier tube
A_FLOW = PI * (G["R_CHANNEL"] ** 2 - NPIN * G["R_CLAD"] ** 2
               - G["R_CTUBE_OUT"] ** 2)
# wetted perimeter: rods + carrier tube + the tube wall itself
P_WET = 2 * PI * (NPIN * G["R_CLAD"] + G["R_CTUBE_OUT"] + G["R_CHANNEL"])
P_HEAT = 2 * PI * NPIN * G["R_CLAD"]          # only the rods are heated
D_H = 4 * A_FLOW / P_WET

# THM's CLUSTER geometry, per rod: a Wigner-Seitz hexagon of a triangular
# array of pitch p, less one rod (THM.f:963-971 does three of these at once).
RGG = G["R_CLAD"]
a_rod = lambda p: math.sqrt(3) / 2 * p * p - PI * RGG ** 2
p_area = math.sqrt((A_FLOW / NPIN + PI * RGG ** 2) / (math.sqrt(3) / 2))
# D_h of the array is 4*a_rod/(2*pi*RGG); solve for the pitch that matches
p_dh = math.sqrt((D_H * 2 * PI * RGG / 4 + PI * RGG ** 2) / (math.sqrt(3) / 2))
PITCH = {"area": p_area, "dh": p_dh}[FIT]

A_MODEL = NPIN * a_rod(PITCH)                       # cm2
DH_MODEL = 4 * a_rod(PITCH) / (2 * PI * RGG)        # cm

# ------------------------------------------------------- the operating point
# [D] p.95, verbatim, converted only in units.
KGF = 98066.5                   # Pa per kgf/cm2, exact by definition
P_OUT = 75.3 * KGF              # outlet pressure, Pa
T_IN = 265.0 + 273.15           # inlet temperature, K
MDOT = float(os.environ.get("U4A_MDOT", "30.0")) * 1000.0 / 3600.0   # kg/s
PCH_KW = float(os.environ.get("U4A_POW", "3100.0"))                  # kW
# U4A_HGAP: pellet-clad gap conductance, W/m2/K.  0 lets THM compute it.
# It is the knob the centreline temperature hangs on and it is NOT sourced,
# so it is swept rather than chosen -- see tools/a7a_check.sh.
HGAP = float(os.environ.get("U4A_HGAP", "0"))
TAG = os.environ.get("U4A_TAG", "")
AX_PEAK = 1.4                   # [D] p.95 axial peaking; see below
NZ = 28                         # 28 x 25 cm = 7000 mm channel ([D] p.95)
PITCH_Z = 25.0
BURNUP = 10900.0                # MWd/t, the Unit 4 core average

# Axial power shape.  The SOURCE is the peaking factor 1.4; the functional
# form is an assumption.  A cosine truncated short of its zeros is the
# one-parameter family a reflected core produces, so solve its half-width for
# peak/mean = 1.4 rather than picking a shape that happens to give it.
def cosine_shape(peak, n):
    def ratio(c):
        return c / (2.0 * math.sin(c / 2.0))
    lo, hi = 1e-6, math.pi - 1e-6
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if ratio(mid) < peak:
            lo = mid
        else:
            hi = mid
    c = 0.5 * (lo + hi)
    f = [math.cos(c * ((k + 0.5) / n - 0.5)) for k in range(n)]
    s = sum(f) / n
    return c, [x / s for x in f]          # normalised to mean 1


C_HALF, SHAPE = cosine_shape(AX_PEAK, NZ)


def fmt(items, per, indent="    "):
    out, line = [], []
    for it in items:
        line.append(it)
        if len(line) == per:
            out.append(indent + " ".join(line)); line = []
    if line:
        out.append(indent + " ".join(line))
    return "\n".join(out)


def main():
    hgap_line = (f"  HGAP {HGAP:.4E}\n" if HGAP > 0 else
                 "*  HGAP not given: THM: computes the gap conductance itself.\n")
    zedges = [f"{k * PITCH_Z:.1f}" for k in range(NZ + 1)]
    deck = f"""*----
*  A7a -- ONE RBMK FUEL CHANNEL AGAINST [D] p.95.
*  GENERATED by decks/Donjon/data/gen_rbmk_a7a.py.  Edit the generator.
*
*  Prescribed, from [D] p.95: channel power {PCH_KW:.0f} kW, flow
*  {MDOT * 3600 / 1000:.1f} t/h, outlet pressure {P_OUT:.4E} Pa ({P_OUT / KGF:.1f} kgf/cm2),
*  inlet temperature {T_IN:.2f} K ({T_IN - 273.15:.0f} C), axial peaking {AX_PEAK}.
*
*  Compared, NOT tuned: exit quality (published 19.6 %), outlet coolant
*  temperature (289.3 C), clad surface (295 C), pellet centreline (2100 C),
*  peak coolant velocity (18.5 m/s), max linear rating (360-385 W/cm).
*
*  CHANNEL GEOMETRY, from openmc/rbmk_cell.py (A6.1, closed against eight
*  sources) -- parsed from that file by the generator, not restated:
*    tube bore          {G["R_CHANNEL"]:.4f} cm        {NPIN} rods, clad OD {2 * G["R_CLAD"]:.4f} cm
*    carrier tube OD    {G["R_CTUBE_OUT"]:.4f} cm        pellet OD  {2 * G["R_PELLET"]:.4f} cm
*    flow area          {A_FLOW:.4f} cm2      wetted perim {P_WET:.4f} cm
*    heated perimeter   {P_HEAT:.4f} cm       hydraulic D  {D_H:.4f} cm
*
*  EQUIVALENT CLUSTER PITCH: U4A_FIT={FIT}, pitch {PITCH:.4f} cm.
*    this model's flow area        {A_MODEL:.4f} cm2   ({100 * (A_MODEL / A_FLOW - 1):+.1f} % vs real)
*    this model's hydraulic D      {DH_MODEL:.4f} cm    ({100 * (DH_MODEL / D_H - 1):+.1f} % vs real)
*  THM:'s CLUSTER is a triangular array and an RBMK channel is not one, so
*  one pitch cannot match both; see the generator header for why the flow
*  area is the nominal choice and the diameter is the bracket.
*
*  CLOSURE, before any calculation: {PCH_KW:.0f} kW over {NZ * PITCH_Z:.0f} cm over {NPIN} rods at
*  peak/mean {AX_PEAK} is {PCH_KW * 1000.0 * max(SHAPE) / (NZ * PITCH_Z * NPIN):.0f} W/cm per rod, against [D] p.95's own
*  360-385 W/cm maximum.  It sits just below because a channel-average model
*  carries no rod-to-rod peaking; a 1.07 factor puts it at {PCH_KW * 1000.0 * max(SHAPE) * 1.07 / (NZ * PITCH_Z * NPIN):.0f}.  Power,
*  length and rod count are therefore mutually consistent, with nothing fitted.
*
*  Axial shape: cosine of half-width {C_HALF:.4f} rad, solved for peak/mean
*  = {AX_PEAK} ([D] p.95).  The peaking is sourced; the cosine is an assumption.
*  It barely affects the quality and the outlet temperature, which are
*  integrals of the total power, and it does affect the local temperatures.
*----
LINKED_LIST GEOM GEO2 MATEX FMAP THER ;
MODULE      GEO: USPLIT: RESINI: THM: UTL: GREP: DELETE: END: ;
REAL eout tmaxf ;

*--- one channel, {NZ} bundles of {PITCH_Z:.0f} cm.  There is no neutronics in this deck:
*    the power is prescribed and THM: reads it from the fuel map's BUND-PW.
GEOM := GEO: :: CAR3D 1 1 {NZ}
  EDIT 0
  X- REFL X+ REFL  Y- REFL Y+ REFL  Z- VOID Z+ VOID
  MIX
{chr(10).join(f"PLANE {k}" + ("  1" if k == 1 else " SAME 1") for k in range(1, NZ + 1))}
  MESHX 0.0 {PITCH_Z:.1f}
  MESHY 0.0 {PITCH_Z:.1f}
  MESHZ
{fmt(zedges, 10)}
  ;

GEO2 MATEX := USPLIT: GEOM :: EDIT 0 NGRP 2 MAXR {NZ}
  NFUEL 1 FMIX 1 ;

FMAP MATEX := RESINI: MATEX ::
  ::: GEO: CAR3D 1 1 {NZ}
      EDIT 0
      X- REFL X+ REFL  Y- REFL Y+ REFL  Z- VOID Z+ VOID
      MIX
{chr(10).join(f"PLANE {k}" + ("  1" if k == 1 else " SAME 1") for k in range(1, NZ + 1))}
      MESHX 0.0 {PITCH_Z:.1f}
      MESHY 0.0 {PITCH_Z:.1f}
      MESHZ
{fmt(zedges, 10)}
      ;
  NXNAME 'A'
  NYNAME '1'
  NCOMB 1
  B-ZONE 1
*  THM: writes back into parameters it recognises BY P-NAME (THM.f:1138-1142
*  accepts T-FUEL, D-COOL, T-COOL, T-SURF, P-COOL); NCR: later reads them by
*  PARKEY, which is why the two names differ.  LOCAL means per bundle.
  ADD-PARAM PNAME 'T-FUEL' PARKEY 'TF'  LOCAL
  ADD-PARAM PNAME 'D-COOL' PARKEY 'DCA' LOCAL
  ADD-PARAM PNAME 'T-COOL' PARKEY 'TCA' LOCAL
*  SET-PARAM addresses a parameter by its P-NAME, not its PARKEY (RESPAR.f:
*  "UNABLE TO FIND PARAMETER WITH PNAME"), so these are the THM: names.
*  A LOCAL parameter needs SAME | CHAN | BUND before its value
*  (RESPAR.f:164-176); only a GLOBAL one takes a bare number.
  SET-PARAM 'T-FUEL' SAME 900.0
  SET-PARAM 'D-COOL' SAME 0.72
  SET-PARAM 'T-COOL' SAME 538.15
  INST-BVAL SAME {BURNUP:.1f}
  REACTOR-POW {PCH_KW / 1000.0:.6f}
  AXIAL-PFORM
{fmt([f"{x:.6f}" for x in SHAPE], 7)}
  ;

THER FMAP := THM: FMAP ::
  EDIT 3
  CONV 100 100 100 0.5 1.0E-4
  INLET {P_OUT:.6E} {T_IN:.4f}
*  INLET-Q takes the flow SECTION and the MASS FLOW and computes the velocity
*  itself from its own water properties at the inlet state -- so no steam
*  table of ours enters the comparison.  Both arguments are PER CHANNEL, so
*  the SUMSEC/CWSECT line THM: prints compares a channel against a channel.
  INLET-Q {A_FLOW * 1.0E-4:.6E} {MDOT:.6f}
  CLUSTER {PITCH * 1.0E-2:.6E} {NPIN}
  RADIUS {G["R_PELLET"] * 1.0E-2:.6E} {G["R_GAP"] * 1.0E-2:.6E} {G["R_CLAD"] * 1.0E-2:.6E} 0.0
  RODMESH 15 20
  CRITFL 1.80E+6
*  SAHA selects the Saha-Zuber profile-fit boiling model (ISUBM=2); the
*  DEFAULT is Bowring (ISUBM=1).  This is not a free choice.  Bowring's
*  subcooled form is XFL = XFL0 + Q/(mdot*hfg*(1+PI)) with
*  PI = rho_l*cp*(Tsclad-Tl)/(rho_g*hfg) (THMH2O.f:161-162), and PI does NOT
*  go to zero when the bulk reaches saturation, because TSCLAD is held at
*  TSAT+DSAT above the liquid temperature.  So the quality stays permanently
*  below the thermodynamic value and ENERGY IS NOT CONSERVED in the vapour
*  bookkeeping -- measured here as 7.3 % exit quality where the model's own
*  enthalpy rise demands 16 %.  Saha-Zuber is (F2+F3)/(1+F3) with
*  F2 = (h-hf)/hfg the thermodynamic quality and F3 vanishing as the bulk
*  heats (THMH2O.f:165), so it reverts to the energy balance.  An RBMK channel
*  exits at ~20 % quality, far past bulk boiling, so that is the regime that
*  matters.  Upstream's own FourChannels.x2m uses SAHA.
  SAHA
  DFM 0
{hgap_line}  ;

GREP: THER :: GETVAL 'MAX-T-FUEL' 1 >>tmaxf<< ;
ECHO "A7A FIT {FIT} PITCH {PITCH:.4f} MAXTFUEL" tmaxf ;

*  Everything the comparison needs, per axial node, straight out of the
*  channel's own directory (THM.f:943-945 builds HISTORY-DATA/TIMESTEP0000/
*  CHANNEL).  XFL is the flow quality, EPSILON the void fraction.
UTL: THER :: STEP UP 'HISTORY-DATA' STEP UP 'TIMESTEP0000'
             STEP UP 'CHANNEL' STEP AT 1
  IMPR XFL * IMPR EPSILON * IMPR COOLANT-TEMP * IMPR CENTER-TEMPS *
  IMPR VELOCITIES * IMPR DENSITY * IMPR PRESSURE * IMPR POWER *
  IMPR ENTHALPY * IMPR LIQUID-DENS * IMPR V-LIQ * IMPR V-VAP *
  IMPR PINLET * IMPR VINLET * IMPR POULET *
*  TEMPERATURES is the full radial profile, NDTOT points per axial node
*  (RODMESH <NFD> <NDTOT>): point 1 is the pellet centre, point NFD its
*  surface, point NFD+1 the clad inner face and point NDTOT the clad OUTER
*  face -- which is what THMDRV hands to the boiling correlation as
*  TRE11(NDTOT) (THMDRV.f:389).  So this one block carries every temperature
*  [D] p.95 quotes.
  IMPR TEMPERATURES * ;

ECHO "rbmk_a7a completed" ;
END: ;
QUIT .
"""
    over = [l for l in deck.splitlines() if len(l) > 120]
    assert not over, f"{len(over)} line(s) over 120 columns, first: {over[0][:90]!r}"
    open(OUT, "w").write(deck)
    open(OUT + ".access", "w").write("#!/bin/sh\n# no external data: the power is"
                                     " prescribed and there is no COMPO.\n")
    os.chmod(OUT + ".access", 0o755)
    print(f"wrote {os.path.relpath(OUT, ROOT)}")
    print(f"  real channel : A {A_FLOW:8.4f} cm2  Dh {D_H:7.4f} cm  "
          f"Pwet {P_WET:8.4f}  Pheat {P_HEAT:8.4f} cm")
    print(f"  CLUSTER {FIT:5s}: pitch {PITCH:7.4f} cm  A {A_MODEL:8.4f} "
          f"({100 * (A_MODEL / A_FLOW - 1):+6.1f} %)  Dh {DH_MODEL:7.4f} "
          f"({100 * (DH_MODEL / D_H - 1):+6.1f} %)")
    print(f"  prescribed   : {PCH_KW:.0f} kW, {MDOT * 3.6:.1f} t/h, "
          f"{P_OUT / KGF:.1f} kgf/cm2 out, {T_IN - 273.15:.0f} C in")
    # Linear rating is PER ROD, and it is a closure check on the sourced set
    # rather than an output: 3100 kW over 700 cm over 18 rods at peak 1.4 has
    # to land in [D]'s own 360-385 W/cm window, and nothing was adjusted to
    # make it.  If it did not, one of power / length / rod count would be wrong.
    q_peak = PCH_KW * 1000.0 * max(SHAPE) / (NZ * PITCH_Z * NPIN)
    print(f"  axial        : cosine half-width {C_HALF:.4f} rad, "
          f"peak/mean {max(SHAPE):.3f}")
    print(f"  CLOSURE      : peak linear rating {q_peak:.0f} W/cm per rod, "
          f"{q_peak * 1.07:.0f} with a 1.07 rod-to-rod factor,")
    print(f"                 against [D] p.95's 360-385 W/cm maximum. The "
          f"bare number sits just")
    print(f"                 below the window because a channel-average model "
          f"has no rod-to-rod")
    print(f"                 peaking in it; the closure is that power, length "
          f"and rod count")
    print(f"                 are mutually consistent to within that factor, "
          f"with nothing fitted.")


if __name__ == "__main__":
    main()
