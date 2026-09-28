"""
RBMK-1000 CPS (control and protection system) channel -- shared specification
for A6 (A6_CPS_PLAN.md).  The ONE transcription of the CPS channel's geometry
and materials: it builds the OpenMC supercells and writes the DRAGON procedures
and decks, so a transcription error lands in both codes identically (the
pattern of srp94_common.py).

    python cps_common.py            # write the DRAGON procedures and decks

WHAT IS MODELLED
A CPS channel holds no fuel, so it cannot be homogenised on its own.  It sits
at the centre of a 3 x 3 SUPERCELL of 25 cm cells, the other 8 being the
production fuel cell (rbmk_proc/RbmkGeo.c2m, RbmkLib.c2m; rbmk_cell.py in
OpenMC), with reflective boundaries.  The real CPS lattice is a 45-degree
rotated square of pitch 2*sqrt(2) cells ([D] p. 12; tools/digitise_fig_II6.py)
with 7 fuel cells per CPS cell; the 3 x 3 supercell has 8.  That shape effect
is measured in OpenMC (supercell 'r45', below) and reported, not corrected.

Central-cell section types (the axial pieces a rod is made of):
  ABS   absorber link   water / Al 50x2 / B4C 65x7.5 / He / Al 70x2 / water
  DSP   displacer link  graphite / Al 74x2.5 / water
  WAT   water column    (telescope, and the channel below a withdrawn rod)
  VOID  drained channel (loss of CPS cooling; bounding case)
  FUEL  a fuel cell     (the GATE A6.2 check: 9 fuel cells = the single cell)
All inside the CPS channel tube, Zr-2.5%Nb 88 x 3 mm, then the same gas
clearance, graphite rings and block as a fuel cell.

SOURCES (tags as in sources/README.md; every number below carries one)
  [D]      Dollezhal & Emelyanov 1980, p. 12 (CPS channel and rod design),
           p. 11 (graphite), p. 59 (in-core Al alloy is SAV-1)
  [INSAG7] INSAG-7 (IAEA 1992) s. 2.2, p. 43, p. 103 (rod types, axial design)
  [TD722]  IAEA-TECDOC-722 s. 3.1 item 12 (B4C ~350 C; CPS water 40-80 C)
  [OST]    OST 1 90048-90 via evek.org/materials/splav-sav1.html (SAV-1
           composition); [SF] studfile.net/preview/16424193 p. 10 (an RBMK
           training text: absorber tubes 50x2 and 70x2 of SAV-1)

OPEN INPUTS, each carried as a bracket (A6_CPS_PLAN.md "Open"):
  B4C_DENSITY   nominal 2.0 g/cm3, bracket 1.7-2.3 (pressed natural-B4C
                bushings, 70-90 % of 2.52 theoretical).  No source found.
  DSP_DENSITY   nominal 1.65 ([D] p. 11, the stack), upper 1.73 ([D] p. 47);
                the displacer's filling ("bushings and blocks") may leave gaps,
                so 1.50 (90 % fill) is the lower case.
  T_DSP         nominal = CPS water; the displacer is sealed in an Al tube in
                50 C water (conduction estimate: < 10 K rise).  CAST (2016)
                bounds displacer irradiation at <= 500 C: 773 K is the upper case.
ASSUMPTIONS (stated, none tuned):
  - The CPS channel carries the same gas clearance and graphite rings as a
    fuel channel ([D] p. 12: "graphite rings outside").
  - SAV-1 at the midpoints of its Si and Mg ranges; Fe at half its maximum;
    trace B and Cd omitted (bounded: <= 1 % of the Al tubes' own absorption).
    Density 2.70 g/cm3 (Al-Mg-Si alloys: 2.69-2.71).
  - B4C with natural boron (B-10 19.9 at.%).  Post-1986 rods use enriched
    B-10 [CAST]; 1986 rods: no source says enriched.
  - CPS water 50 C (mid of [D]'s 40-60 C), 0.988 g/cm3.
  - The drained channel (VOID) holds He at 1 atm, as the gaps.
"""
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "decks", "Dragon", "data")
PROC = os.path.join(DATA, "rbmk_proc")
NA = 0.6022140857                     # 1e-24 * Avogadro: g/cm3 / (g/mol) -> atom/b-cm

# --- geometry, cm -------------------------------------------------------------
PITCH = 25.0                           # [D] p. 11
R_CPS_IN, R_CPS_OUT = 4.10, 4.40       # CPS tube 88 x 3 mm            [D] p. 12
R_GAS_OUT, R_RINGS_OUT, R_BLOCK = 4.55, 5.70, 11.00   # as the fuel cell (RbmkGeo)
# absorber link: Al 50x2 inner tube, B4C 65x7.5 bushings, Al 70x2 outer tube [D] p. 12
R_ABS = dict(al_in_i=2.30, al_in_o=2.50, b4c_o=3.25, al_out_i=3.30, al_out_o=3.50)
# displacer link: Al tube 74 x 2.5, graphite filled                          [D] p. 12
R_DSP = dict(gr_o=3.45, al_o=3.70)

# --- temperatures, K ------------------------------------------------------------
T_CPS = 323.15                         # CPS water and Al, 50 C          [D] p. 12
T_B4C = 623.15                         # ~350 C                          [TD722]
T_DSP = T_CPS                          # see OPEN INPUTS

# --- open inputs: nominal and bracket ---------------------------------------------
B4C_DENSITY = {"nom": 2.0, "lo": 1.7, "hi": 2.3}
DSP_DENSITY = {"nom": 1.65, "lo": 1.50, "hi": 1.73}
T_DSP_CASES = {"nom": T_DSP, "hi": 773.15}

ISO = {  # natural abundance, atom fraction
    "B": {"B10": 0.199, "B11": 0.801},
    "Si": {"Si28": 0.92223, "Si29": 0.04685, "Si30": 0.03092},
    "Mg": {"Mg24": 0.7899, "Mg25": 0.1000, "Mg26": 0.1101},
    "Fe": {"Fe54": 0.05845, "Fe56": 0.91754, "Fe57": 0.02119, "Fe58": 0.00282},
    "Al": {"Al27": 1.0},
}
MASS = {"H": 1.00794, "O": 15.9994, "B": 10.811, "C": 12.011, "Al": 26.9815,
        "Si": 28.0855, "Mg": 24.305, "Fe": 55.845}


def _weight_to_atoms(rho, wt):
    """{element: wt fraction} at density rho -> {nuclide: atom/b-cm}."""
    out = {}
    for el, w in wt.items():
        n = rho * w * NA / MASS[el]
        for iso, f in ISO[el].items():
            out[iso] = out.get(iso, 0.0) + n * f
    return out


def water(rho=0.988):
    n = rho * NA / (2 * MASS["H"] + MASS["O"])
    return {"H1": 2 * n, "O16": n}


def sav1():
    """SAV-1 per [OST]: Si 0.7-1.2, Mg 0.45-0.9, Fe <= 0.2 wt%; Al the rest."""
    wt = {"Si": 0.0095, "Mg": 0.00675, "Fe": 0.001}
    wt["Al"] = 1.0 - sum(wt.values())
    return _weight_to_atoms(2.70, wt)


def b4c(rho):
    n = rho * NA / (4 * MASS["B"] + MASS["C"])
    return {"B10": 4 * n * ISO["B"]["B10"], "B11": 4 * n * ISO["B"]["B11"], "C12": n}


