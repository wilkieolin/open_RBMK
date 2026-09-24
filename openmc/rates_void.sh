#!/bin/bash
cd "$(dirname "${BASH_SOURCE[0]}")"
ENDF_RELEASE=viii.1
. ./env.sh

mkdir -p rates_d0.02
$PY rates.py 0.02 rates_d0.02 40000 160 2>&1 | grep "^@@" > rates_d0.02.txt
echo RATES_VOID_DONE
