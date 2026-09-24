# Sourced by every shell script in openmc/.  Nothing here is absolute: the repo
# root is derived from this file's own location, so a clean clone works wherever
# it lands.
#
# Overridable from the caller's environment:
#   RBMK_ROOT      repo root                     (default: the parent of openmc/)
#   NUCDATA_DIR    OpenMC HDF5 data + chain      (default: $HOME/nucdata)
#   ENDF_RELEASE   viii.0 | viii.1               (default: viii.1)
#   PY             python interpreter            (default: the repo venv)
#
# Two scripts here deliberately pin viii.0 (the historical sweep); they set
# ENDF_RELEASE before sourcing this file.  Everything else wants viii.1, which
# is the evaluation DRAGON's DLIB_99 is built from.
RBMK_ROOT="${RBMK_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
NUCDATA_DIR="${NUCDATA_DIR:-$HOME/nucdata}"
ENDF_RELEASE="${ENDF_RELEASE:-viii.1}"

export OPENMC_CROSS_SECTIONS="${OPENMC_CROSS_SECTIONS:-$NUCDATA_DIR/endfb-$ENDF_RELEASE-hdf5/cross_sections.xml}"
export RBMK_CHAIN="${RBMK_CHAIN:-$NUCDATA_DIR/chain_endfb80_thermal.xml}"
PY="${PY:-$RBMK_ROOT/.venv-openmc/bin/python}"

if [ ! -f "$OPENMC_CROSS_SECTIONS" ]; then
    echo "ERROR: no cross sections at $OPENMC_CROSS_SECTIONS" 1>&2
    echo "       Run tools/fetch_openmc_data.sh, or set NUCDATA_DIR." 1>&2
    return 1 2>/dev/null || exit 1
fi
if [ ! -x "$PY" ]; then
    echo "ERROR: no OpenMC interpreter at $PY" 1>&2
    echo "       Run tools/bootstrap.sh, or set PY." 1>&2
    return 1 2>/dev/null || exit 1
fi
