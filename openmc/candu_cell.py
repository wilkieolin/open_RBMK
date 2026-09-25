"""
CANDU-6 cell in OpenMC -- the control for the RBMK void-coefficient comparison.

Geometry is twlup_proc/TCWU07.c2m verbatim (37-element cluster, 4 rings).
Compositions come from candu_common.py, which also generates the DRAGON
procedure rbmk_proc/CanduLib.c2m, so both codes see the same numbers.

The voided case follows TCWU07: the coolant becomes MIX 0, a true void, not
a low-density fluid.  In OpenMC that is a cell with fill=None.

Run:  python candu_cell.py <void 0|1> <outdir> [particles] [batches]
"""
import os
import sys
import numpy as np
import openmc
from candu_common import compositions, A

# TCWU07 geometry, cm
HALF_PITCH = 14.2875
R_COOL, R_PT, R_GAS, R_CT = 5.16890, 5.60320, 6.44780, 6.58750
R_PELLET, R_CLAD = 0.6122, 0.6540
RINGS = [(1, 0.0000, 0.0, 6), (6, 1.4885, 0.0, 7),
         (12, 2.8755, 0.261799, 8), (18, 4.3305, 0.0, 9)]

# OpenMC thermal scattering for the bound scatterers.  DLIB_99 has H2_D2O and
# H1_H2O but no bound oxygen in D2O, so oxygen is left free-gas in both codes.
SAB = {1: [("H2", "c_D_in_D2O"), ("H1", "c_H_in_H2O")],
       5: [("H2", "c_D_in_D2O"), ("H1", "c_H_in_H2O")]}


def build_materials():
    mats, byid = [], {}
    for mid, (T, nucs) in sorted(compositions().items()):
        m = openmc.Material(mid, f"mix{mid}")
        for nuc, n in sorted(nucs.items()):
            m.add_nuclide(nuc, n)
        for nuc, law in SAB.get(mid, []):
            if nuc in nucs:
                m.add_s_alpha_beta(law)
        m.temperature = T
        mats.append(m); byid[mid] = m
    return openmc.Materials(mats), byid


def build_geometry(m, void):
    xmin = openmc.XPlane(-HALF_PITCH, boundary_type="reflective")
    xmax = openmc.XPlane(+HALF_PITCH, boundary_type="reflective")
    ymin = openmc.YPlane(-HALF_PITCH, boundary_type="reflective")
    ymax = openmc.YPlane(+HALF_PITCH, boundary_type="reflective")
    zmin = openmc.ZPlane(-0.5, boundary_type="reflective")
    zmax = openmc.ZPlane(+0.5, boundary_type="reflective")
    box = +xmin & -xmax & +ymin & -ymax

    s_cool = openmc.ZCylinder(r=R_COOL)
    s_pt   = openmc.ZCylinder(r=R_PT)
    s_gas  = openmc.ZCylinder(r=R_GAS)
    s_ct   = openmc.ZCylinder(r=R_CT)

    cells, clads = [], []
    for npin, rpin, apin, fuel_mix in RINGS:
        for k in range(npin):
            th = apin + 2 * np.pi * k / npin
            x0, y0 = rpin * np.cos(th), rpin * np.sin(th)
            sp = openmc.ZCylinder(x0=x0, y0=y0, r=R_PELLET)
            sc = openmc.ZCylinder(x0=x0, y0=y0, r=R_CLAD)
            clads.append(sc)
            cells.append(openmc.Cell(fill=m[fuel_mix], region=-sp))
            cells.append(openmc.Cell(fill=m[10], region=+sp & -sc))

    cool_region = -s_cool
    for sc in clads:
        cool_region &= +sc
    # TCWU07's void case is MIX 0 -- an actual void, so fill=None
    cells.append(openmc.Cell(name="coolant",
                             fill=(None if void else m[1]),
                             region=cool_region))
    cells.append(openmc.Cell(fill=m[2], region=+s_cool & -s_pt))
    cells.append(openmc.Cell(fill=m[3], region=+s_pt & -s_gas))
    cells.append(openmc.Cell(fill=m[4], region=+s_gas & -s_ct))
    cells.append(openmc.Cell(fill=m[5], region=+s_ct & box))

    for c in cells:
        c.region = c.region & +zmin & -zmax
    return openmc.Geometry(openmc.Universe(cells=cells))


def make_model(void, particles=20_000, batches=150, inactive=30):
    mats, m = build_materials()
    model = openmc.Model(geometry=build_geometry(m, void), materials=mats)
    s = openmc.Settings()
    s.run_mode = "eigenvalue"
    s.particles, s.batches, s.inactive = particles, batches, inactive
    s.temperature = {"method": "interpolation", "range": (250.0, 1300.0)}
    s.source = openmc.IndependentSource(
        space=openmc.stats.Box((-4.5, -4.5, -0.5), (4.5, 4.5, 0.5)),
        constraints={"fissionable": True})
    s.output = {"tallies": False}
    model.settings = s
    return model


if __name__ == "__main__":
    void = bool(int(sys.argv[1])); out = sys.argv[2]
    p = int(sys.argv[3]) if len(sys.argv) > 3 else 20_000
    b = int(sys.argv[4]) if len(sys.argv) > 4 else 150
    sp = make_model(void, p, b).run(cwd=out, threads=int(os.environ.get("RBMK_THREADS", os.cpu_count())), output=False)
    with openmc.StatePoint(sp) as s:
        print(f"CANDURESULT void={int(void)} "
              f"k={s.keff.nominal_value:.6f} +/- {s.keff.std_dev:.6f}")
