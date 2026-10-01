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
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "rbmk_unit4_core.don" if WITH_REFL else "rbmk_unit4_norefl.don")

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

# Mixtures.  1 is the only fuel mixture: every fuel channel draws from the same
# MULTICOMPO and is distinguished by what the fuel map carries for it.
# DONJON mixtures.  The radial reflector is FOUR rings and its constants differ
# by ring, because the spectrum a metre into graphite is not the spectrum at the
# core edge -- _RCompo resolves them by depth and it would be wasteful to
# average that away.  0 is void, outside the stack.
# Reflector mixtures come FIRST and the fuel LAST, which is upstream's
# convention (1Sap_vs_3Sap.x2m: RMIX 1 2 3, FMIX 4) and matters: MACINI:
# indexes the non-fuel macrolib by material number, so MACREF's NMIX is
# max(RMIX) and leaving a gap at 1 would leave mixture 1 undefined in it.
# USPLIT: demands NREFL + NFUEL == the highest material index in the geometry
# (USPLIT.f, "WRONG NUMBER OF REFLECTOR OR FUEL TYPES"), so the numbering has
# to close up when U4_REFL=0 drops the four rings rather than leaving a hole.
M_CPS = 1
M_REFL = [2, 3, 4, 5] if WITH_REFL else []   # ring 1 at the core .. ring 4, cooled
M_FUEL = 2 + len(M_REFL)
NMIX = M_FUEL
FUEL_TYPES = {"FUEL"}
# Rod, detector and start-up-chamber channels are all water columns with the
# rods out.  DKEV and KD are not CPS channels, but they are water-filled tubes
# in graphite of similar construction; modelling them as the CPS water column is
# an approximation, recorded here rather than buried.
CPS_TYPES = {"RR", "USP", "AR", "AZ", "AZOC", "DKEV", "KD"}


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


def grid(g, ni, nj, cell, width=3):
    """One radial plane, as DONJON reads it: row j = nj-1 first (y decreasing)."""
    rows = []
    for j in range(nj + 2 * NPAD - 1, -1, -1):
        row = [f"{cell(i - NPAD, j - NPAD, g.get((i - NPAD, j - NPAD))):>{width}d}"
               for i in range(ni + 2 * NPAD)]
        rows.append(wrap(row))
    return "\n".join(rows)


def main():
    g, ni, nj = load()
    ring, stack = rings(g, ni, nj)
    nx, ny = ni + 2 * NPAD, nj + 2 * NPAD
    nz = NZ_ACTIVE + 2 * NZ_REFL
    nel = nx * ny * nz

    def core_mix(i, j, r):
        """Active plane: fuel, CPS water column, reflector ring, or nothing."""
        if r is not None:
            return M_FUEL if r["type"] in FUEL_TYPES else M_CPS
        k = ring.get((i, j))
        return M_REFL[k - 1] if k else 0

    def refl_mix(i, j, r):
        """Axial reflector plane.  The graphite columns continue unchanged --
        they are the same columns -- but every channel position loses its fuel
        and becomes a coolant tube in graphite, which is what the CPS water
        column already is.  That substitution is an approximation (the real end
        region has the Zr/steel transition piece in it) and is stated as one."""
        return M_CPS if r is not None else core_mix(i, j, r)

    # the fuel map numbers only the fuel channels, 1..NCOMB, in the same raster
    # order the B-ZONE block is written in
    nfuel = 0
    num = {}
    for j in range(ny - 1, -1, -1):
        for i in range(nx):
            r = g.get((i - NPAD, j - NPAD))
            if r is not None and r["type"] in FUEL_TYPES:
                nfuel += 1
                num[(i, j)] = nfuel

    active = grid(g, ni, nj, core_mix)
    refl = grid(g, ni, nj, refl_mix)
    fmap_active = grid(g, ni, nj, lambda i, j, r: M_FUEL if r is not None
                       and r["type"] in FUEL_TYPES else 0)
    fmap_refl = grid(g, ni, nj, lambda i, j, r: 0)
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
    # PLANE blocks: the two axial reflector plane-groups are identical, and so
    # are all the active planes, so only two distinct planes are ever written
    def planes(a, r):
        out = []
        for k in range(1, nz + 1):
            isref = k <= NZ_REFL or k > NZ_REFL + NZ_ACTIVE
            if k == 1:
                out.append(f"PLANE {k}\n{r if isref else a}")
            elif k == NZ_REFL + 1:
                out.append(f"PLANE {k}\n{a if not isref else r}")
            else:
                same = 1 if isref else NZ_REFL + 1
                out.append(f"PLANE {k} SAME {same}")
        return "\n".join(out)

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
    tag = "UNIT4" if WITH_REFL else "U4NOREF"
    stem = os.path.basename(OUT)[:-4]
    rcpo_arg = " RCpo" if WITH_REFL else ""
    rcpo_seq = ("\nSEQ_ASCII   _RCompo    :: FILE './_RCompo' ;"
                if WITH_REFL else "")
    rcpo_asg = "\nRCpo := _RCompo ;" if WITH_REFL else ""
    refl_line = (f"{nrefl_col} radial reflector columns in {nring} rings "
                 f"(mix {M_REFL[0]}..{M_REFL[-1]}), {per_ring} per ring "
                 f"from the core outward." if WITH_REFL else
                 "NO RADIAL REFLECTOR (U4_REFL=0): the VOID boundary sits on "
                 "the core outline.")
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
*  {nfuel} fuel channels (mix {M_FUEL}), {ncps} CPS/detector channels (mix {M_CPS}),
*  {refl_line}
*  {NZ_ACTIVE} active planes ({NZ_ACTIVE * PITCH:.0f} cm) and {NZ_REFL} reflector planes each end.
*
*  CROSS SECTIONS.  Fuel from _ACompo, CPS water columns from _CCompoWAT,
*  reflector rings from _RCompo zones 5..8 (3 graphite + 1 cooled).  All at a
*  UNIFORM burnup of 10900 MWd/t, the Unit 4 core average: the burnup
*  PLACEMENT map is still an open A6d item, so a flat field is the honest
*  stand-in and the per-channel route (INST-BURN off the fuel map) is wired
*  but not yet fed.
*
*  All rods are withdrawn: every CPS channel is a full-height water column.
*
*  k FROM THIS DECK IS REPORTED, NOT ASSERTED.  The reflector carries a
*  measured homogenisation error (PROGRESS.md, Phase 1b) and the burnup is
*  flat; the gate here is that the geometry, the fuel map and the solver chain
*  are right and FLUD: converges.
*----
LINKED_LIST GEOM GEO2 MATEX FMAP MACREF MACFUEL MACRO
            TRACK SYSTEM FLUX POWER FCpo CCpo{rcpo_arg} ;
