#!/bin/bash
cd "$(dirname "${BASH_SOURCE[0]}")"
ENDF_RELEASE=viii.1
. ./env.sh

for v in 0 1; do
  mkdir -p candu_v$v
  $PY candu_cell.py $v candu_v$v 40000 260 2>&1 | grep -E "CANDURESULT|Error|Traceback"
done
echo CANDU_OMC_DONE
