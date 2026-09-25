"""
RBMK Safety Review Project (1994) single-cell benchmark -- shared specification.

Source: Alexeev et al., Nucl. Eng. Des. 183 (1998) 287, Tables 3 and 4
([ALX98] in sources/README.md), which reproduce the cell defined by the RBMK
Safety Review Project, topic group 3 (1994).  Published answers from two
independent Monte Carlo codes (MCNP4A, MCU-3) and four deterministic codes are
in [ALX98] Figs 8-9, transcribed in PUBLISHED below.

WHY
This is a cell somebody else specified, with somebody else's Monte Carlo
answers.  Modelling it in both our codes tests (1) whether our OpenMC setup
reproduces two independent Monte Carlo codes, and (2) whether the DRAGON
settings that converged toward OpenMC on our own cell (METHOD_CONVERGENCE_
PLAN.md) close the gap here too -- neither step uses the historical outcome.

This module is the ONE transcription of Tables 3-4.  It builds the OpenMC
model and emits the DRAGON decks (decks/Dragon/data/rbmk_srp94_*.x2m), so a
transcription error lands in both codes identically.

ASSUMPTIONS [ALX98] does not settle (each stated, none tuned):
  T      "cold": every material at 300 K (the temperature Parisi & D'Auria
         2007 use for the same kind of cell).
  VOID   "voided": the water's H and O removed; the grid-spacer steel that
         Table 4 homogenises into the coolant (Cr, Fe, Ni) is kept, since the
         spacers do not boil away.
  ROTATE the rod rings' angular phase is not given; our own cell's (inner on
         the axes, outer offset pi/12) is used.
  ELEMENT Table 4 gives Zr, Nb, Hf, Cr, Fe, Ni as elements; they are split by
         natural isotopic abundance.  Graphite is C-12 only, as tabulated.
Table 3 already omits the pellet-clad gap and the pellet hole, and folds the
graphite gaps into the graphite density -- those are the benchmark's own
simplifications and are kept.
"""
import math

# --- Table 3, dimensions (cm) ------------------------------------------------
HALF_PITCH = 12.5
R_TUBE_IN, R_TUBE_OUT = 4.0, 4.4
R_CPIN = 0.75
R_RING1, R_RING2 = 1.6, 3.1
R_PELLET = 0.5915          # = clad inner radius: no gap
R_CLAD = 0.6815
N1, N2 = 6, 12
A1, A2 = 0.0, math.pi / 12
T = 300.0                  # ASSUMPTION "cold"

# natural isotopic abundances (atom fraction)
NAT = {
    "Zr": {"Zr90": 0.5145, "Zr91": 0.1122, "Zr92": 0.1715, "Zr94": 0.1738, "Zr96": 0.0280},
    "Hf": {"Hf174": 0.0016, "Hf176": 0.0526, "Hf177": 0.1860, "Hf178": 0.2728,
           "Hf179": 0.1362, "Hf180": 0.3508},
    "Cr": {"Cr50": 0.04345, "Cr52": 0.83789, "Cr53": 0.09501, "Cr54": 0.02365},
    "Fe": {"Fe54": 0.05845, "Fe56": 0.91754, "Fe57": 0.02119, "Fe58": 0.00282},
    "Ni": {"Ni58": 0.680769, "Ni60": 0.262231, "Ni61": 0.011399, "Ni62": 0.036345,
           "Ni64": 0.009256},
    "Nb": {"Nb93": 1.0},
}


def _expand(elems):
    out = {}
    for name, n in elems.items():
        if name in NAT:
            for iso, f in NAT[name].items():
                out[iso] = out.get(iso, 0.0) + n * f
        else:
            out[name] = out.get(name, 0.0) + n
    return out


