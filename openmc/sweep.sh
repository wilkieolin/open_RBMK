#!/bin/bash
export OPENMC_CROSS_SECTIONS=/home/wilkie/nucdata/endfb-viii.0-hdf5/cross_sections.xml
cd /home/wilkie/code/RBMK/openmc
for d in 0.72 0.35 0.02; do
  mkdir -p run_d$d
  /usr/bin/time -v /home/wilkie/code/RBMK/.venv-openmc/bin/python run_one.py \
      $d 100000 1100 100 run_d$d > run_d$d/log.txt 2>&1
  grep -E "RESULT|Maximum resident" run_d$d/log.txt
done
echo SWEEP_DONE
