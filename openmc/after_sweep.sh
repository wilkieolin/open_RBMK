#!/bin/bash
cd "$(dirname "${BASH_SOURCE[0]}")"
ENDF_RELEASE=viii.0
. ./env.sh

until grep -q SWEEP_DONE /tmp/sweep.log 2>/dev/null; do sleep 20; done
echo "=== sweep finished, starting depletion ==="
$PY -u deplete_void.py
echo DEPLETION_DONE