def compositions(tube="Zr", watered=True):
    """{mix: {nuclide: atom/b-cm}} -- Table 4 of [ALX98], verbatim."""
    zralloy_tube = {"Zr": 3.3900e-2, "Nb": 6.2845e-4, "Hf": 1.0400e-5}
    cool = {"Cr": 1.3500e-4, "Fe": 4.8170e-4, "Ni": 6.6500e-5}      # spacers
    if watered:
        cool.update({"H1": 6.6366e-2, "O16": 3.3183e-2})
    fuel = {"O16": 4.2502e-2, "U235": 4.3049e-4, "U238": 2.0820e-2}
    return {
        1: _expand(cool),                                            # coolant
        2: _expand(zralloy_tube if tube == "Zr" else {"Al27": 5.9784e-2}),
        3: {"C12": 8.5075e-2, "B10": 1.8000e-8},                     # graphite
        4: _expand({"Zr": 3.3900e-2, "Nb": 6.2845e-4, "Hf": 1.0400e-5}),  # central pin
        5: _expand({"Zr": 4.3352e-2, "Nb": 8.0365e-4, "Hf": 1.3340e-5}),  # clad
        6: dict(fuel),                                               # fuel, inner ring
        7: dict(fuel),                                               # fuel, outer ring
    }


# [ALX98] Figs 8-9, read off the plots (+-0.001 in k, +-0.02 in dk; error bars 3 sigma).
# void effect is dk * 100 = (k_voided - k_watered) * 100, as the paper plots it.
PUBLISHED = [
    # code, library, tube, k_watered, k_voided, dk%
    ("MCNP4A", "ENDF/B-IV",     "Zr", 1.2781, 1.3211, 4.29),
    ("MCNP4A", "B-IV+VI",       "Zr", 1.2807, 1.3254, 4.47),
    ("MCNP4A", "ENDF/B-VI/L",   "Zr", 1.2778, 1.3263, 4.85),
    ("MCNP4A", "ENDF/B-VI/B",   "Zr", 1.2806, 1.3285, 4.81),
    ("MCU-3",  "3lib",          "Zr", 1.2800, 1.3280, 4.80),
    ("MCNP4A", "ENDF/B-VI/L",   "Al", 1.2714, 1.3247, 5.33),
    ("MCNP4A", "ENDF/B-VI/B",   "Al", 1.2725, 1.3254, 5.28),
    ("MCU-3",  "3lib",          "Al", 1.2740, 1.3283, 5.43),
    ("MCU-3",  "2lib",          "Al", 1.2733, 1.3280, 5.47),
    ("MONK-5W", "WIMS86",       "Al", 1.2838, 1.3310, 4.72),
    ("WIMS-E", "WIMS86",        "Al", 1.2884, 1.3355, 4.71),
    ("WIMS-D", "WIMS86",        "Al", 1.2925, 1.3371, 4.45),
    ("APOLLO-2", "CEA86",       "Al", 1.2946, 1.3404, 4.57),
]


