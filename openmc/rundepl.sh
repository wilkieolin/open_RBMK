#!/bin/bash
cd "$(dirname "${BASH_SOURCE[0]}")"
ENDF_RELEASE=viii.1
. ./env.sh

export RBMK_DEPLDIR=depl81 RBMK_BRDIR=branch81 RBMK_RESJSON=branch_results81.json
$PY -u deplete_void.py
echo DEPLETION_DONE
