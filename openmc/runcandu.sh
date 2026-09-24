#!/bin/bash
export OPENMC_CROSS_SECTIONS=/home/wilkie/nucdata/endfb-viii.1-hdf5/cross_sections.xml
cd /home/wilkie/code/RBMK/openmc
PY=/home/wilkie/code/RBMK/.venv-openmc/bin/python
for v in 0 1; do
  mkdir -p candu_v$v
  $PY candu_cell.py $v candu_v$v 40000 260 2>&1 | grep -E "CANDURESULT|Error|Traceback"
done
echo CANDU_OMC_DONE
