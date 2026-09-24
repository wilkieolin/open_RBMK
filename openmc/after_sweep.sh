#!/bin/bash
export OPENMC_CROSS_SECTIONS=/home/wilkie/nucdata/endfb-viii.0-hdf5/cross_sections.xml
cd /home/wilkie/code/RBMK/openmc
until grep -q SWEEP_DONE /tmp/sweep.log 2>/dev/null; do sleep 20; done
echo "=== sweep finished, starting depletion ==="
/home/wilkie/code/RBMK/.venv-openmc/bin/python -u deplete_void.py
echo DEPLETION_DONE
