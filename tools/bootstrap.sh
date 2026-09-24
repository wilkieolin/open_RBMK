#!/usr/bin/env bash
#
# Everything a fresh clone needs, in order.  Safe to re-run: each step is a
# no-op once it has succeeded.
#
#   git clone <this repo> RBMK && cd RBMK && ./tools/bootstrap.sh
#
# Steps 1-3 are cheap.  Step 4 compiles DRAGON5/DONJON5 (a few minutes).
# Step 5 is the expensive one: 9.7 GB of OpenMC cross sections, and it only
# matters if you want to re-run the Monte Carlo cross-check -- skip it with
# --no-openmc and the DRAGON/DONJON side still works.
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/env.sh"
cd "$RBMK_ROOT"

WANT_OPENMC=1
for a in "$@"; do
    case "$a" in
        --no-openmc) WANT_OPENMC=0 ;;
        -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
        *) echo "unknown option: $a" 1>&2; exit 1 ;;
    esac
done

step() { echo; echo "=== $* ==="; }

step "1/5  submodules"
# 5.1 is the DRAGON5/DONJON5 monorepo and `libraries` is ~6 GB of draglibs;
# both come from git.oecd-nea.org and need NEA Data Bank credentials.
git submodule update --init --recursive

step "2/5  decks -> submodule"
./tools/link_decks.sh

step "3/5  libraries hygiene"
./tools/tidy_libraries.sh

step "4/5  build DRAGON5/DONJON5"
if [ -x "5.1/Dragon/bin/${DRAGON_ARCH}/Dragon" ]; then
    echo "already built for ${DRAGON_ARCH}"
else
    ./build_monorepo.sh
fi

if [ "$WANT_OPENMC" = 1 ]; then
    step "5/5  OpenMC"
    ./tools/fetch_openmc_data.sh viii.1
    if [ -x .venv-openmc/bin/python ]; then
        echo "venv already present"
    else
        python3 -m venv .venv-openmc
        .venv-openmc/bin/pip install --upgrade pip
        .venv-openmc/bin/pip install -r openmc/requirements.txt
    fi
    .venv-openmc/bin/python -c "import openmc; print('openmc', openmc.__version__)"
else
    step "5/5  OpenMC -- skipped (--no-openmc)"
fi

cat <<'DONE'

Ready.  Smoke test the DRAGON side:

    cd 5.1/Dragon && ./rdragon -c custom -p 1 rbmk_cell_a3.x2m
    grep -m1 'K-INFINITY' Linux_*/rbmk_cell_a3.result     # expect 1.310172

The 630-point cross-section database (decks/Dragon/data/rbmk_a5b_compo.x2m)
is NOT in the repo -- it is a 114 MB derived artifact and takes hours to build.
Regenerate it before running any DONJON deck that reads a COMPO.
DONE
