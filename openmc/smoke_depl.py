import os
os.environ.setdefault("RBMK_DEPLDIR", "smoke_depl/depl")
os.environ.setdefault("RBMK_BRDIR",   "smoke_depl/branch")
os.environ.setdefault("RBMK_RESJSON", "smoke_depl/res.json")
import deplete_void as dv
dv.BU_GRID = [0.0, 0.5]          # two points only
dv.DENSITIES = [0.72, 0.02]
marks = dv.run_depletion()
print("marks", marks, flush=True)
dv.branch_runs(marks, particles=500, batches=20, inactive=5)
print("SMOKE_DEPL_OK")