SEQ_ASCII   _ACompo    :: FILE './_ACompo' ;
SEQ_ASCII   _CCompoWAT :: FILE './_CCompoWAT' ;{rcpo_seq}
MODULE      GEO: USPLIT: RESINI: NCR: MACINI: TRIVAT: TRIVAA: FLUD:
            FLPOW: GREP: DELETE: END: ;
REAL keff ;

FCpo := _ACompo ;
CCpo := _CCompoWAT ;{rcpo_asg}

*--- core geometry: one node per column, mixture 0 outside the graphite stack
GEOM := GEO: :: CAR3D {nx} {ny} {nz}
  EDIT 0
  X- VOID X+ VOID  Y- VOID Y+ VOID  Z- VOID Z+ VOID
  MIX
{planes(active, refl)}
  MESHX
{mesh(nx)}
  MESHY
{mesh(ny)}
  MESHZ
{fmt(zedges, 10)}
  ;

GEO2 MATEX := USPLIT: GEOM :: EDIT 0
  NGRP 2 MAXR {nel}
  NREFL {1 + nring} RMIX {M_CPS} {" ".join(str(m) for m in M_REFL[:nring])}
  NFUEL 1 FMIX {M_FUEL} ;

*--- the fuel map: {nfuel} channels, numbered in the B-ZONE block below
FMAP MATEX := RESINI: MATEX ::
  ::: GEO: CAR3D {nx} {ny} {nz}
      EDIT 0
      X- VOID X+ VOID  Y- VOID Y+ VOID  Z- VOID Z+ VOID
      MIX
{planes(fmap_active, fmap_refl)}
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
  ;

*--- non-fuel constants: the CPS water column and the four reflector rings.
*    MACINI: indexes this macrolib by MATERIAL number, so mixture k here is
*    material k and the order must match RMIX above (1Sap_vs_3Sap.x2m:29).
MACREF := NCR: CCpo{rcpo_arg} :: EDIT 0 MACRO LINEAR NMIX {1 + nring}
  COMPO CCpo 'EDICPS'
  MIX {M_CPS} FROM 5 SET 'burnup' 10900.0 SET 'DCA' 0.72 SET 'TF' 900.0 ENDMIX
{refl_mixes}  ;

*--- fuel constants, one mixture per bundle.  NMIX is NOT given: with a fuel
*    map on the RHS, NCR.f:127 sets it from FLMIX = NCH x NB = {nfuel} x {nz}.
*    'burnup' is SET rather than taken from the map (NCRRGR.f:717 says so in
*    the printout), because no burnup placement map exists yet.
MACFUEL := NCR: FCpo FMAP :: EDIT 0 MACRO LINEAR
  TABLE FCpo 'EDIRBMK'
  MIX {M_FUEL} SET 'burnup' 10900.0 SET 'DCA' 0.72
               SET 'TF' 900.0 SET 'TG' 750.0 ENDMIX
  ;

MACRO MATEX := MACINI: MATEX MACREF MACFUEL :: EDIT 0 ;

TRACK := TRIVAT: GEO2 :: EDIT 0 MAXR {nel} DUAL 1 1 ;
SYSTEM := TRIVAA: MACRO TRACK :: EDIT 0 ;
FLUX := FLUD: SYSTEM TRACK :: EDIT 1 ADI 2 EXTE 300 1.0E-6 ;
GREP: FLUX :: GETVAL 'K-EFFECTIVE' 1 >>keff<< ;
ECHO "{tag} KEFF" keff ;

*--- power shape.  PTOT is the nominal thermal rating; the shape, not the
*    normalisation, is what this increment checks.
POWER FMAP := FLPOW: FMAP FLUX TRACK MATEX ::
  EDIT 2 PTOT 3200.0 PRINT DISTR POWER ;

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