def graphite(rho):
    # C12_GR carries all carbon as C-12 at M = 12.011, as RbmkLib MIX 4/5 do
    return {"C12": rho * NA / MASS["C"]}


def zr25nb():
    """The CPS tube is the fuel channel's alloy ([D] p. 12): RbmkLib MIX 2, read
    from the file rather than copied, so the two cannot drift (standing rule 6)."""
    txt = open(os.path.join(PROC, "RbmkLib.c2m")).read()
    blk = re.search(r"MIX\s+2\s+<<tcool>>(.*?)\n\s*\n", txt, re.S).group(1)
    out = {m.group(1): float(m.group(2))
           for m in re.finditer(r"^\s+(\w+)\s+=\s+\w+\s+([\d.E+-]+)", blk, re.M)}
    assert set(out) == {"Zr90", "Zr91", "Zr92", "Zr94", "Zr96", "Nb93"}, out
    return out


HE = {"He4": 1.28100E-5}               # RbmkLib MIX 3

# DRAGON mixtures of the CPS cell (1-9 are RbmkLib's fuel cell)
MIX = {"wat": 10, "al": 11, "b4c": 12, "dsp": 13, "tube": 14, "gas": 15}
ZR_SET_TUBE = 6                        # RbmkLib uses sets 1-5


def cps_materials(b4c_rho=B4C_DENSITY["nom"], dsp_rho=DSP_DENSITY["nom"], t_dsp=T_DSP,
                  t_wat=T_CPS):
    """{mix: (name, temperature K, {nuclide: atom/b-cm})}.

    t_wat is separable from T_CPS only so the two codes can be compared with the
    CPS water on a draglib temperature node -- see RbmkCpsLib's header."""
    return {
        MIX["wat"]: (f"CPS water, {t_wat - 273.15:.0f} C", t_wat, water()),
        MIX["al"]: ("SAV-1 Al alloy", T_CPS, sav1()),
        MIX["b4c"]: (f"B4C natural B, {b4c_rho} g/cm3", T_B4C, b4c(b4c_rho)),
        MIX["dsp"]: (f"displacer graphite, {dsp_rho} g/cm3", t_dsp, graphite(dsp_rho)),
        MIX["tube"]: ("CPS tube Zr-2.5Nb", T_CPS, zr25nb()),
        MIX["gas"]: ("He, sealed gaps and drained channel", T_CPS, dict(HE)),
    }


# Radial content inside the CPS tube, from the axis out: (outer radius, material key).
# 'split' is the production flux-mesh subdivision of each annulus (GEOFL); the
# converged mesh multiplies it by k, as RbmkGeoFine does for the fuel cell.
SECTIONS = {
    "ABS": [(R_ABS["al_in_i"], "wat", 2), (R_ABS["al_in_o"], "al", 1),
            (R_ABS["b4c_o"], "b4c", 4), (R_ABS["al_out_i"], "gas", 1),
            (R_ABS["al_out_o"], "al", 1), (R_CPS_IN, "wat", 2)],
    "DSP": [(R_DSP["gr_o"], "dsp", 3), (R_DSP["al_o"], "al", 1), (R_CPS_IN, "wat", 2)],
    "WAT": [(R_CPS_IN, "wat", 4)],
    "VOID": [(R_CPS_IN, "gas", 4)],
}
TYPES = ["FUEL", "WAT", "ABS", "DSP", "VOID"]


def volume_fractions(stype):
    """Analytic area of each CPS-cell material, cm2 (GATE A6.2 guardrail)."""
    out, r0 = {}, 0.0
    for r, key, _ in SECTIONS[stype]:
        out[key] = out.get(key, 0.0) + math.pi * (r * r - r0 * r0)
        r0 = r
    out["tube"] = math.pi * (R_CPS_OUT ** 2 - R_CPS_IN ** 2)
    return out


def fuel_cell_areas():
    """{DRAGON mix: area cm2} of one production fuel cell (RbmkGeo.c2m radii)."""
    pi = math.pi
    a = lambda r1, r0=0.0: pi * (r1 * r1 - r0 * r0)
    rods = 18
    return {
        1: a(4.0) - rods * a(0.679) - a(0.75) + a(0.625, 0.6),
        2: a(4.4, 4.0),
        3: a(4.55, 4.4) + rods * (a(0.1) + a(0.585, 0.575)),
        4: a(5.7, 4.55),
        5: PITCH ** 2 - a(5.7),
        6: 6 * a(0.575, 0.1),
        7: 12 * a(0.575, 0.1),
        8: rods * a(0.679, 0.585),
        9: a(0.6) + a(0.75, 0.625),
    }


def supercell_areas(stype):
    """{DRAGON mix: area cm2} of the whole 3 x 3 supercell (GATE A6.2 guardrail)."""
    out = {m: 8 * v for m, v in fuel_cell_areas().items()}
    if stype == "FUEL":
        for m, v in fuel_cell_areas().items():
            out[m] += v
        return out
    mixof = dict(MIX)
    for key, v in volume_fractions(stype).items():
        out[mixof[key]] = out.get(mixof[key], 0.0) + v
    out[3] += math.pi * (R_GAS_OUT ** 2 - R_CPS_OUT ** 2)
    out[4] += math.pi * (R_RINGS_OUT ** 2 - R_GAS_OUT ** 2)
    out[5] += PITCH ** 2 - math.pi * R_RINGS_OUT ** 2
    assert abs(sum(out.values()) - 9 * PITCH ** 2) < 1e-6
    return out


def _guardrail(stype):
    """EDI: per-mixture areas of the supercell, checked against supercell_areas()."""
    exp = supercell_areas(stype)
    mixes = sorted(m for m, v in exp.items() if v > 0)
    # EDI: wants one index per mixture up to the highest one in the GEOMETRY
    # ("14 MIXTURE INDICES EXPECTED" for WAT / DSP, which have no MIX 15)
    nmix = max(mixes)
    merg = " ".join(str(mixes.index(m) + 1) if m in mixes else "0" for m in range(1, nmix + 1))
    # MIXTURESVOL is written by the micro edit only (EDIMIC.f:925): MICR is required
    out = [f"EDIMIX := EDI: LIBSS SCTRK FLUX SCFL SYS :: EDIT 0 MICR ALL",
           f"  MERG MIX {merg} SAVE ON MIXED ;",
           "MACMIX := EDIMIX :: STEP UP MIXED ;"]
    for i, m in enumerate(mixes):
        v = exp[m]
        fail = f'  ECHO "FAIL: {stype} MIX {m} area" vol "expected {v:.5f}" ; ABORT: ; ENDIF ;'
        out += [f"GREP: MACMIX :: GETVAL 'MIXTURESVOL' {i + 1} >>vol<< ;",
                f"IF vol {v * (1 - 1e-3):.5f} < THEN", fail,
                f"IF vol {v * (1 + 1e-3):.5f} > THEN", fail]
    out += [f'ECHO "supercell {stype} volume guardrail PASSED ({len(mixes)} mixtures)" ;',
            "EDIMIX MACMIX := DELETE: EDIMIX MACMIX ;"]
    return "\n".join(out)


# =============================================================================
# OpenMC
# =============================================================================
OMC_NAME = {"H1": "H1"}                 # OpenMC names are ours; bound H via S(a,b)


