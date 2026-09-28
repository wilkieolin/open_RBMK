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
  * PLACEHOLDER: the graphite reflector.  A reflector dataset is its own job
    (a 1-D core/reflector transport calculation, homogenised and SPH-corrected
    -- upstream's `Reflector_beavrs` case is the template).  Until that exists
    this deck carries a clearly-marked stand-in and **its k is not a physics
    result**.  The gate for this increment is the geometry, the fuel map and
    the solver, not the eigenvalue.
  * NOT YET HERE: the rods.  Every CPS channel is modelled as a full-height
    water column, i.e. all rods withdrawn.  Rods arrive as DEVINI:/DSET:
    devices once A6.4b's rod-cell equivalence lands, because a rod inserted
    with today's CPS data is 7-10 % short on worth.

SOLVER.  TRIVAT DUAL 1 1, not the MCFD 1 that A2 chose and TIER_A_WORKPLAN A2.3
still recommends.  Measured 2026-09-28: MCFD 1 loses 31-34 % of the absorber
worth on the A6.4 gate and cannot carry a converged SPH equivalence at all,
while DUAL 1 1 costs 8 % more wall clock (2.11 s vs 1.95 s) and 17 MB on this
same geometry, and the two agree to 0.7 pcm when no absorber is present.
"""
import csv
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", ".."))
MAP = os.path.join(ROOT, "sources", "derived", "unit4_channel_map.csv")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rbmk_unit4_core.don")

PITCH = 25.0            # cm, the lattice pitch ([D], closed in the A6.1 sources)
NREF = 2                # radial reflector, cells (50 cm) -- ASSUMPTION, see below
NZ_ACTIVE = 28          # 28 x 25 cm = 700 cm active height
NZ_REFL = 2             # axial graphite reflector, planes each end (50 cm)

# Mixtures.  1 is the only fuel mixture: every fuel channel draws from the same
# MULTICOMPO and is distinguished by what the fuel map carries for it.
M_FUEL, M_GRAPH, M_CPS = 1, 2, 3
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


def grid(g, ni, nj, cell, width=3):
    """One radial plane, as DONJON reads it: row j = nj-1 first (y decreasing)."""
    rows = []
    for j in range(nj + 2 * NREF - 1, -1, -1):
        row = [f"{cell(g.get((i - NREF, j - NREF))):>{width}d}"
               for i in range(ni + 2 * NREF)]
        rows.append(wrap(row))
    return "\n".join(rows)


def main():
    g, ni, nj = load()
    nx, ny = ni + 2 * NREF, nj + 2 * NREF
    nz = NZ_ACTIVE + 2 * NZ_REFL

    def core_mix(r):
        if r is None:
            return M_GRAPH
        return M_FUEL if r["type"] in FUEL_TYPES else M_CPS

    # the fuel map numbers only the fuel channels, 1..NCOMB, in the same raster
    # order the B-ZONE block is written in
    nfuel = 0
    num = {}
    for j in range(ny - 1, -1, -1):
        for i in range(nx):
            r = g.get((i - NREF, j - NREF))
            if r is not None and r["type"] in FUEL_TYPES:
                nfuel += 1
                num[(i, j)] = nfuel

    active = grid(g, ni, nj, core_mix)
    refl = grid(g, ni, nj, lambda r: M_GRAPH)
    fmap_active = grid(g, ni, nj, lambda r: M_FUEL if r is not None
                       and r["type"] in FUEL_TYPES else 0)
    fmap_refl = grid(g, ni, nj, lambda r: 0)
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
    nxname = "\n".join(wrap([lab(ci.get(i - NREF, "-")) for i in range(nx)],
                            indent="         ").splitlines()).lstrip()
    nyname = "\n".join(wrap([lab(rj.get(j - NREF, "-")) for j in range(ny - 1, -1, -1)],
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

    deck = f"""*----
*  CHERNOBYL UNIT 4 CORE (A6.5) -- GENERATED by decks/Donjon/data/gen_rbmk_unit4.py.
*  Edit the generator, not this file.
*
*  {nx} x {ny} x {nz} nodes at {PITCH:.0f} cm: {ni} x {nj} channel positions from
*  sources/derived/unit4_channel_map.csv, a {NREF}-cell radial graphite reflector,
*  {NZ_ACTIVE} active planes ({NZ_ACTIVE * PITCH:.0f} cm) and {NZ_REFL} reflector planes each end.
*
*  {nfuel} fuel channels (mix {M_FUEL}), {ncps} CPS/detector channels (mix {M_CPS}),
*  graphite elsewhere (mix {M_GRAPH}).  Counts asserted by the generator against
*  [PAV] Table 1 and INSAG-7 pp. 43/103.
*
*  THE REFLECTOR CROSS SECTIONS ARE A PLACEHOLDER (see the generator header).
*  The gate for this deck is that the geometry, the fuel map and the solver are
*  right and FLUD: converges -- NOT the eigenvalue.  Do not quote k from it.
*
*  All rods are withdrawn: every CPS channel is a full-height water column.
*----
LINKED_LIST GEOM GEO2 MATEX FMAP MACREF MACFUEL MACRO MACRO2
            TRACK SYSTEM FLUX POWER FCpo CCpo ;
SEQ_ASCII   _ACompo    :: FILE './_ACompo' ;
SEQ_ASCII   _CCompoWAT :: FILE './_CCompoWAT' ;
MODULE      GEO: MAC: USPLIT: RESINI: NCR: MACINI: TRIVAT: TRIVAA: FLUD:
            FLPOW: GREP: DELETE: END: ;
REAL keff ;

FCpo := _ACompo ;
CCpo := _CCompoWAT ;

*--- core geometry: one node per channel, VOID outside the reflector
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
  NGRP 2 MAXR {nx * ny * nz}
  NMIX {M_CPS} NREFL 2 RMIX {M_GRAPH} {M_CPS} NFUEL 1 FMIX {M_FUEL} ;

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

ECHO "UNIT4 geometry {nx} x {ny} x {nz}, {nfuel} fuel channels, {ncps} CPS channels" ;
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
                         'cp "$src"/_CCompoWAT . || exit 1\n')
    os.chmod(acc, 0o755)
    print(f"wrote {os.path.relpath(OUT, ROOT)}")
    print(f"  grid {nx} x {ny} x {nz} = {nx * ny * nz} nodes, "
          f"{nx * PITCH:.0f} x {ny * PITCH:.0f} x {nz * PITCH:.0f} cm")
    print(f"  {nfuel} fuel + {ncps} CPS = {len(g)} channels")


if __name__ == "__main__":
    main()
