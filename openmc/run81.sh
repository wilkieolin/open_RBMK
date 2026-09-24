#!/bin/bash
# ENDF/B-VIII.1 -- the library DRAGON's DLIB_99 is built from, so this is the
# comparison that isolates method (172-group deterministic vs continuous-energy
# Monte Carlo) from nuclear data.
export OPENMC_CROSS_SECTIONS=/home/wilkie/nucdata/endfb-viii.1-hdf5/cross_sections.xml
cd /home/wilkie/code/RBMK/openmc
PY=/home/wilkie/code/RBMK/.venv-openmc/bin/python

# wait for the VIII.0 sweep and the depletion smoke test to release the cores
# VIII.0 sweep already complete
# no contending jobs
echo "=== VIII.1 sweep starting ==="

for d in 0.72 0.35 0.02; do
  mkdir -p run81_d$d
  /usr/bin/time -v $PY run_one.py $d 100000 500 100 run81_d$d > run81_d$d/log.txt 2>&1
  grep -hE "RESULT|Maximum resident" run81_d$d/log.txt
done
echo VIII1_SWEEP_DONE

export RBMK_DEPLDIR=depl81 RBMK_BRDIR=branch81 RBMK_RESJSON=branch_results81.json
$PY -u deplete_void.py
echo VIII1_DEPLETION_DONE