def openmc_cps_materials(graphite_tsl="c_Graphite_10p", **kw):
    """openmc.Material per CPS mix, ids as the DRAGON mixtures."""
    import openmc
    out = {}
    for mix, (name, t, comp) in cps_materials(**kw).items():
        m = openmc.Material(mix, name)
        for n, d in comp.items():
            m.add_nuclide(n, d)
        m.set_density("sum")
        m.temperature = t
        if mix == MIX["wat"]:
            m.add_s_alpha_beta("c_H_in_H2O")
        if mix == MIX["dsp"]:
            m.add_s_alpha_beta(graphite_tsl)   # the displacer is reactor graphite too
        out[mix] = m
    return out


def openmc_cps_cells(stype, m, cm):
    """Cells of one CPS cell, unbounded (the block is everything outside the rings)."""
    import openmc
    cells, r0 = [], None
    rows = [(r, cm[MIX[k]]) for r, k, _ in SECTIONS[stype]] + \
           [(R_CPS_OUT, cm[MIX["tube"]]), (R_GAS_OUT, m["gas"]), (R_RINGS_OUT, m["gr_ring"])]
    for r, mat in rows:
        s = openmc.ZCylinder(r=r)
        cells.append(openmc.Cell(fill=mat, region=(-s if r0 is None else +r0 & -s)))
        r0 = s
    cells.append(openmc.Cell(fill=m["gr_block"], region=+r0))
    return cells


def openmc_supercell(stype, layout="3x3", dca=0.72, fuel=None, particles=50_000,
                     batches=300, inactive=50, seed=1, graphite_tsl="c_Graphite_10p",
                     temps=None, **kw):
    """layout '3x3': the DRAGON supercell (reflective, CPS at the centre).
    layout 'r45': the true rotated CPS lattice, 4 x 4 cells with CPS cells at
    (0,0) and (2,2), periodic -- 7 fuel cells per CPS cell, as in the core.
    fuel: None (fresh) or {6: Material, 7: Material} of burned fuel."""
    import openmc
    import rbmk_cell as rc
    saved = rc.T_FUEL, rc.T_GRAP, rc.T_COOL
    if temps:
        rc.T_FUEL, rc.T_GRAP, rc.T_COOL = temps
    try:
        mats, m = rc.build_materials(dca, graphite_tsl)
        if fuel:
            for mid, key in ((6, "fuel_in"), (7, "fuel_out")):
                fm = fuel[mid]
                fm.temperature = m[key].temperature
                m[key] = fm
            mats = openmc.Materials([m[k] for k in ("coolant", "pt", "gas", "gr_ring",
                                     "gr_block", "fuel_in", "fuel_out", "clad", "carrier")])
        fuel_u = openmc.Universe(cells=rc.fuel_cells(m))
    finally:
        rc.T_FUEL, rc.T_GRAP, rc.T_COOL = saved
    cm = openmc_cps_materials(graphite_tsl, **kw)
    if stype == "FUEL":
        cps_u = fuel_u
    else:
        cps_u = openmc.Universe(cells=openmc_cps_cells(stype, m, cm))
        mats += [cm[i] for i in sorted(cm)]
    n = 3 if layout == "3x3" else 4
    half = n * PITCH / 2
    lat = openmc.RectLattice()
    lat.pitch = (PITCH, PITCH)
    lat.lower_left = (-half, -half)
    if layout == "3x3":
        grid = [[fuel_u] * 3, [fuel_u, cps_u, fuel_u], [fuel_u] * 3]
        bc = "reflective"
    else:
        grid = [[fuel_u] * 4 for _ in range(4)]
        grid[3][0] = cps_u          # row index runs top-down in OpenMC
        grid[1][2] = cps_u
        bc = "periodic"
    lat.universes = grid
    xs = [openmc.XPlane(sg * half, boundary_type=bc) for sg in (-1, 1)]
    ys = [openmc.YPlane(sg * half, boundary_type=bc) for sg in (-1, 1)]
    zs = [openmc.ZPlane(sg * 0.5, boundary_type="reflective") for sg in (-1, 1)]
    if bc == "periodic":
        xs[0].periodic_surface, ys[0].periodic_surface = xs[1], ys[1]
    root = openmc.Cell(fill=lat, region=+xs[0] & -xs[1] & +ys[0] & -ys[1] & +zs[0] & -zs[1])
    geom = openmc.Geometry(openmc.Universe(cells=[root]))
    st = openmc.Settings()
    st.run_mode, st.particles, st.batches, st.inactive, st.seed = \
        "eigenvalue", particles, batches, inactive, seed
    st.temperature = {"method": "interpolation", "range": (250.0, 2100.0)}
    st.source = openmc.IndependentSource(
        space=openmc.stats.Box((-half, -half, -0.5), (half, half, 0.5)),
        constraints={"fissionable": True})
    st.source_rejection_fraction = 0.01     # fuel is 2.6-2.9 % of the area
    st.output = {"tallies": False}
    return openmc.Model(geometry=geom, materials=openmc.Materials(mats), settings=st)


# =============================================================================
# DRAGON
# =============================================================================
def dragon_cpslib():
    """RbmkCpsLib.c2m: adds MIX 10-15 to a fuel-cell LIBRARY (RbmkLib + BURN)."""
    out = ["*DECK RbmkCpsLib", "*----",
           "*  CPS-channel mixtures, added to a LIBRARY that already holds the fuel",
           "*  cell (RbmkLib, optionally with burned fuel from LIB: ... BURN).",
           "*  GENERATED by openmc/cps_common.py -- edit that, not this file.",
           "*",
           "*  Called as:  LIBRARY := RbmkCpsLib LIBRARY :: <<b4c>> <<dsp>> <<tdsp>> <<twat>> ;",
           "*    b4c   B4C density g/cm3 (open input: 1.7-2.3, nominal 2.0)",
           "*    dsp   displacer graphite density g/cm3 (1.50-1.73, nominal 1.65)",
           "*    tdsp  displacer graphite temperature K",
           "*    twat  CPS water temperature K.  Its own argument, not T_CPS, because",
           "*          the draglib has H1_H2O only at 293.6 / 350 / 400 / 450 / 500 / 600 K",
           "*          and LIBDRA.f:68 interpolates cubically in sqrt(T) (NOTX=3).  The",
           "*          nominal 323.15 K therefore sits 29.5 K off the nearest node, in the",
           "*          steepest part of the bound-hydrogen kernel, while OpenMC has points",
           "*          at 320 and 324 K.  A6.3 Track C tests that with twat = 293.6.",
           "*  Number densities scale linearly with the densities given.",
           "*----",
           "PARAMETER LIBRARY ::", "   EDIT 0", "      ::: LINKED_LIST LIBRARY ;", ";",
           "MODULE LIB: END: ;", "REAL b4c dsp tdsp twat ;",
           ":: >>b4c<< >>dsp<< >>tdsp<< >>twat<< ;"]
    ref = cps_materials(1.0, 1.0)
    nb = {n: d for n, d in ref[MIX["b4c"]][2].items()}
    ng = ref[MIX["dsp"]][2]["C12"]
    for n, d in nb.items():
        out.append(f"REAL n{n}B := {d:.6E} b4c * ;")
    out.append(f"REAL nC12D := {ng:.6E} dsp * ;")
    # MIX blocks are only read after MIXS, on an update too (LIB.f:451)
    out += ["", "LIBRARY := LIB: LIBRARY ::", "  EDIT 0", "  NMIX 15",
            "  MIXS LIB: DRAGON FIL: DLIB_99"]
    dname = {"H1": "H1_H2O"}
    for mix, (name, t, comp) in cps_materials().items():
        tt = {MIX["dsp"]: "<<tdsp>>", MIX["wat"]: "<<twat>>"}.get(mix, f"{t:.2f}")
        out += ["", f"* MIX {mix}: {name}", f"  MIX     {mix}  {tt}"]
        for n, d in comp.items():
            if mix == MIX["b4c"]:
                val = f"<<n{n}B>>"
            elif mix == MIX["dsp"]:
                n, val = "C12_GR", "<<nC12D>>"
            else:
                val = f"{d:.5E}"
            dn = dname.get(n, n) if mix == MIX["wat"] else n
            ss = f"  {ZR_SET_TUBE}" if mix == MIX["tube"] and n.startswith("Zr") else ""
            out.append(f"     {dn:<7s} = {dn:<7s} {val}{ss}")
    out += ["  ;", "", "END: ;", "QUIT ."]
    return "\n".join(out) + "\n"


