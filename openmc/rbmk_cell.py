"""
RBMK-1000 lattice cell -- independent OpenMC model for cross-checking the
DRAGON5 deck 5.1/Dragon/data/rbmk_cell_a3.x2m.

The point of this file is to be an INDEPENDENT transport solution of the SAME
physical cell, so it deliberately copies the number densities and dimensions
from the DRAGON input and nothing else.  Geometry is rebuilt from the
dimension table in rbmk_cell_a3.x2m; compositions are the atom densities in
rbmk_proc/RbmkLib.c2m, verbatim.  Any difference in k-inf is then attributable
to method (deterministic 172-group Sn/CP vs continuous-energy Monte Carlo) and
to nuclear data (DLIB_99 vs ENDF/B-VIII.0), not to a different reactor.

Memory: continuous-energy data for ~15 nuclides at 2-4 temperatures, shared
across threads; a few GB resident.  No GPU allocation.  Nowhere near the
~110 GB ceiling on this machine.
"""
import numpy as np
import openmc

# ----------------------------------------------------------------------
# State point.  Defaults match the nominal case in rbmk_cell_a3.x2m.
# ----------------------------------------------------------------------
DCA_NOM = 0.72        # coolant density, g/cm3
T_FUEL  = 900.0       # K
T_GRAP  = 750.0       # K
T_COOL  = 573.0       # K
T_CLAD  = 600.0       # K   (MIX 8 is pinned at 600.0 in RbmkLib.c2m)

# ----------------------------------------------------------------------
# Geometry, cm.  Table from the header of rbmk_cell_a3.x2m.
# ----------------------------------------------------------------------
HALF_PITCH   = 12.5
R_CHANNEL    = 4.00    # coolant / pressure tube
R_PT_OUT     = 4.40    # pressure tube / gas clearance
R_GAS_OUT    = 4.55    # gas clearance / graphite rings
R_RINGS_OUT  = 5.70    # graphite rings / graphite block

# Carrier, corrected 2026-09-24 against Dollezhal & Emelyanov (1980) p.11:
# 18 rods on a CENTRAL TUBE of Zr "15 x 1.25 mm" (OD 15, ID 12.5); inside it
# "either a carrier rod of diameter 12 mm, or a carrier tube 12 x 2.5 mm".
# The solid 12 mm rod is the standard channel and is what is modelled.
R_CARR_ROD   = 0.600   # solid Zr carrier rod, 12 mm
R_CTUBE_IN   = 0.625   # central tube ID 12.5 mm  (0.25 mm water annulus)
R_CTUBE_OUT  = 0.750   # central tube OD 15 mm

# Fuel rod, corrected 2026-09-24 against the same page:
# clad OD 13.5 mm, wall 0.9 mm, pellet 11.5 mm.  Previously 13.6 x 0.825,
# which made the pellet-clad gap ~2.3x too thick.  Refined 2026-09-24 (3) to
# the drawing nominal 13.58 x ID 11.7 (dvoika.net RBMK page; LEI/SKB 2005);
# see sources/README.md and the rbmk_cell_a3.x2m header.
R_HOLE       = 0.1000  # 2 mm pellet hole -- confirmed [RU-A][LEI05][BIB]
R_PELLET     = 0.5750
R_GAP        = 0.5850
R_CLAD       = 0.6790

RING1_R, RING1_N, RING1_A = 1.60, 6,  0.0
RING2_R, RING2_N, RING2_A = 3.10, 12, 0.261799   # 15 deg, as APIN in the deck


