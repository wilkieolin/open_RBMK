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
_BSFX = "" if _BURN0 == "flat" else "_b" + _BURN0
_STEM = ("rbmk_unit4_core" if WITH_REFL else "rbmk_unit4_norefl") + (
    "" if _RODS0 == "wat" else "_" + _RODS0) + (
    "" if _TILT0 == "0" else "_t" + _TILT0) + (
    "" if _DCA0 == "0.72" else "_d" + _DCA0.replace(".", "")) + _BSFX
if WITH_THM:
    _STEM = ("rbmk_unit4_a7" + ("" if _RODS0 == "wat" else "_" + _RODS0)
             + ("" if FLOW == "prop" else "_" + FLOW)
             + ("" if os.environ.get("U4_VOIDFB", "1") != "0" else "_nvf")
             + _BSFX)
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
NMIX = M_FUEL
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

if RODS == "wat":
    RODCOL = [_W] * NZ_ACTIVE
elif RODS in HALVES:
    RODCOL = HALVES[RODS]
elif RODS in NAMED:
    RODCOL = stack(NAMED[RODS])
elif RODS.startswith("d") and RODS[1:].isdigit():
    RODCOL = stack(int(RODS[1:]))
else:
    raise SystemExit(f"U4_RODS={RODS!r}: expected wat, d<n>, or one of "
                     f"{sorted(set(NAMED) | set(HALVES))}")

# U4_TILT inserts the 36 AZOC channels n planes from the top, as their own
# bank.  It exists to tilt the axial flux downward, because the displacer
# sweep's SIGN depends on the tilt and nothing else in this deck provides one:
# the burnup is flat and there is no xenon.  A partially-inserted scram bank
# is a real configuration, but THIS pattern is not the 01:23 pattern and is
# not offered as one.
BANKCOL = stack(TILT) if TILT else [_W] * NZ_ACTIVE


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
BURNSEED = int(os.environ.get("U4_BURNSEED", "20260404"))


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
    elif BURNMAP == "edge":
        order = sorted(cells, key=lambda c: rad[c])
        pool.sort()                             # freshest nearest the centre
        why = "freshest fuel in the middle, most-burnt at the edge"
    else:
        raise SystemExit(f"U4_BURNMAP={BURNMAP!r} is not one of "
                         "flat|rand|cent|edge|ring")
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
        if not active:
            # Above and below the core the graphite columns continue unchanged,
            # but every channel loses its fuel and becomes a coolant tube in
            # graphite, which is what the CPS water column already is.  An
            # approximation: the real end region holds the Zr/steel transition
            # piece.  Rods are not tracked outside the active core.
            return M_WAT
        if r["type"] in FUEL_TYPES:
            return M_FUEL
        if r["type"] in ROD_DSP:
            return M_OF[RODCOL[k - NZ_REFL - 1]]
        if r["type"] in ROD_BANK:
            return M_OF[BANKCOL[k - NZ_REFL - 1]]
        return M_WAT

    def fmap_mix(i, j, k, r):
        active = NZ_REFL < k <= NZ_REFL + NZ_ACTIVE
        return M_FUEL if (active and r is not None
                          and r["type"] in FUEL_TYPES) else 0

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

    if BURNMAP == "flat":
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
    _bkey = " 'burnup'" if BURNMAP != "flat" else ""
    _bmix = "INST-BURN" if BURNMAP != "flat" else "SET 'burnup' 10900.0"
    NCRFUEL = """MACFUEL := NCR: FCpo FMAP :: EDIT 0 MACRO LINEAR
  TABLE FCpo 'EDIRBMK'%s
  MIX %d %s%s ENDMIX
  ;""" % (_bkey, M_FUEL, _bmix, "" if WITH_THM else
          "\n               SET 'DCA' %s SET 'TF' 900.0 SET 'TG' 750.0" % DCA_SET)
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
            vel = [V_REF * q / P_REF for q in pw]
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
            vbar = V_REF * (sum(pw) / len(pw)) / P_REF
            speed = f"  SPEED {vbar:.4f}"
            flowdoc = (f"*  U4_FLOW=unif: one velocity everywhere, {vbar:.4f} m/s, the core-average\n"
                       f"*  of the same normalisation.  No valving at all, so the hot channels\n"
                       f"*  boil much harder than the cold ones -- the other end of the bracket.\n")
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
  SYSTEM := TRIVAA: MACRO TRACK :: EDIT 0 ;
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
  MACFUEL MACRO SYSTEM FLUX POWER := DELETE:
    MACFUEL MACRO SYSTEM FLUX POWER ;
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
SYSTEM := TRIVAA: MACRO TRACK :: EDIT 0 ;
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
ECHO "{tag} TMAXFUEL" tmaxf "DCOOL" dmin dmax ;"""
    else:
        solver = f"""{NCRFUEL}

MACRO MATEX := MACINI: MATEX MACREF MACFUEL :: EDIT 0 ;

TRACK := TRIVAT: GEO2 :: EDIT 0 MAXR {nel} DUAL 1 1 ;
SYSTEM := TRIVAA: MACRO TRACK :: EDIT 0 ;
FLUX := FLUD: SYSTEM TRACK :: EDIT 1 ADI 2 EXTE 300 1.0E-6 ;
GREP: FLUX :: GETVAL 'K-EFFECTIVE' 1 >>keff<< ;
ECHO "{tag} KEFF" keff ;"""

    refl_line = (f"{nrefl_col} radial reflector columns in {nring} rings "
                 f"(mix {M_REFL[0]}..{M_REFL[-1]}), {per_ring} per ring "
                 f"from the core outward." if WITH_REFL else
                 "NO RADIAL REFLECTOR (U4_REFL=0): the VOID boundary sits on "
                 "the core outline.")
    ther_obj = " THER" if WITH_THM else ""
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
LINKED_LIST GEOM GEO2 MATEX FMAP MACREF MACFUEL MACRO
            TRACK SYSTEM FLUX POWER{ther_obj} FCpo CCpo ACpo DCpo{rcpo_arg} ;
SEQ_ASCII   _ACompo    :: FILE './_ACompo' ;
SEQ_ASCII   _CCompoWAT :: FILE './_CCompoWAT' ;
SEQ_ASCII   _CCompoABS :: FILE './_CCompoABS' ;
SEQ_ASCII   _CCompoDSP :: FILE './_CCompoDSP' ;{rcpo_seq}
MODULE      GEO: USPLIT: RESINI: NCR: MACINI: TRIVAT: TRIVAA: FLUD:
            FLPOW:{thm_mod} UTL: GREP: DELETE: END: ;
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
  NFUEL 1 FMIX {M_FUEL} ;

*--- the fuel map: {nfuel} channels, numbered in the B-ZONE block below
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
  EDIT 2 PTOT 3200.0 PRINT DISTR POWER ;

*--- the {nfuel} channel powers in CHANNEL ORDER -- the order RESPFM.f:74-82
*    finds them, which is the order B-ZONE above is written in and the order
*    THMINP reads a per-channel list in.  A7b sets each channel's coolant flow
*    from its power, so this is the handover and it has to be the flat list
*    rather than the radial-plane table FLPOW: prints.
UTL: POWER :: IMPR POWER-CHAN * ;

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
                         'cp "$src"/_ACompo . || exit 1\n'
                         'cp "$src"/_CCompoWAT . || exit 1\n'
                         'cp "$src"/_CCompoABS . || exit 1\n'
                         'cp "$src"/_CCompoDSP . || exit 1\n'
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
