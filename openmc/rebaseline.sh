#!/bin/bash
# Re-run every OpenMC number the project quotes, on the current cell geometry.
#
# Written for the 2026-09-24 (3) re-baseline, after the cell geometry was
# closed against sources (carrier, clad OD 13.58, sourced ring radii).  Every
# OpenMC result before that date was computed on an older geometry.
#
# Order is by what the DRAGON/OpenMC bracket needs first:
#   1. depletion at nominal density + 0.72 / 0.02 branches   -> branch_results81.json
#   2. mid-density branches 0.35 / 0.15, reusing (1)          -> branch_results81_mid.json
#   3. fresh-fuel sweep at 0.72 / 0.35 / 0.02 (50k x 250 active, ~20 pcm)  -> run81_d*/log.txt
#   4. beta_eff by prompt-vs-total at fresh fuel              -> beta81_*/
#
# Threads: RBMK_THREADS (default: all cores).  The depletion step runs OpenMC
# in-process, which takes its thread count from OMP_NUM_THREADS instead.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
ENDF_RELEASE=viii.1
. ./env.sh || exit 1
export RBMK_THREADS="${RBMK_THREADS:-$(nproc)}"
export OMP_NUM_THREADS="$RBMK_THREADS"
echo "=== OpenMC re-baseline: $($PY -c 'import openmc; print(openmc.__version__)'), $RBMK_THREADS threads, $OPENMC_CROSS_SECTIONS"

export RBMK_DEPLDIR=depl81 RBMK_BRDIR=branch81 RBMK_RESJSON=branch_results81.json
rm -rf depl81 branch81 branch81mid
$PY -u deplete_void.py; echo STEP1_DONE

RBMK_BRDIR=branch81mid RBMK_RESJSON=branch_results81_mid.json \
    $PY -u branch_mid.py; echo STEP2_DONE

for d in 0.72 0.35 0.02; do
    rm -rf run81_d$d; mkdir -p run81_d$d
    $PY run_one.py $d 50000 300 50 run81_d$d > run81_d$d/log.txt 2>&1
    grep -h RESULT run81_d$d/log.txt
done
echo STEP3_DONE

rm -rf beta81_*
$PY -u beta_eff.py 0.72 beta81; echo STEP4_DONE
echo REBASELINE_DONE