FUEL_CELL = """  ::: F := GEO: CARCEL 5
    MESHX 0.0 25.0 MESHY 0.0 25.0
    RADIUS  0.00     4.00   4.40   4.55   5.70   11.00
    MIX     1        2      3      4      5      5
{fsplit}    CLUSTER CARR ROD1 ROD2
    ::: CARR := GEO: TUBE 3
      MIX  9 1 9   NPIN 1  RPIN 0.00  APIN 0.00
      RADIUS 0.0000 0.6000 0.6250 0.7500 {csplit};
    ::: ROD1 := GEO: TUBE 4
      MIX  3 6 3 8   NPIN 6  RPIN 1.60  APIN 0.00
      RADIUS 0.0000 0.1000 0.5750 0.5850 0.6790 {rsplit};
    ::: ROD2 := GEO: ROD1
      MIX  3 7 3 8   NPIN 12  RPIN 3.10  APIN 0.261799 ;
    ;"""


def _cps_cell(stype, split):
    rows = SECTIONS[stype] + [(R_CPS_OUT, "tube", 1), (R_GAS_OUT, "gas3", 1),
                              (R_RINGS_OUT, "ring", 2), (R_BLOCK, "block", 6)]
    mixof = dict(MIX, gas3=3, ring=4, block=5)
    rad = " ".join(f"{r:.4f}" for r, _, _ in rows)
    mix = " ".join(str(mixof[k]) for _, k, _ in rows) + " 5"
    sp = ("    SPLITR " + " ".join(f"<<k{s}>>" for _, _, s in rows) + "\n") if split else ""
    return f"""  ::: C := GEO: CARCEL {len(rows)}
    MESHX 0.0 25.0 MESHY 0.0 25.0
    RADIUS 0.0000 {rad}
    MIX {mix}
{sp}    ;"""


def dragon_geo(stype):
    """RbmkSc<type>.c2m: the 3 x 3 supercell, coarse GEOSS and refined GEOFL.
    GEOFL's SPLITR counts are RbmkGeo's times the parameter k (k = 1 production,
    k = 4 the converged mesh of METHOD_CONVERGENCE_PLAN), as in RbmkGeoFine."""
    centre = "F" if stype == "FUEL" else "C"
    ks = sorted({s for _, _, s in SECTIONS.get(stype, [])} | {1, 2, 3, 4, 6})

    def geo(split):
        fsplit = "    SPLITR <<k4>> <<k1>> <<k1>> <<k2>> <<k6>>\n" if split else ""
        csplit = "SPLITR <<k1>> <<k1>> <<k1>> " if split else ""
        rsplit = "SPLITR <<k1>> <<k3>> <<k1>> <<k1>> " if split else ""
        body = FUEL_CELL.format(fsplit=fsplit, csplit=csplit, rsplit=rsplit)
        if stype != "FUEL":
            body += "\n" + _cps_cell(stype, split)
        return f"""GEO: :: CAR2D 3 3
  EDIT 0
  X- REFL X+ REFL Y- REFL Y+ REFL
  CELL F F F
       F {centre} F
       F F F
{body}
  ;"""
    kdecl = "\n".join(f"INTEGER k{s} := {s} k * ;" for s in ks)
    return f"""*DECK RbmkSc{stype}
*----
*  3 x 3 CPS supercell, centre = {stype}; 8 production fuel cells around it.
*  GENERATED by openmc/cps_common.py -- edit that, not this file.  The fuel
*  cell is RbmkGeo.c2m's, verbatim; the centre is cps_common.SECTIONS['{stype}'].
*
*  Called as:  GEOSS GEOFL := RbmkSc{stype} :: <<k>> ;   (k = 1 production)
*----
PARAMETER GEOSS GEOFL ::
   EDIT 0
      ::: LINKED_LIST GEOSS GEOFL ;
;
MODULE GEO: END: ;
INTEGER k ;
:: >>k<< ;
{kdecl}

GEOSS := {geo(False)}

GEOFL := {geo(True)}

END: ;
QUIT .
"""


# depletion nodes, MWd/t: the COMPO's (rbmk_a5b_compo) up to 15000 plus 10900,
# the Unit 4 core average at 01:22:30 (INSAG-7 p. 128: 10.3 MWd/kg is the
# "reference" core; PROJECT_PLAN uses 10.9)
BU_NODES = [0.0, 500.0, 2000.0, 3500.0, 5000.0, 7500.0, 10000.0, 10900.0, 12500.0, 15000.0]
# depleted with EVO: EXTR 1 on this grid, which is rbmk_a5b_compo's (and
# rbmk_meth_dstep25x's) with 10900 added: no step over 2.5 MWd/kg, and the
# 500 MWd/t node kept.  Dropping that node biased the whole trajectory 45-75
# pcm low (2026-09-27), because EXTR 1 extrapolates from the step history.