# --- OpenMC ------------------------------------------------------------------
def openmc_model(tube="Zr", watered=True, particles=50_000, batches=300,
                 inactive=50, seed=1, graphite_tsl="c_Graphite"):
    import openmc
    comp = compositions(tube, watered)
    names = {1: "coolant", 2: f"tube {tube}", 3: "graphite", 4: "central pin",
             5: "clad", 6: "fuel inner", 7: "fuel outer"}
    mats = {}
    for mid, nucs in comp.items():
        m = openmc.Material(mid, names[mid])
        for n, d in nucs.items():
            if d > 0:
                m.add_nuclide(n, d)
        m.set_density("sum")
        m.temperature = T
        mats[mid] = m
    if watered:
        mats[1].add_s_alpha_beta("c_H_in_H2O")
    mats[3].add_s_alpha_beta(graphite_tsl)

    xs = [openmc.XPlane(s * HALF_PITCH, boundary_type="reflective") for s in (-1, 1)]
    ys = [openmc.YPlane(s * HALF_PITCH, boundary_type="reflective") for s in (-1, 1)]
    zs = [openmc.ZPlane(s * 0.5, boundary_type="reflective") for s in (-1, 1)]
    box = +xs[0] & -xs[1] & +ys[0] & -ys[1] & +zs[0] & -zs[1]
    c_in, c_out = openmc.ZCylinder(r=R_TUBE_IN), openmc.ZCylinder(r=R_TUBE_OUT)
    cpin = openmc.ZCylinder(r=R_CPIN)
    cells, rods = [openmc.Cell(fill=mats[4], region=-cpin & +zs[0] & -zs[1])], []
    for R, n, a, fm in ((R_RING1, N1, A1, 6), (R_RING2, N2, A2, 7)):
        for i in range(n):
            th = a + 2 * math.pi * i / n
            x0, y0 = R * math.cos(th), R * math.sin(th)
            p = openmc.ZCylinder(x0=x0, y0=y0, r=R_PELLET)
            c = openmc.ZCylinder(x0=x0, y0=y0, r=R_CLAD)
            cells.append(openmc.Cell(fill=mats[fm], region=-p & +zs[0] & -zs[1]))
            cells.append(openmc.Cell(fill=mats[5], region=+p & -c & +zs[0] & -zs[1]))
            rods.append(c)
    cool = -c_in & +cpin & +zs[0] & -zs[1]
    for c in rods:
        cool &= +c
    cells.append(openmc.Cell(fill=mats[1], region=cool))
    cells.append(openmc.Cell(fill=mats[2], region=+c_in & -c_out & +zs[0] & -zs[1]))
    cells.append(openmc.Cell(fill=mats[3], region=+c_out & box))
    geom = openmc.Geometry(openmc.Universe(cells=cells))

    s = openmc.Settings()
    s.run_mode, s.particles, s.batches, s.inactive, s.seed = \
        "eigenvalue", particles, batches, inactive, seed
    s.temperature = {"method": "interpolation", "range": (250.0, 1300.0)}
    s.source = openmc.IndependentSource(
        space=openmc.stats.Box((-3.5, -3.5, -0.5), (3.5, 3.5, 0.5)),
        constraints={"fissionable": True})
    s.output = {"tallies": False}
    return openmc.Model(geometry=geom, materials=openmc.Materials(mats.values()),
                        settings=s)


# --- DRAGON ------------------------------------------------------------------
# DRAGON library names differ from OpenMC's for the bound moderators only.
DRAGON_NAME = {"H1": "H1_H2O", "C12": "C12_GR"}
FUEL_SET = {6: 1, 7: 2}          # self-shielding set per fuel mixture
ZR_SET = {2: 3, 4: 4, 5: 5}      # used only when zr_ss (Zr isotopes only; Nb has no subgroups)


def dragon_lib(tube, watered, zr_ss):
    lines = ["LIBRARY := LIB: ::", "  EDIT 0", "  NMIX 7", "  CTRA APOL", "  ANIS 2",
             "  SUBG", "  MIXS LIB: DRAGON FIL: DLIB_99"]
    for mid, nucs in compositions(tube, watered).items():
        lines.append(f"  MIX {mid} {T:.1f}")
        for n, d in nucs.items():
            nm = DRAGON_NAME.get(n, n)
            ss = ""
            if mid in FUEL_SET and n in ("U235", "U238"):
                ss = f"  {FUEL_SET[mid]}"
            elif zr_ss and mid in ZR_SET and n.startswith("Zr"):
                ss = f"  {ZR_SET[mid]}"
            lines.append(f"     {nm:<7s} = {nm:<7s} {d:.5E}{ss}")
    lines.append("  ;")
    return "\n".join(lines)


def dragon_geo(k=1):
    """Coarse GEOSS and refined GEOFL; k multiplies every SPLITR count."""
    return f"""GEOSS := GEO: :: CARCEL 4
  EDIT 0
  X- REFL X+ REFL MESHX {-HALF_PITCH} {HALF_PITCH}
  Y- REFL Y+ REFL MESHY {-HALF_PITCH} {HALF_PITCH}
  RADIUS  0.00  {R_TUBE_IN}  {R_TUBE_OUT}  5.70  11.00
  MIX     1     2     3     3     3
  CLUSTER CARR ROD1 ROD2
  ::: CARR := GEO: TUBE 1
    MIX 4   NPIN 1  RPIN 0.00  APIN 0.00
    RADIUS 0.0000 {R_CPIN} ;
  ::: ROD1 := GEO: TUBE 2
    MIX 6 5   NPIN {N1}  RPIN {R_RING1}  APIN {A1:.6f}
    RADIUS 0.0000 {R_PELLET} {R_CLAD} ;
  ::: ROD2 := GEO: ROD1
    MIX 7 5   NPIN {N2}  RPIN {R_RING2}  APIN {A2:.6f} ;
  ;
GEOFL := GEO: GEOSS :: SPLITR {4*k} {k} {2*k} {6*k}
  ::: CARR := GEO: CARR SPLITR {k} ;
  ::: ROD1 := GEO: ROD1 SPLITR {3*k} {k} ;
  ::: ROD2 := GEO: ROD2 SPLITR {3*k} {k} ;
  ;"""


