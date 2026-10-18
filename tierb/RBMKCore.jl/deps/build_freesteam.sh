#!/bin/sh
# Builds the water-property oracle: the freesteam (IAPWS-IF97) C sources
# vendored in DONJON's Utilib, i.e. exactly the tables THM: calls through
# FREESTEAM.f90 (free_pT, free_Tx, region4 psat/Tsat).  Output in
# tierb/build/ (not tracked).
set -e
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
SRC=$ROOT/5.1/Utilib/src
OUT=$ROOT/tierb/build
mkdir -p "$OUT"
cd "$SRC"
gcc -O2 -fPIC -shared -o "$OUT/libfreesteam.so" b23.c backwards.c bounds.c common.c \
  freesteam_api.c region1.c region2.c region3.c region4.c steam.c steam_pT.c steam_Ts.c \
  steam_Tx.c thcond.c viscosity.c zeroin.c -lm
echo "$OUT/libfreesteam.so"
