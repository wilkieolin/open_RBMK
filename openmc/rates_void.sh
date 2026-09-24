#!/bin/bash
export OPENMC_CROSS_SECTIONS=/home/wilkie/nucdata/endfb-viii.1-hdf5/cross_sections.xml
cd /home/wilkie/code/RBMK/openmc
mkdir -p rates_d0.02
/home/wilkie/code/RBMK/.venv-openmc/bin/python rates.py 0.02 rates_d0.02 40000 160 2>&1 | grep "^@@" > rates_d0.02.txt
echo RATES_VOID_DONE