def dragon_deck(name, bus, dcas, tfs, types, k=1, moc=0, b4c="nom", dsp="nom",
                tdsp="nom", flux_trk="TISO 15 30.0", libproc="RbmkLib", fixed_fuel=False,
                twat=T_CPS):
    """One deck: deplete the single fuel cell on production settings to the
    burnups needed, then solve the supercell of every type at every state.
    fixed_fuel: libproc already holds the burned fuel (the OpenMC-isotopics
    procedures, RbmkLibOED<bu>); no depletion, bus must be [None].
    Output:  CPSTAB <bu> <dca> <tf> <itype> <k-inf>   (itype: TYPES index, 1-based)
             CPSCELL <bu> <dca> <tf> <k-inf>          (the single fuel cell)"""
    lib_anis, ctra = (max(2, moc), "NONE") if moc >= 2 else (2, "APOL")
    solver = ""
    if moc:
        assert libproc.endswith("N2") or moc == 1, "MOC P1 needs a CTRA NONE / ANIS 2 library"
        solver = f"  (flux: MOC, P{moc - 1}, CTRA {ctra})"
    ftrk = (f"ANIS {moc} " if moc >= 2 else "") + flux_trk
    mccg = ("SCTRK := MCCGT: SCTRK SCFTRK SCFL ::\n  EDIT 0 LCMD 3 MAXI 1 EPSI 1E-5 HDD 0. "
            "MCU 400000 KRYL 0 SCR 0 AAC 100 TMT ;") if moc else ""
    asm, fflux = (" ARM", " SCFTRK") if moc else ("", "")
    geoprocs = " ".join(f"RbmkSc{t}" for t in types)
    lines = [f"""*----
*  A6.2 / A6.3 CPS supercell -- {name}
*  fuel library {libproc}, supercell mesh x{k}{solver}
*  B4C {b4c} ({B4C_DENSITY[b4c]} g/cm3), displacer {dsp} ({DSP_DENSITY[dsp]} g/cm3), T_dsp {tdsp}
*  CPS water at {twat} K
*  GENERATED by openmc/cps_common.py -- edit that, not this file.
*  Output:  CPSTAB <bu> <dca> <tf> <itype> <k-inf>  itype {' '.join(f'{i+1}={t}' for i, t in enumerate(TYPES))}
*           CPSCELL <bu> <dca> <tf> <k-inf>   single fuel cell, production settings
*----
LINKED_LIST LIBRARY LIBSS GEOSS GEOFL TRKSS TRK SYS FLUX BURNUP
            SCSS SCFL SCTRKSS SCTRK EDIMIX MACMIX ;
SEQ_BINARY  FTRKSS FTRK SCFTRKSS SCFTRK ;
MODULE      LIB: GEO: NXT: USS: ASM: FLU: EVO: EDI: GREP: DELETE: ABORT: END: {'MCCGT: ' if moc else ''};
PROCEDURE   {' '.join(dict.fromkeys([libproc] + ([] if fixed_fuel else ['RbmkLib'])))} RbmkGeo
            RbmkCpsLib {geoprocs} ;
REAL tgnom := 750.0 ;
REAL tcool := 573.0 ;
REAL fpwr  := 16.7 ;
REAL b4c := {B4C_DENSITY[b4c]} ;
REAL dsp := {DSP_DENSITY[dsp]} ;
REAL tdsp := {T_DSP_CASES[tdsp]} ;
REAL twat := {twat} ;
REAL kinf tbeg tend vol ;
"""]
    if not fixed_fuel:
        nodes = " ".join(f"{b:.1f}" for b in BU_NODES)
        need = max(bus)
        lines.append(f"""*--- single fuel cell: production depletion at the nominal state (as rbmk_a5b_compo)
GEOSS GEOFL := RbmkGeo ;
TRKSS FTRKSS := NXT: GEOSS :: EDIT 0 TITLE 'CELL-SS' ALLG BATCH 100 TISO 8 15.0 ;
TRK FTRK := NXT: GEOFL :: EDIT 0 TITLE 'CELL-FL' ALLG BATCH 100 TISO 15 30.0 ;
LIBRARY := RbmkLib :: 0.72 900.0 <<tgnom>> <<tcool>> ;
LIBSS := USS: LIBRARY TRKSS FTRKSS :: EDIT 0 PASS 2 MAXST 300 ;
SYS := ASM: LIBSS TRK FTRK :: EDIT 0 ;
FLUX := FLU: LIBSS TRK SYS :: TYPE K EXTE 1.0E-6 ;
EVALUATE tend := 0.0 ;
BURNUP LIBSS := EVO: LIBSS FLUX TRK :: EDIT 0 SAVE <<tend>> DAY POWR <<fpwr>> ;""")
        for i in range(1, BU_NODES.index(need) + 1):
            lines.append(f"""EVALUATE tbeg tend := tend {BU_NODES[i]} fpwr / ;
BURNUP LIBSS := EVO: BURNUP LIBSS FLUX TRK ::
  EDIT 0 EXTR 1 DEPL <<tbeg>> <<tend>> DAY POWR <<fpwr>> ;
SYS := DELETE: SYS ;
SYS := ASM: LIBSS TRK FTRK :: EDIT 0 ;
FLUX := FLU: FLUX LIBSS TRK SYS :: TYPE K EXTE 1.0E-6 ;
BURNUP LIBSS := EVO: BURNUP LIBSS FLUX TRK :: EDIT 0 SAVE <<tend>> DAY POWR <<fpwr>> ;""")
        lines.append("LIBRARY LIBSS SYS FLUX := DELETE: LIBRARY LIBSS SYS FLUX ;")
    else:
        lines.append("""GEOSS GEOFL := RbmkGeo ;
TRKSS FTRKSS := NXT: GEOSS :: EDIT 0 TITLE 'CELL-SS' ALLG BATCH 100 TISO 8 15.0 ;
TRK FTRK := NXT: GEOFL :: EDIT 0 TITLE 'CELL-FL' ALLG BATCH 100 TISO 15 30.0 ;""")
    for t in types:
        it = TYPES.index(t) + 1
        lines.append(f"""
*=== supercell, centre {t}
SCSS SCFL := RbmkSc{t} :: {k} ;
SCTRKSS SCFTRKSS := NXT: SCSS :: EDIT 0 TITLE 'SC-SS' ALLG BATCH 100 TISO 8 15.0 ;
SCTRK SCFTRK := NXT: SCFL :: EDIT 0 TITLE 'SC-FL' ALLG BATCH 100 {ftrk} ;
{mccg}""")
        first = True
        for bu in bus:
            for dca in dcas:
                for tf in tfs:
                    bul = 0.0 if bu is None else bu
                    burn = "" if (fixed_fuel or bu == 0.0) else (
                        f"LIBRARY := LIB: LIBRARY BURNUP :: EDIT 0 BURN {BU_NODES.index(bu) + 1} MIX 6 MIX 7 ;\n")
                    libcall = (f"LIBRARY := {libproc} :: {dca} {tf} <<tgnom>> <<tcool>> ;\n{burn}")
                    cell = ""
                    if t == types[0] and not moc and k == 1:
                        cell = f"""LIBSS := USS: LIBRARY TRKSS FTRKSS :: EDIT 0 PASS 2 MAXST 300 ;
SYS := ASM: LIBSS TRK FTRK :: EDIT 0 ;
FLUX := FLU: LIBSS TRK SYS :: TYPE K EXTE 1.0E-6 ;
GREP: FLUX :: GETVAL 'K-INFINITY' 1 >>kinf<< ;
ECHO "CPSCELL" {bul} {dca} {tf} kinf ;
LIBSS SYS FLUX := DELETE: LIBSS SYS FLUX ;
"""
                    # the FUEL-centre supercell has no CPS mixtures: adding them would
                    # hand USS: a self-shielding set (the CPS tube's) with no region
                    cps = "" if t == "FUEL" else \
                        "LIBRARY := RbmkCpsLib LIBRARY :: <<b4c>> <<dsp>> <<tdsp>> <<twat>> ;\n"
                    guard = (_guardrail(t) + "\n") if first else ""
                    first = False
                    lines.append(f"""{libcall}{cell}{cps}LIBSS := USS: LIBRARY SCTRKSS SCFTRKSS :: EDIT 0 PASS 2 MAXST 300 ;
SYS := ASM: LIBSS SCTRK SCFTRK :: EDIT 0{asm} ;
FLUX := FLU: LIBSS SCTRK{fflux} SYS :: TYPE K EXTE 1.0E-6 ;
GREP: FLUX :: GETVAL 'K-INFINITY' 1 >>kinf<< ;
ECHO "CPSTAB" {bul} {dca} {tf} {it} kinf ;
{guard}LIBRARY LIBSS SYS FLUX := DELETE: LIBRARY LIBSS SYS FLUX ;""")
        lines.append("SCSS SCFL SCTRKSS SCTRK SCFTRKSS SCFTRK := DELETE: SCSS SCFL SCTRKSS SCTRK SCFTRKSS SCFTRK ;")
    lines.append(f'\nECHO "rbmk_cps_{name} completed" ;\nEND: ;\nQUIT .\n')
    text = "\n".join(lines)
    # CLE-2000 reads columns 1-120 and silently drops the rest (clelog.c:31)
    assert max(map(len, text.splitlines())) <= 110, "deck line too long"
    return text