def dragon_deck(tube="Zr", zr_ss=False, k=1, uss="PASS 2 GRMIN 18", flux_trk="TISO 15 30.0",
                label=""):
    body = []
    for iw, watered in ((1, True), (2, False)):
        body.append(f"""
*  ---- {'watered' if watered else 'voided'} ----
{dragon_lib(tube, watered, zr_ss)}
LIBSS := USS: LIBRARY TRKSS FTRKSS :: EDIT 0 {uss} ;
SYS   := ASM: LIBSS TRK FTRK :: EDIT 0 ;
FLUX  := FLU: LIBSS TRK SYS :: TYPE K EXTE 1.0E-6 ;
GREP: FLUX :: GETVAL 'K-INFINITY' 1 >>kinf<< ;
ECHO "SRP94TAB" {iw} kinf ;
LIBRARY LIBSS SYS FLUX := DELETE: LIBRARY LIBSS SYS FLUX ;""")
    return f"""*----
*  RBMK SAFETY REVIEW PROJECT (1994) SINGLE CELL -- {label}
*  tube {tube}, Zr self-shielding {'ON' if zr_ss else 'off'}, mesh x{k}, USS: {uss}
*
*  GENERATED by openmc/srp94_common.py from [ALX98] Tables 3-4 -- edit that,
*  not this file.  Output: SRP94TAB <1 watered | 2 voided> <k-inf>
*----
LINKED_LIST LIBRARY LIBSS GEOSS GEOFL TRKSS TRK SYS FLUX ;
SEQ_BINARY  FTRKSS FTRK ;
MODULE      LIB: GEO: NXT: USS: ASM: FLU: GREP: DELETE: END: ;
REAL kinf ;

{dragon_geo(k)}
TRKSS FTRKSS := NXT: GEOSS ::
  EDIT 0 TITLE 'SRP94-SS' ALLG BATCH 100 TISO 8 15.0 ;
TRK FTRK := NXT: GEOFL ::
  EDIT 0 TITLE 'SRP94-FLUX' ALLG BATCH 100 {flux_trk} ;
{''.join(body)}

ECHO "rbmk_srp94 completed" ;
END: ;
QUIT .
"""


# id: (tube, zr_ss, k, library access, USS options, flux tracking)
DRAGON_VARIANTS = {
    "d172_zr": ("Zr", False, 1, "dlib99.access", "PASS 2 GRMIN 18", "TISO 15 30.0"),
    "d172_al": ("Al", False, 1, "dlib99.access", "PASS 2 GRMIN 18", "TISO 15 30.0"),
    "d361_zr": ("Zr", True, 1, "shem361.access", "PASS 2 MAXST 300", "TISO 15 30.0"),
    "d361_al": ("Al", False, 1, "shem361.access", "PASS 2 MAXST 300", "TISO 15 30.0"),
    "best_zr": ("Zr", True, 4, "shem361.access", "PASS 2 MAXST 300", "TISO 30 120.0"),
    "best_al": ("Al", False, 4, "shem361.access", "PASS 2 MAXST 300", "TISO 30 120.0"),
}

if __name__ == "__main__":
    import os
    data = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "decks",
                        "Dragon", "data")
    for vid, (tube, zr, k, acc, uss, trk) in DRAGON_VARIANTS.items():
        p = os.path.join(data, f"rbmk_srp94_{vid}.x2m")
        open(p, "w").write(dragon_deck(tube, zr, k, uss, trk, label=vid))
        a = os.path.join(data, f"rbmk_srp94_{vid}.access")
        if os.path.lexists(a):
            os.remove(a)
        os.symlink("../../common/" + acc, a)
        print("wrote", os.path.relpath(p))
