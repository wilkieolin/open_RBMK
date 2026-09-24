"""
Fill in the middle of the OpenMC void axis, at dca = 0.35 and 0.15.

WHY
The A5b MULTICOMPO is produced in two variants (PROGRESS.md, "the bracket"):
the DRAGON one, and a copy whose void branches are rescaled to OpenMC.  The
rescaling has to act on the BRANCH RATIO k_void/k_nominal rather than on
absolute k, because the two codes' depletion trajectories diverge (+268 pcm at
5 MWd/kg, -2084 at 20) and correcting absolute k would fold a depletion
difference into a void correction.

To rescale a seven-point DCA axis we need the OpenMC ratio as a function of
density, not just at the two ends.  branch_results81.json has 0.72 and 0.02 at
every burnup; this fills 0.35 and 0.15 so the correction can be fitted in void
fraction rather than assumed linear.  0.15 matters more than it looks: the
DRAGON curve is strongly non-monotonic at low burnup (it turns over between
0.35 and 0.02) and a two-point fit cannot see that at all.

The existing depletion in depl81/ is REUSED -- this only re-runs the branch
transport solves, so it costs a fraction of the original sweep.
"""
import json
import os

import deplete_void as dv

dv.DENSITIES = [0.35, 0.15]
dv.BRDIR = os.environ.get("RBMK_BRDIR", "branch81mid")
dv.RESJSON = os.environ.get("RBMK_RESJSON", "branch_results81_mid.json")

if __name__ == "__main__":
    _, marks = dv.substeps()
    print("reusing depletion in", dv.DEPLDIR, "grid indices:", marks,
          flush=True)
    dv.branch_runs(marks, outdir=os.environ.get("RBMK_DEPLDIR", "depl81"),
                   particles=10_000, batches=130)
    print("wrote", dv.RESJSON)
