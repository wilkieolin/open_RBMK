#!/usr/bin/env python3
"""
Build the Chernobyl Unit 4 channel map (A6d) by registering two independent
digitisations against each other:

  core_layout.xlsx          [D] Fig. 2.3 -- Leningrad-2's initial loading: the
                            core outline, and what sits at every one of its
                            1888 positions, including the rod TYPES.
  insag7_fig_II6_012230.csv INSAG-7 Fig. II-6 -- Unit 4 at 01:22:30: which
                            lattice sites hold a rod, and how deep each is.

    python tools/build_unit4_map.py     # -> sources/derived/unit4_channel_map.csv

THE REGISTRATION IS EXACT, AND IT IS THE EVIDENCE.  Every one of Fig. II-6's
223 sites lands on a rod-lattice site of Fig. 2.3, at a single offset, with
nothing left over on the Unit-4 side.  Two figures twelve years apart, of two
different reactors, digitised by different means (Fig. 2.3 by hand, Fig. II-6
by glyph detection) -- so each is now a check on the other.  What falls out:

  * Fig. II-6's 12 blank sites are Fig. 2.3's 12 ДКЭ(в) axial-detector
    channels.  All twelve, exactly.  That had been an inference; it is now a
    measurement.
  * Unit 4's 211 rods sit on Leningrad-2's 179 rod sites PLUS 32 sites that
    Leningrad-2 used for 27 additional absorbers, 4 unloaded channels and one
    fuel channel.  179 + 32 = 211 -- the second-stage rod count of INSAG-7
    p. 43, with no site left to guess at.
  * The totals close with nothing spare: 1888 positions = 223 rod-lattice
    sites + 1665, and 1665 = 1661 fuel channels + 4 start-up chambers, which
    are [PAV]'s and [D]'s own counts for Unit 4.

WHAT IS STILL AN ASSUMPTION.  Not WHICH sites hold rods -- that is measured --
but what TYPE the 32 extra rods are.  INSAG-7 p. 43 gives second-stage units
24 emergency (АЗ) and 24 shortened (УСП) rods against Leningrad-2's 21 and 21,
so at least 3 + 3 of the 32 are АЗ and УСП; the rest are manual (РР) by
elimination, which is what `EXTRA_TYPE` assumes.  The choice is recorded per
row in `type_source`, so A8's sensitivity can vary it.
"""
import collections
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_core_layout as rc

ROOT = rc.ROOT
FIG26 = os.path.join(ROOT, "sources", "derived", "insag7_fig_II6_012230.csv")
OUT = os.path.join(ROOT, "sources", "derived", "unit4_channel_map.csv")

# Leningrad-2 code -> our channel type
TYPE = {"H": "RR", "Q": "USP", "XO": "AR", "F": "AZ", "O": "AZOC",
        "X": "DKEV", "T": "KD", "D": "DP", "*": "EMPTY", "": "FUEL",
        "o": "FUEL"}   # fuel carrying a radial detector is fuel to the core model
ROD_CODES = {"H", "Q", "XO", "F", "O"}
# the 32 sites Leningrad-2 did not use for a rod: type assumed (see the header)
EXTRA_TYPE = "RR"


def lattice(grid):
    """The rod lattice of the Leningrad-2 map: 45-degree rotated, pitch 2*sqrt(2) cells."""
    spec = {k for k, v in grid.items()
            if not v["out"] and v["code"] in ROD_CODES | {"X", "T"}}
    (jp, off), _ = collections.Counter(
        (j % 2, (i - 2 * (j // 2)) % 4) for i, j in spec).most_common(1)[0]
    return {k for k, v in grid.items()
            if not v["out"] and k[1] % 2 == jp and (k[0] - 2 * (k[1] // 2)) % 4 == off}


def register(lat, sites):
    """The (di, dj) putting every Fig. II-6 site on a lattice site.  Sites are on
    half-steps (h, row); one h step is 2 cells, one row is 2 cells."""
    best = max(((sum((2 * h + di, 2 * r + dj) in lat for h, r, _, _ in sites), di, dj)
                for di in range(-10, 40) for dj in range(-10, 40)))
    n, di, dj = best
    assert n == len(sites), f"only {n} of {len(sites)} sites registered"
    return di, dj


def main():
    cols, rows, grid = rc.load()
    lat = lattice(grid)
    sites = [(int(r["h"]), int(r["row"]), r["kind"],
              None if r["depth_cm"] == "" else float(r["depth_cm"]))
             for r in csv.DictReader(open(FIG26))]
    di, dj = register(lat, sites)
    u4 = {(2 * h + di, 2 * r + dj): (kind, depth) for h, r, kind, depth in sites}

    out, tally = [], collections.Counter()
    for (i, j), cell in sorted(grid.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        if cell["out"]:
            continue
        l2 = TYPE[cell["code"]]
        kind, depth = u4.get((i, j), (None, None))
        if kind == "ROD":
            typ = l2 if cell["code"] in ROD_CODES else EXTRA_TYPE
            src = "Fig 2.3" if cell["code"] in ROD_CODES else "assumed (see header)"
        elif kind == "EMPTY":
            typ, src = "DKEV", "Fig 2.3 (DKE(v)) = Fig II-6 blank"
            assert l2 == "DKEV", f"Fig II-6 blank at {rows[j]}-{cols[i]} is {l2} in Fig 2.3"
        else:
            typ = "KD" if l2 == "KD" else "FUEL"      # Leningrad-2's absorbers and
            src = "Fig 2.3"                           # unloaded channels are fuel in U4
        tally[typ] += 1
        out.append(dict(row=rows[j], col=cols[i], i=i, j=j, type=typ,
                        depth_cm="" if depth is None else f"{depth:g}",
                        leningrad2=l2, type_source=src))
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)

    rods = sum(v for k, v in tally.items() if k in {"RR", "USP", "AR", "AZ", "AZOC"})
    print(f"registration offset (di, dj) = ({di}, {dj}); all {len(sites)} sites placed")
    print(f"{len(out)} positions -> {os.path.relpath(OUT, ROOT)}")
    for k, v in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"  {k:6s} {v:5d}")
    print(f"  rods total {rods}")
    # every count has an independent source; none is chosen to make these agree
    for name, got, want, src in (("rods", rods, 211, "INSAG-7 pp. 43, 103"),
                                 ("fuel channels", tally["FUEL"], 1661, "[PAV] Table 1"),
                                 ("DKE(v)", tally["DKEV"], 12, "[D] p. 57"),
                                 ("start-up chambers", tally["KD"], 4, "[D] p. 57"),
                                 ("positions", len(out), 1888, "sum of the above")):
        print(f"  {name:18s} {got:5d} vs {want:5d}  {'OK' if got == want else 'DIFF'}   {src}")
    ins = [r for r in out if r["depth_cm"] not in ("", "0")]
    print(f"  {len(ins)} rods inserted at 01:22:30, "
          f"{sum(float(r['depth_cm']) for r in ins):.0f} cm in total")


if __name__ == "__main__":
    main()