def build_materials(dca=DCA_NOM, graphite_tsl="c_Graphite"):
    """Atom densities copied from rbmk_proc/RbmkLib.c2m (atom/b-cm)."""
    # MIX 1 -- channel coolant, H2O.  RbmkLib scales linearly with density.
    coolant = openmc.Material(1, "coolant H2O")
    coolant.add_nuclide("H1",  4.81360E-2 * dca / 0.72)
    coolant.add_nuclide("O16", 2.40680E-2 * dca / 0.72)
    coolant.add_s_alpha_beta("c_H_in_H2O")
    coolant.temperature = T_COOL

    # MIX 2 -- pressure tube, Zr-2.5%Nb at 6.55 g/cm3
    pt = openmc.Material(2, "pressure tube Zr-2.5Nb")
    for nuc, n in [("Zr90", 2.16890E-2), ("Zr91", 4.72990E-3),
                   ("Zr92", 7.22980E-3), ("Zr94", 7.32670E-3),
                   ("Zr96", 1.18040E-3), ("Nb93", 1.06140E-3)]:
        pt.add_nuclide(nuc, n)
    pt.temperature = T_COOL

    # MIX 3 -- He fill gas
    gas = openmc.Material(3, "He fill gas")
    gas.add_nuclide("He4", 1.28100E-5)
    gas.temperature = T_COOL

    # MIX 4 / MIX 5 -- graphite rings and block, 1.65 g/cm3.
    # DRAGON's C12_GR is all carbon treated as C-12; matched here on purpose
    # so the comparison isolates method and data, not composition.
    def graphite(mid, name):
        g = openmc.Material(mid, name)
        g.add_nuclide("C12", 8.27260E-2)
        # c_Graphite = perfect crystal.  DRAGON's C12_GR is reactor graphite
        # 10 % porosity (libraries/pynjoy/endfb8r1_apolib99_v5p1.py:77); pass
        # graphite_tsl="c_Graphite_10p" to compare on identical data (H1).
        g.add_s_alpha_beta(graphite_tsl)
        g.temperature = T_GRAP
        return g
    gr_ring  = graphite(4, "graphite rings")
    gr_block = graphite(5, "graphite block")

    # MIX 6 / MIX 7 -- UO2, 2.0 wt% U-235.  Two IDs because DRAGON needs
    # separate self-shielding sets; identical composition.
    def fuel(mid, name):
        f = openmc.Material(mid, name)
        f.add_nuclide("U235", 4.69750E-4)
        f.add_nuclide("U238", 2.27272E-2)
        f.add_nuclide("O16",  4.63940E-2)
        f.temperature = T_FUEL
        return f
    fuel_in  = fuel(6, "UO2 inner ring")
    fuel_out = fuel(7, "UO2 outer ring")

    # MIX 8 / MIX 9 -- Zr-1%Nb cladding and carrier rod
    def zr1nb(mid, name, temp):
        z = openmc.Material(mid, name)
        for nuc, n in [("Zr90", 2.20240E-2), ("Zr91", 4.80290E-3),
                       ("Zr92", 7.34120E-3), ("Zr94", 7.43970E-3),
                       ("Zr96", 1.19860E-3), ("Nb93", 4.24560E-4)]:
            z.add_nuclide(nuc, n)
        z.temperature = temp
        return z
    clad    = zr1nb(8, "clad Zr-1Nb",    T_CLAD)
    carrier = zr1nb(9, "carrier Zr-1Nb", T_COOL)

    mats = openmc.Materials([coolant, pt, gas, gr_ring, gr_block,
                             fuel_in, fuel_out, clad, carrier])
    return mats, dict(coolant=coolant, pt=pt, gas=gas, gr_ring=gr_ring,
                      gr_block=gr_block, fuel_in=fuel_in, fuel_out=fuel_out,
                      clad=clad, carrier=carrier)


def rod_positions():
    """Centres of the 18 fuel rods, matching NPIN/RPIN/APIN in the deck."""
    inner = [(RING1_R * np.cos(RING1_A + 2*np.pi*k/RING1_N),
              RING1_R * np.sin(RING1_A + 2*np.pi*k/RING1_N))
             for k in range(RING1_N)]
    outer = [(RING2_R * np.cos(RING2_A + 2*np.pi*k/RING2_N),
              RING2_R * np.sin(RING2_A + 2*np.pi*k/RING2_N))
             for k in range(RING2_N)]
    return inner, outer