# =============================================================================
# A6.4: homogenisation, SPH and the CPS MULTICOMPO
# =============================================================================
A64_BUS = [0.0, 10900.0, 15000.0]
A64_DCAS = [0.72, 0.35, 0.02]
A64_TFS = [900.0, 1500.0]


def compo_deck(stype, bus=None, dcas=None, tfs=None, tag=None, mtrack="DUAL 1 1"):
    """rbmk_cps_a64_<type>: production supercell at every A64 state; two-group
    cell-by-cell homogenisation (MERG CELL), SPH equivalence on the macro-geometry
    with TRIVAT DUAL 1 1 (one node per 25 cm cell; see the deck comment for why
    not MCFD) -- and a MULTICOMPO whose mixture 5 is the SPH-corrected CPS cell.
    Axes as the fuel COMPO: 'burnup' (of the surrounding fuel), 'TF', 'DCA'.
    TG is held at 750 K.  Output: CPSTAB rows as dragon_deck, and _CCompo."""
    it = TYPES.index(stype) + 1
    bus, dcas, tfs = bus or A64_BUS, dcas or A64_DCAS, tfs or A64_TFS
    tag = tag or stype
    nodes = BU_NODES[:BU_NODES.index(max(bus)) + 1]
    L = [f"""*----
*  A6.4 CPS MULTICOMPO -- centre {stype}.  GENERATED by openmc/cps_common.py.
*  Production settings (RbmkLib, SHEM-361 + Zr SS, RbmkGeo mesh, CP), fuel depleted
*  as rbmk_a5b_compo (EXTR 1, <= 2.5 MWd/kg steps, 16.7 MW/t).
*  COMPO mixture 5 = the CPS cell (SPH-corrected);
*  mixtures 1-4, 6-9 = the fuel cells around it (not used by the core).
*  Output: CPSTAB <bu> <dca> <tf> {it} <k-inf>;  _CCompo (saved to compo/_CCompo{tag})
*----
LINKED_LIST LIBRARY LIBSS GEOSS GEOFL TRKSS TRK SYS FLUX BURNUP
            SCSS SCFL SCTRKSS SCTRK EDIOBJ GEOMAC MTRACK COMPO DONNEES ;
SEQ_BINARY  FTRKSS FTRK SCFTRKSS SCFTRK ;
*  FILE is required: without it the export is a scratch file, deleted at END:
SEQ_ASCII   _CCompo :: FILE './_CCompo' ;
MODULE      LIB: GEO: NXT: USS: ASM: FLU: EVO: EDI: SPH: TRIVAT: COMPO: UTL:
            GREP: DELETE: END: ;
PROCEDURE   RbmkLib RbmkGeo RbmkCpsLib RbmkSc{stype} ;
REAL tgnom := 750.0 ;
REAL tcool := 573.0 ;
REAL fpwr  := 16.7 ;
REAL kinf tbeg tend ;

GEOSS GEOFL := RbmkGeo ;
TRKSS FTRKSS := NXT: GEOSS :: EDIT 0 TITLE 'CELL-SS' ALLG BATCH 100 TISO 8 15.0 ;
TRK FTRK := NXT: GEOFL :: EDIT 0 TITLE 'CELL-FL' ALLG BATCH 100 TISO 15 30.0 ;
LIBRARY := RbmkLib :: 0.72 900.0 <<tgnom>> <<tcool>> ;
LIBSS := USS: LIBRARY TRKSS FTRKSS :: EDIT 0 PASS 2 MAXST 300 ;
SYS := ASM: LIBSS TRK FTRK :: EDIT 0 ;
FLUX := FLU: LIBSS TRK SYS :: TYPE K EXTE 1.0E-6 ;
EVALUATE tend := 0.0 ;
BURNUP LIBSS := EVO: LIBSS FLUX TRK :: EDIT 0 SAVE <<tend>> DAY POWR <<fpwr>> ;"""]
    for b in nodes[1:]:
        L.append(f"""EVALUATE tbeg tend := tend {b} fpwr / ;
BURNUP LIBSS := EVO: BURNUP LIBSS FLUX TRK ::
  EDIT 0 EXTR 1 DEPL <<tbeg>> <<tend>> DAY POWR <<fpwr>> ;
SYS := DELETE: SYS ;
SYS := ASM: LIBSS TRK FTRK :: EDIT 0 ;
FLUX := FLU: FLUX LIBSS TRK SYS :: TYPE K EXTE 1.0E-6 ;
BURNUP LIBSS := EVO: BURNUP LIBSS FLUX TRK :: EDIT 0 SAVE <<tend>> DAY POWR <<fpwr>> ;""")
    L.append(f"""LIBRARY LIBSS SYS FLUX := DELETE: LIBRARY LIBSS SYS FLUX ;

SCSS SCFL := RbmkSc{stype} :: 1 ;
SCTRKSS SCFTRKSS := NXT: SCSS :: EDIT 0 TITLE 'SC-SS' ALLG BATCH 100 TISO 8 15.0 ;
SCTRK SCFTRK := NXT: SCFL :: EDIT 0 TITLE 'SC-FL' ALLG BATCH 100 TISO 15 30.0 ;

*  Macro-geometry for SPH: one homogeneous 25 cm node per cell, as in the core.
*  Discretisation DUAL 1 1 (lowest-order Raviart-Thomas), NOT the MCFD 1 the core
*  has used since A2: with MCFD the SPH iteration oscillates and never converges
*  (200 iterations, any normalisation: STD, ASYM 1; tested 2026-09-26 on the ABS
*  supercell), and on the full deck it ended in a segfault in TRI1GSO.  DUAL 1 1
*  converges in 22 iterations.  The core must use the discretisation SPH was
*  computed with, so A6.5 onward runs TRIVAT DUAL 1 1.
*  With NXT tracking, EDI: MERG CELL merges cell by cell (EDIMRC) but builds no
*  macro-geometry (EDI.f:449), so it is given here; merged regions are numbered
*  cell by cell, and the CPS centre is 5 in either raster order.
GEOMAC := GEO: :: CAR2D 3 3
  X- REFL X+ REFL Y- REFL Y+ REFL
  MESHX 0.0 25.0 50.0 75.0 MESHY 0.0 25.0 50.0 75.0
  MIX 1 2 3  4 5 6  7 8 9 ;
MTRACK := TRIVAT: GEOMAC :: EDIT 0 MAXR 20 {mtrack} ;

*  TF is a TEMP axis read from the LIBRARY (mixture 6), as in rbmk_a5b_compo
COMPO := COMPO: ::
  EDIT 1
  STEP UP 'EDICPS'
  MAXCAL 5
  COMM 'RBMK CPS cell {stype}, 3x3 supercell, SPH (TRIVAT {mtrack})' ENDC
  PARA 'burnup' IRRA
  PARA 'TF'  TEMP LIBRARY 6
  PARA 'DCA' VALU REAL
  INIT
  ;""")
    for bu in bus:
        istep = BU_NODES.index(bu) + 1
        for tf in tfs:
            for dca in dcas:
                burn = "" if bu == 0.0 else                     f"LIBRARY := LIB: LIBRARY BURNUP :: EDIT 0 BURN {istep} MIX 6 MIX 7 ;\n"
                L.append(f"""
LIBRARY := RbmkLib :: {dca} {tf} <<tgnom>> <<tcool>> ;
{burn}LIBRARY := RbmkCpsLib LIBRARY :: {B4C_DENSITY['nom']} {DSP_DENSITY['nom']} {T_DSP} {T_CPS} ;
LIBSS := USS: LIBRARY SCTRKSS SCFTRKSS :: EDIT 0 PASS 2 MAXST 300 ;
SYS := ASM: LIBSS SCTRK SCFTRK :: EDIT 0 ;
*  B1 at zero buckling: sets the leakage flag so COMPO: keeps GOLVER's DIFF
*  (see rbmk_a5b_compo), without changing the spectrum
FLUX := FLU: LIBSS SCTRK SYS :: TYPE K B1 SIGS BUCK 0.0 EXTE 1.0E-6 ;
GREP: FLUX :: GETVAL 'K-INFINITY' 1 >>kinf<< ;
ECHO "CPSTAB" {bu} {dca} {tf} {it} kinf ;
EDIOBJ := EDI: LIBSS SCTRK FLUX SCFL SYS GEOMAC ::
  EDIT 0 MERG CELL NXT COND 0.625 GOLVER MGEO GEOMAC SAVE ON EDICPS ;
*  ASYM 1: SPH factors normalised to 1 in a fuel cell (merged region 1, a corner),
*  because the core uses the fuel COMPO's own, uncorrected cross sections next to
*  this cell.  STD (average-flux normalisation over all nine cells) left the fuel
*  cells' factors off 1 and the DONJON supercell 374 pcm off DRAGON (2026-09-26).
EDIOBJ := SPH: EDIOBJ MTRACK :: EDIT 1 ASYM 1 ITER 1.0E-6 200 ;
EVALUATE tend := {bu} fpwr / ;
COMPO := COMPO: COMPO EDIOBJ BURNUP LIBRARY ::
  EDIT 0 STEP UP 'EDICPS' 'DCA' {dca} SET <<tend>> DAY ;
LIBRARY LIBSS SYS FLUX EDIOBJ := DELETE: LIBRARY LIBSS SYS FLUX EDIOBJ ;""")
    L.append(f"""
_CCompo := COMPO ;
ECHO "rbmk_cps_a64_{tag} completed" ;
END: ;
QUIT .
""")
    text = "\n".join(L)
    assert max(map(len, text.splitlines())) <= 110, max(text.splitlines(), key=len)
    return text


