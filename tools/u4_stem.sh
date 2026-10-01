#!/usr/bin/env bash
# The deck stem gen_rbmk_unit4.py writes for a given U4_RODS / U4_TILT, kept in
# one place so tools/u4_rods.sh and the generator cannot drift apart.
x=""
[ "$1" = wat ] || x="_$1"
[ "${2:-0}" = 0 ] || x="${x}_t$2"
echo "rbmk_unit4_core${x}"
