#!/bin/bash
cd "$(dirname "${BASH_SOURCE[0]}")"
ENDF_RELEASE=viii.0
. ./env.sh

for d in 0.72 0.35 0.02; do
  mkdir -p run_d$d
  /usr/bin/time -v $PY run_one.py \
      $d 100000 1100 100 run_d$d > run_d$d/log.txt 2>&1
  grep -E "RESULT|Maximum resident" run_d$d/log.txt
done
echo SWEEP_DONE
