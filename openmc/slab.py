#!/usr/bin/env python3
"""An independent check on the reflector strip: OpenMC on the same slabs.

WHY.  DRAGON transport says a 1 m block of fuel cells with one vacuum face has
k = 0.849336, while DONJON diffusion on DRAGON's OWN homogenised constants for
the same block says 1.191992.  Reflected, the two agree -- DRAGON reproduces
the cell k-inf to 3 pcm and DONJON to -459 pcm -- so the disagreement is
entirely about LEAKAGE, and it is a factor of 5.7 in the implied migration
area.  That is too large and too consequential to settle by arguing one
deterministic code against another, and standing rule 4 says not to try.

So: the same two slabs in OpenMC, continuous-energy Monte Carlo with no
homogenisation, no group structure and no diffusion approximation.

  reflected  must reproduce the fuel cell's k-inf, 1.313968 -- the control
             that says the OpenMC model is the same reactor
  vacuum     the number in dispute: ~0.85 (DRAGON) or ~1.19 (DONJON)

Whichever it lands on decides whether the reflector finding is "diffusion
cannot represent a free surface in this lattice", which is a real physics
limit, or "something is wrong with the strip", which is a bug to fix.
"""
import os
import sys

import openmc

import cps_common as cc
import rbmk_cell as rc

THREADS = int(os.environ.get("OMP_NUM_THREADS", "20"))


def slab(ncell=4, bc_out="vacuum", dca=0.72, graphite_tsl="c_Graphite_10p",
         particles=20_000, batches=150, inactive=30, seed=1):
    """ncell fuel cells in x; x- reflective, x+ `bc_out`, y and z reflective.

    x- reflective makes this the edge of an infinite core, which is what the
    DRAGON strip models.  Everything else -- cell geometry, materials,
    temperatures, thermal scattering -- comes from rbmk_cell, the same module
    the lattice and CPS work uses, so this cannot drift from them.
    """
    mats, m = rc.build_materials(dca, graphite_tsl)
    fuel_u = openmc.Universe(cells=rc.fuel_cells(m))
    lat = openmc.RectLattice()
    lat.pitch = (cc.PITCH, cc.PITCH)
    lat.lower_left = (0.0, -cc.PITCH / 2)
    lat.universes = [[fuel_u] * ncell]
    x0 = openmc.XPlane(0.0, boundary_type="reflective")
    x1 = openmc.XPlane(ncell * cc.PITCH, boundary_type=bc_out)
    ys = [openmc.YPlane(s * cc.PITCH / 2, boundary_type="reflective")
          for s in (-1, 1)]
    zs = [openmc.ZPlane(s * 0.5, boundary_type="reflective") for s in (-1, 1)]
    root = openmc.Cell(fill=lat,
                       region=+x0 & -x1 & +ys[0] & -ys[1] & +zs[0] & -zs[1])
    geom = openmc.Geometry(openmc.Universe(cells=[root]))
    st = openmc.Settings()
    st.run_mode, st.particles, st.batches = "eigenvalue", particles, batches
    st.inactive, st.seed = inactive, seed
    st.temperature = {"method": "interpolation", "range": (250.0, 2100.0)}
    st.source = openmc.IndependentSource(space=openmc.stats.Box(
        (0.0, -cc.PITCH / 2, -0.5), (ncell * cc.PITCH, cc.PITCH / 2, 0.5)))
    return openmc.Model(geometry=geom, materials=mats, settings=st)


def main():
    out = os.path.join(cc.ROOT, "openmc", "slab_runs")
    os.makedirs(out, exist_ok=True)
    print("reference: the fuel cell's own k-inf = 1.313968 (DRAGON, A3)")
    print("           DRAGON transport, 4 cells: 1.314007 reflected, "
          "0.849336 vacuum")
    print("           DONJON diffusion, 4 zones: 1.305690 reflected, "
          "1.191992 vacuum\n")
    for bc in ("reflective", "vacuum"):
        d = os.path.join(out, f"slab4_{bc}")
        os.makedirs(d, exist_ok=True)
        sp = slab(4, bc).run(cwd=d, threads=THREADS, output=False)
        with openmc.StatePoint(sp) as s:
            k = s.keff
        print(f"  OpenMC, 4 cells, x+ {bc:<10} k = {k.n:.6f} +/- {k.s:.6f}")


if __name__ == "__main__":
    main()
