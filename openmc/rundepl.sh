#!/bin/bash
export OPENMC_CROSS_SECTIONS=/home/wilkie/nucdata/endfb-viii.1-hdf5/cross_sections.xml
export RBMK_DEPLDIR=depl81 RBMK_BRDIR=branch81 RBMK_RESJSON=branch_results81.json
cd /home/wilkie/code/RBMK/openmc
/home/wilkie/code/RBMK/.venv-openmc/bin/python -u deplete_void.py
echo DEPLETION_DONE
