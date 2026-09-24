#!/usr/bin/env bash
#
# Fetch the OpenMC nuclear data.  56 GB unpacked, which is why it lives outside
# the repo (default $HOME/nucdata, override with NUCDATA_DIR).
#
# Sources are the official libraries listed at https://openmc.org/data/ .  The
# Box links below are opaque, so each one is pinned with the exact byte count
# the project was built against; the script refuses a download that does not
# match rather than silently using a different evaluation.
#
# Which library matters, and why:
#   VIII.1  is what DRAGON's DLIB_99 (draglibendfb8r1Apolib99_v5p1) is built
#           from, so a DRAGON/OpenMC comparison on VIII.1 isolates *method*
#           -- 172-group deterministic vs continuous-energy Monte Carlo --
#           from nuclear data.  This is the one the results in docs/report.html
#           rest on.
#   VIII.0  is kept only because the first sweep used it; two scripts in
#           openmc/ still pin it so that history stays reproducible.
#
# The depletion chain is served as chain_endfb80_pwr.xml and stored here as
# chain_endfb80_thermal.xml: it is the thermal-spectrum variant of the VIII.0
# chain (openmc.org offers a thermal and a fast version of each; this is the
# thermal one).  Renamed on arrival so the filename says which it is.
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/env.sh"

WHICH="${1:-viii.1}"
mkdir -p "$NUCDATA_DIR"
cd "$NUCDATA_DIR"

get() {                             # get <url-id> <local name> <expected bytes>
    local url="https://anl.box.com/shared/static/$1" out=$2 want=$3
    if [ -f "$out" ] && [ "$(stat -c%s "$out")" = "$want" ]; then
        echo "have $out ($want bytes)"; return
    fi
    echo "downloading $out ($(numfmt --to=iec "$want"))..."
    curl -L --fail --retry 3 -C - -o "$out.part" "$url"
    local got; got=$(stat -c%s "$out.part")
    if [ "$got" != "$want" ]; then
        echo "ERROR: $out is $got bytes, expected $want." 1>&2
        echo "       The upstream link may have been republished; check https://openmc.org/data/" 1>&2
        exit 1
    fi
    mv "$out.part" "$out"
}

case "$WHICH" in
  viii.1|all)
    get 6qr7jezzihkj9p9esl5jn19qgpujyjyz.xz endfb81_hdf5.tar.xz 9661406540
    [ -d endfb-viii.1-hdf5 ] || { echo "unpacking VIII.1..."; tar xf endfb81_hdf5.tar.xz; }
    ;;
esac
case "$WHICH" in
  viii.0|all)
    get uhbxlrx7hvxqw27psymfbhi7bx7s6u6a.xz endfb80_hdf5.tar.xz 3383607420
    [ -d endfb-viii.0-hdf5 ] || { echo "unpacking VIII.0..."; tar xf endfb80_hdf5.tar.xz; }
    ;;
esac

# The depletion chain is needed either way.
get nyezmyuofd4eqt6wzd626lqth7wvpprr.xml chain_endfb80_thermal.xml 27526672

echo
echo "NUCDATA_DIR=$NUCDATA_DIR"
for d in endfb-viii.0-hdf5 endfb-viii.1-hdf5; do
    [ -f "$d/cross_sections.xml" ] && echo "  $d/cross_sections.xml"
done
echo "  chain_endfb80_thermal.xml"
echo
echo "The tarballs are kept so a re-run verifies instead of re-downloading;"
echo "delete them once you are happy (13 GB)."
