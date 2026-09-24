# Shared environment for the RBMK tooling.  Source it; don't execute it.
#
#   . tools/env.sh
#
# Everything is derived from this file's location, and every value can be
# overridden from the caller's environment.
RBMK_ROOT="${RBMK_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)}"
export RBMK_ROOT

# OpenMC nuclear data.  56 GB unpacked, so it lives outside the repo; see
# tools/fetch_openmc_data.sh.
export NUCDATA_DIR="${NUCDATA_DIR:-$HOME/nucdata}"

# DRAGON's own draglibs come from the `libraries` submodule and need no fetch.
# They are decompressed into this cache rather than in place, so the submodule
# stays clean -- see decks/common/dlib99.access.
export DRAGLIB_CACHE="${DRAGLIB_CACHE:-$RBMK_ROOT/.cache/draglib}"

# The DRAGON/DONJON binaries name their output directory after the platform.
export DRAGON_ARCH="${DRAGON_ARCH:-$(uname -s)_$(uname -m)}"
