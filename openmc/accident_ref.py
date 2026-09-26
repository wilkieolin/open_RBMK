"""OpenMC reference for the accident state (METHOD_CONVERGENCE_PLAN Gate B).

    python accident_ref.py

Full-void branches (0.72 -> 0.02 g/cm3) at 10 and 15 MWd/kg, on the depletion
normalised on deposited energy (RBMK_DEPLDIR, default depl_gb10_ed -- the burnup
scale DRAGON's H-factor normalisation uses, see PROGRESS.md 2026-09-25 (3)) and
on DRAGON's own graphite scattering law (c_Graphite_10p).  50k x 250 active,
about 11x the statistics of deplete_void.py's branches.  Writes accident_ref.json.
"""
import os

import deplete_void as D

if __name__ == "__main__":
    depl = os.environ.get("RBMK_DEPLDIR", "depl_gb10_ed")
    marks = D.substeps()[1]
    D.branch_runs(marks, outdir=depl, particles=50_000, batches=300, inactive=50,
                  graphite_tsl="c_Graphite_10p", bus=(10.0, 15.0),
                  brdir="branch_accref", resjson="accident_ref.json")