def build_geometry(m, boundary="reflective"):
    """CARCEL 5 + CLUSTER CARR/ROD1/ROD2, as a 2-D infinite lattice."""
    # Outer square, reflective on all four sides; z reflective => infinite axially
    # Side faces only: "white" reproduces DRAGON's TISO tracking, which applies
    # isotropic reflection (NXTTCG.f:464) -- hypothesis H2.  z stays specular so
    # the model remains strictly 2-D, as DRAGON's is.
    xmin = openmc.XPlane(-HALF_PITCH, boundary_type=boundary)
    xmax = openmc.XPlane(+HALF_PITCH, boundary_type=boundary)
    ymin = openmc.YPlane(-HALF_PITCH, boundary_type=boundary)
    ymax = openmc.YPlane(+HALF_PITCH, boundary_type=boundary)
    zmin = openmc.ZPlane(-0.5, boundary_type="reflective")
    zmax = openmc.ZPlane(+0.5, boundary_type="reflective")
    box = +xmin & -xmax & +ymin & -ymax & +zmin & -zmax

    s_chan  = openmc.ZCylinder(r=R_CHANNEL)
    s_pt    = openmc.ZCylinder(r=R_PT_OUT)
    s_gas   = openmc.ZCylinder(r=R_GAS_OUT)
    s_rings = openmc.ZCylinder(r=R_RINGS_OUT)
    s_rod   = openmc.ZCylinder(r=R_CARR_ROD)
    s_ci    = openmc.ZCylinder(r=R_CTUBE_IN)
    s_co    = openmc.ZCylinder(r=R_CTUBE_OUT)

    cells = []

    # Carrier assembly at the cell centre: solid 12 mm Zr rod, a 0.25 mm water
    # annulus, then the 15 x 1.25 mm central tube the spacer grids sit on.
    c = openmc.Cell(name="carrier rod", fill=m["carrier"], region=-s_rod)
    cells.append(c)
    c = openmc.Cell(name="carrier annulus", fill=m["coolant"],
                    region=+s_rod & -s_ci)
    c.temperature = T_COOL
    cells.append(c)
    c = openmc.Cell(name="central tube", fill=m["carrier"],
                    region=+s_ci & -s_co)
    cells.append(c)

    # Fuel rods
    inner, outer = rod_positions()
    rod_outer_surfs = []
    for idx, (pos, fuel_mat) in enumerate(
            [(p, m["fuel_in"]) for p in inner] +
            [(p, m["fuel_out"]) for p in outer]):
        x0, y0 = pos
        sh = openmc.ZCylinder(x0=x0, y0=y0, r=R_HOLE)
        sp = openmc.ZCylinder(x0=x0, y0=y0, r=R_PELLET)
        sg = openmc.ZCylinder(x0=x0, y0=y0, r=R_GAP)
        sc = openmc.ZCylinder(x0=x0, y0=y0, r=R_CLAD)
        rod_outer_surfs.append(sc)
        cells.append(openmc.Cell(name=f"hole{idx}",   fill=m["gas"],   region=-sh))
        cells.append(openmc.Cell(name=f"pellet{idx}", fill=fuel_mat,   region=+sh & -sp))
        cells.append(openmc.Cell(name=f"gap{idx}",    fill=m["gas"],   region=+sp & -sg))
        cells.append(openmc.Cell(name=f"clad{idx}",   fill=m["clad"],  region=+sg & -sc))

    # Coolant: inside the channel, outside the carrier and every rod
    cool_region = -s_chan & +s_co
    for sc in rod_outer_surfs:
        cool_region &= +sc
    c = openmc.Cell(name="coolant", fill=m["coolant"], region=cool_region)
    c.temperature = T_COOL
    cells.append(c)

    # Annuli outside the channel
    cells.append(openmc.Cell(name="pressure tube", fill=m["pt"],
                             region=+s_chan & -s_pt))
    cells.append(openmc.Cell(name="gas clearance", fill=m["gas"],
                             region=+s_pt & -s_gas))
    cells.append(openmc.Cell(name="graphite rings", fill=m["gr_ring"],
                             region=+s_gas & -s_rings))
    # MIX 5 fills everything from the rings out to the square (the deck's
    # r=11.0 surface separates two identical graphite regions, so it is
    # omitted here -- it cannot affect the transport solution).
    cells.append(openmc.Cell(name="graphite block", fill=m["gr_block"],
                             region=+s_rings & box))

    # Bound the inner cells axially and laterally
    for c in cells[:-1]:
        c.region = c.region & +zmin & -zmax

    return openmc.Geometry(openmc.Universe(cells=cells))


def make_model(dca=DCA_NOM, particles=50_000, batches=150, inactive=30,
               seed=1, graphite_tsl="c_Graphite", boundary="reflective"):
    mats, m = build_materials(dca, graphite_tsl)
    geom = build_geometry(m, boundary)

    settings = openmc.Settings()
    settings.run_mode = "eigenvalue"
    settings.particles = particles
    settings.batches = batches
    settings.inactive = inactive
    settings.seed = seed
    # 573 K and 750 K fall between library temperatures, so interpolate
    # rather than snapping to the nearest grid point.
    settings.temperature = {"method": "interpolation",
                            "range": (250.0, 1300.0)}
    settings.source = openmc.IndependentSource(
        space=openmc.stats.Box((-3.5, -3.5, -0.5), (3.5, 3.5, 0.5)),
        constraints={"fissionable": True})
    settings.output = {"tallies": False}

    return openmc.Model(geometry=geom, materials=mats, settings=settings)


if __name__ == "__main__":
    make_model().export_to_model_xml("model.xml")
    print("wrote model.xml")
