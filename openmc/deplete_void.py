"""
Independent OpenMC check of the A5 result: void coefficient vs burnup.

Mirrors 5.1/Dragon/data/rbmk_a5_void.x2m -- deplete at nominal coolant
density and 16.7 MW/t, then at each saved burnup point re-run the cell at
each branch density with the depleted fuel isotopics restored.  Same grid,
same power, same densities; different transport method and different data.

Memory: the chain is reduced to level 5, so the loaded nuclide set stays in
the low hundreds rather than ~3800.  Expect a few GB resident, CPU only.
"""
# Depleted fuel carries ~379 nuclides, so every transport solve runs ~25x
# slower than the fresh-fuel one.  Particle counts below are sized for that,
# not for the fresh cell: the void signal at discharge burnup is of order
# 1000 pcm and does not need the 8 pcm precision the fresh sweep used.
import os, json
import numpy as np
import openmc, openmc.deplete
from rbmk_cell import make_model, R_PELLET, R_HOLE, RING1_N, RING2_N

CHAIN   = os.environ.get(
    "RBMK_CHAIN",
    os.path.join(os.environ.get("NUCDATA_DIR", os.path.expanduser("~/nucdata")),
                 "chain_endfb80_thermal.xml"))
DEPLDIR = os.environ.get("RBMK_DEPLDIR", "depl")
BRDIR   = os.environ.get("RBMK_BRDIR",   "branch")
RESJSON = os.environ.get("RBMK_RESJSON", "branch_results.json")
POWER_DENSITY = 16.7          # W per gram of initial heavy metal
BU_GRID = [0.0, 2.0, 5.0, 10.0, 15.0, 20.0]           # MWd/kg
DENSITIES = [0.72, 0.02]                               # g/cm3

A = lambda r: np.pi * r * r
PELLET_AREA = A(R_PELLET) - A(R_HOLE)                  # per rod, cm2
VOL = {6: RING1_N * PELLET_AREA, 7: RING2_N * PELLET_AREA}   # 1 cm slab


def substeps():
    """Subdivide the DRAGON grid so no depletion step exceeds 2.5 MWd/kg."""
    steps, marks, cum = [], [], 0.0
    for lo, hi in zip(BU_GRID[:-1], BU_GRID[1:]):
        n = int(np.ceil((hi - lo) / 2.5))
        d = (hi - lo) / n
        for _ in range(n):
            steps.append(d)
            cum += d
        marks.append(len(steps))       # result index of this grid point
    return steps, [0] + marks


def run_depletion(outdir=DEPLDIR):
    os.makedirs(outdir, exist_ok=True)
    model = make_model(dca=0.72, particles=5_000, batches=110, inactive=20)
    for mat in model.materials:
        if mat.id in VOL:
            mat.volume = VOL[mat.id]
            mat.depletable = True

    op = openmc.deplete.CoupledOperator(
        model, CHAIN, normalization_mode="fission-q",
        reduce_chain_level=5)
    steps, marks = substeps()
    integ = openmc.deplete.CECMIntegrator(
        op, steps, power_density=POWER_DENSITY, timestep_units="MWd/kg")
    cwd = os.getcwd()
    os.chdir(outdir)
    try:
        integ.integrate()
    finally:
        os.chdir(cwd)
    return marks


def branch_runs(marks, outdir=DEPLDIR, particles=10_000, batches=130,
                inactive=20):
    """Re-run each saved burnup point at each coolant density."""
    res = openmc.deplete.Results(os.path.join(outdir, "depletion_results.h5"))
    out = []
    for bu, idx in zip(BU_GRID, marks):
        # depleted fuel compositions at this burnup point
        depleted = {m.id: m for m in res.export_to_materials(
            idx, path=os.path.join(outdir, "materials.xml"))}
        for dca in DENSITIES:
            tag = f"bu{bu:g}_d{dca:g}"
            d = os.path.join(BRDIR, tag)
            os.makedirs(d, exist_ok=True)
            model = make_model(dca=dca, particles=particles,
                               batches=batches, inactive=inactive)
            # swap in the depleted isotopics for MIX 6 and MIX 7
            newmats = []
            for mat in model.materials:
                if mat.id in VOL:
                    dm = depleted[mat.id]
                    dm.volume = VOL[mat.id]
                    dm.temperature = mat.temperature
                    newmats.append(dm)
                else:
                    newmats.append(mat)
            model.materials = openmc.Materials(newmats)
            sp = model.run(cwd=d, threads=int(os.environ.get("RBMK_THREADS", os.cpu_count())), output=False)
            with openmc.StatePoint(sp) as s:
                k, sd = s.keff.nominal_value, s.keff.std_dev
            out.append(dict(bu=bu, dca=dca, k=k, sd=sd))
            print(f"  BU={bu:6.1f} MWd/kg  dca={dca:4.2f}  "
                  f"k={k:.5f} +/- {sd:.5f}", flush=True)
    with open(RESJSON, "w") as f:
        json.dump(out, f, indent=1)
    return out


if __name__ == "__main__":
    marks = run_depletion()
    print("depletion done; grid indices:", marks, flush=True)
    branch_runs(marks)