SAVE_HOOK = """#!/bin/sh
# SAVE HOOK (generated by openmc/cps_common.py): move the CPS MULTICOMPO out of the
# scratch run directory to <CodeDir>/compo/, as rbmk_a5b_compo.save does.
dest="$1"/compo
mkdir -p "$dest"
if [ -f _CCompo ]; then
   mv _CCompo "$dest"/_CCompo{t}
   echo "saved $dest/_CCompo{t} ($(wc -c < "$dest"/_CCompo{t}) bytes)"
else
   echo "WARNING: _CCompo was not produced by the run" 1>&2
fi
"""


# name: kwargs for dragon_deck
DRAGON_DECKS = {
    # A6.2 smoke and gate: fresh fuel, nominal state, every type
    "smoke": dict(bus=[0.0], dcas=[0.72], tfs=[900.0], types=TYPES),
    # A6.3 production method: fresh, and OpenMC's 10 MWd/kg isotopics (as oed10)
    "a63_fresh": dict(bus=[0.0], dcas=[0.72, 0.02], tfs=[900.0], types=TYPES),
    "a63_oed10": dict(bus=[10000.0], dcas=[0.72, 0.02], tfs=[900.0], types=TYPES,
                      libproc="RbmkLibOED10", fixed_fuel=True),
    # A6.3 Track C (2026-09-28): the absolute-k comparison puts the residual in
    # the WATER column -- WAT is +452 to +616 pcm off OpenMC while VOID, the
    # SAME geometry filled with helium instead, is +43 to -157.  The draglib has
    # H1_H2O only at 293.6 / 350 / 400 / 450 / 500 / 600 K and interpolates
    # cubically in sqrt(T) (LIBDRA.f:68, NOTX=3), so the nominal 323.15 K sits
    # 29.5 K off the nearest node; OpenMC has 320 and 324 K.  These two decks
    # are the control: the CPS water moved to 293.6 K, exactly on the draglib
    # node, where LIBLEX.f:46 returns TERP = 1 and no interpolation happens.
    # If the gap collapses, the interpolation is the mechanism.
    "a63_twat": dict(bus=[0.0], dcas=[0.72, 0.02], tfs=[900.0], types=["WAT"],
                     twat=293.6),
}
# A6.3 converged method (4x mesh + MOC P1, as bestmoc / oedbest10), one deck per
# type so they run in parallel.  The FUEL centre is the single cell (bestmoc,
# oedbest10 exist) and is not repeated.
for _t in TYPES[1:]:
    DRAGON_DECKS[f"a63_fresh_conv_{_t}"] = dict(
        bus=[0.0], dcas=[0.72, 0.02], tfs=[900.0], types=[_t], k=4, moc=2,
        libproc="RbmkLibZN2", flux_trk="TISO 30 120.0")
    if _t in ("WAT", "DSP"):
        # the first launch of these died after dca 0.72 on the EDI: mixture-count
        # bug above; these finish the voided point
        DRAGON_DECKS[f"a63_fresh_conv_{_t}_v"] = dict(
            bus=[0.0], dcas=[0.02], tfs=[900.0], types=[_t], k=4, moc=2,
            libproc="RbmkLibZN2", flux_trk="TISO 30 120.0")
        DRAGON_DECKS[f"a63_oed10_conv_{_t}_v"] = dict(
            bus=[10000.0], dcas=[0.02], tfs=[900.0], types=[_t], k=4, moc=2,
            libproc="RbmkOED10N2", flux_trk="TISO 30 120.0", fixed_fuel=True)
    DRAGON_DECKS[f"a63_oed10_conv_{_t}"] = dict(
        bus=[10000.0], dcas=[0.72, 0.02], tfs=[900.0], types=[_t], k=4, moc=2,
        libproc="RbmkOED10N2", flux_trk="TISO 30 120.0", fixed_fuel=True)


DON = os.path.join(ROOT, "decks", "Donjon", "data")


def verify_don(stype, states, tag=None):
    """rbmk_cps_a64v_<tag>.don -- GATE A6.4.  DONJON on the homogenised 3 x 3
    supercell: the 8 fuel cells from the FUEL MULTICOMPO (_ACompo, the core's own
    fuel data -- not the supercell's), the centre from _CCompo<type> mixture 5
    (SPH-corrected).  Compared with DRAGON's supercell k-inf at the same state
    (CPSTAB rows).  Output: A64V <bu> <dca> <tf> <itype> <k> with TRIVAT DUAL 1 1
    (the discretisation SPH used: the gate) and A64M ... with MCFD 1 (what the
    A2 core solver would give with the same data: information only)."""
    tag = tag or stype
    it = TYPES.index(stype) + 1
    L = [f"""*----
*  GATE A6.4 -- centre {stype}.  GENERATED by openmc/cps_common.py.
*----
LINKED_LIST FCpo CCpo MACRO GEOM TRACK TRKFD GEOS TRKS SYSTEM FLUX ;
SEQ_ASCII   _ACompo :: FILE './_ACompo' ;
SEQ_ASCII   _CCompo :: FILE './_CCompo{tag}' ;
MODULE      NCR: GEO: TRIVAT: TRIVAA: FLUD: GREP: DELETE: END: ;
REAL kinf ;
FCpo := _ACompo ;
CCpo := _CCompo ;
GEOM := GEO: :: CAR2D 3 3
  X- REFL X+ REFL Y- REFL Y+ REFL
  MESHX 0.0 25.0 50.0 75.0 MESHY 0.0 25.0 50.0 75.0
  MIX 1 1 1  1 2 1  1 1 1 ;
TRACK := TRIVAT: GEOM :: EDIT 0 MAXR 20 DUAL 1 1 ;
TRKFD := TRIVAT: GEOM :: EDIT 0 MAXR 20 MCFD 1 ;
GEOS := GEO: :: CAR2D 3 3
  X- REFL X+ REFL Y- REFL Y+ REFL
  MESHX 0.0 25.0 50.0 75.0 MESHY 0.0 25.0 50.0 75.0
  MIX 1 2 3  4 5 6  7 8 9 ;
TRKS := TRIVAT: GEOS :: EDIT 0 MAXR 20 DUAL 1 1 ;"""]
    for bu, dca, tf in states:
        L.append(f"""
MACRO := NCR: FCpo CCpo :: EDIT 0 MACRO LINEAR NMIX 2
  COMPO FCpo 'EDIRBMK'
  MIX 1 FROM 1 SET 'burnup' {bu} SET 'DCA' {dca} SET 'TF' {tf} SET 'TG' 750.0 ENDMIX
  COMPO CCpo 'EDICPS'
  MIX 2 FROM 5 SET 'burnup' {bu} SET 'DCA' {dca} SET 'TF' {tf} ENDMIX ;
SYSTEM := TRIVAA: MACRO TRACK :: EDIT 0 ;
FLUX := FLUD: SYSTEM TRACK :: EDIT 0 EXTE 1.0E-7 ;
GREP: FLUX :: GETVAL 'K-EFFECTIVE' 1 >>kinf<< ;
ECHO "A64V" {bu} {dca} {tf} {it} kinf ;
SYSTEM FLUX := DELETE: SYSTEM FLUX ;
SYSTEM := TRIVAA: MACRO TRKFD :: EDIT 0 ;
FLUX := FLUD: SYSTEM TRKFD :: EDIT 0 EXTE 1.0E-7 ;
GREP: FLUX :: GETVAL 'K-EFFECTIVE' 1 >>kinf<< ;
ECHO "A64M" {bu} {dca} {tf} {it} kinf ;
MACRO SYSTEM FLUX := DELETE: MACRO SYSTEM FLUX ;
*  SPH self-consistency: all nine cells from the CPS COMPO -> DRAGON's k exactly
MACRO := NCR: CCpo :: EDIT 0 MACRO LINEAR NMIX 9
  COMPO CCpo 'EDICPS'
{{sc}}  ;
SYSTEM := TRIVAA: MACRO TRKS :: EDIT 0 ;
FLUX := FLUD: SYSTEM TRKS :: EDIT 0 EXTE 1.0E-7 ;
GREP: FLUX :: GETVAL 'K-EFFECTIVE' 1 >>kinf<< ;
ECHO "A64S" {bu} {dca} {tf} {it} kinf ;
MACRO SYSTEM FLUX := DELETE: MACRO SYSTEM FLUX ;""".replace("{sc}", "".join(
            f"  MIX {m} FROM {m} SET 'burnup' {bu} SET 'DCA' {dca} SET 'TF' {tf} ENDMIX\n"
            for m in range(1, 10))))
    L.append(f'ECHO "rbmk_cps_a64v_{tag} completed" ;\nEND: ;\nQUIT .\n')
    return "\n".join(L)


DON_ACCESS = """#!/bin/sh
# Generated by openmc/cps_common.py: stage the fuel and CPS MULTICOMPOs.
src="$1"/../Dragon/compo
cp "$src"/_ACompo . || exit 1
cp "$src"/_CCompo{t} . || exit 1
"""


def write_a64():
    decks = {t: dict(stype=t) for t in TYPES[1:]}
    # one-state smoke: exercises EDI -> SPH -> COMPO -> DONJON before the full runs
    decks["smk"] = dict(stype="ABS", bus=[0.0], dcas=[0.72], tfs=[900.0], tag="smk")
    # The MCFD control (2026-09-28).  A64M in the gate applies DUAL-derived SPH
    # factors to an MCFD solve, so its 31-34 % absorber-worth loss is part MCFD
    # and part mismatch.  This builds the COMPO with SPH computed under MCFD
    # itself, so A64M off THIS compo is MCFD judged on its own terms.  If SPH
    # will not converge under MCFD, that failure is the answer.
    decks["smkm"] = dict(stype="ABS", bus=[0.0], dcas=[0.72], tfs=[900.0], tag="smkm",
                         mtrack="MCFD 1")
    for t, kw in decks.items():
        p = os.path.join(DATA, f"rbmk_cps_a64_{t}.x2m")
        open(p, "w").write(compo_deck(**kw))
        a = os.path.join(DATA, f"rbmk_cps_a64_{t}.access")
        if os.path.lexists(a):
            os.remove(a)
        os.symlink("../../common/rbmk.access", a)
        sv = os.path.join(DATA, f"rbmk_cps_a64_{t}.save")
        open(sv, "w").write(SAVE_HOOK.replace("{t}", t))
        os.chmod(sv, 0o755)
        print("wrote", os.path.relpath(p, ROOT))
        st = [(b, d, f) for b in kw.get("bus") or A64_BUS for f in kw.get("tfs") or A64_TFS
              for d in kw.get("dcas") or A64_DCAS]
        q = os.path.join(DON, f"rbmk_cps_a64v_{t}.don")
        open(q, "w").write(verify_don(kw["stype"], st, tag=t))
        qa = q + ".access"
        open(qa, "w").write(DON_ACCESS.replace("{t}", t))
        os.chmod(qa, 0o755)


def write_dragon():
    open(os.path.join(PROC, "RbmkCpsLib.c2m"), "w").write(dragon_cpslib())
    for t in TYPES:
        open(os.path.join(PROC, f"RbmkSc{t}.c2m"), "w").write(dragon_geo(t))
    for name, kw in DRAGON_DECKS.items():
        p = os.path.join(DATA, f"rbmk_cps_{name}.x2m")
        open(p, "w").write(dragon_deck(name, **kw))
        a = os.path.join(DATA, f"rbmk_cps_{name}.access")
        if os.path.lexists(a):
            os.remove(a)
        os.symlink("../../common/rbmk.access", a)
        print("wrote", os.path.relpath(p, ROOT))


if __name__ == "__main__":
    write_dragon()
    write_a64()
