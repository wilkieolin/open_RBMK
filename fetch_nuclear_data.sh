#!/usr/bin/env bash
set -euo pipefail

# Nuclear Data Fetch Script - ENDF/B-VIII.0
# Downloads and prepares nuclear data for DRAGON5

ROOT_DIR="${RBMK_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
DATA_DIR="${ROOT_DIR}/nuclear-data/endfb8"
PREFIX="${ROOT_DIR}/install"

export PATH="${PREFIX}/bin:${PATH}"
export LD_LIBRARY_PATH="${PREFIX}/lib:${LD_LIBRARY_PATH:-}"

mkdir -p "${DATA_DIR}"
cd "${DATA_DIR}"

echo "=== ENDF/B-VIII.0 Nuclear Data ==="
echo "Target: ${DATA_DIR}"
echo ""

# Option 1: Use DRAGON's built-in library getter (preferred)
if command -v dragon &>/dev/null; then
    echo "Using DRAGON LIB: module to fetch ENDF/B-VIII.0..."
    cat > get_endfb8.dra << 'EOF'
LIB:  ::  EDIT 1
    GETXSLIB  ENDF/B-VIII.0  300.0
    ;
END:
EOF
    dragon < get_endfb8.dra 2>&1 | tee get_endfb8.log
    echo "DRAGON library fetch complete."
else
    echo "DRAGON not in PATH. Skipping automated fetch."
    echo "Run this script after build_all.sh completes."
fi

# Option 2: Manual download URLs (for reference)
cat > DOWNLOAD_URLS.txt << 'EOF'
# ENDF/B-VIII.0 Nuclear Data Sources
# Primary: https://www.nndc.bnl.gov/endf/b8.0/
# NEA mirror: https://www.oecd-nea.org/dbdata/endf/endfb8/

# For DRAGON5, you need:
# 1. Neutron cross sections (ENDF-6 format)
# 2. Thermal scattering law data (S(alpha,beta))
# 3. Fission product yield data
# 4. Decay data

# Pre-processed libraries for DRAGON (if available):
# - Check NEA Data Bank for DRAGON-formatted ENDF/B-VIII.0
# - Or use IAEA's pre-processed libraries

# Approximate size: ~10 GB for full ENDF/B-VIII.0
EOF
echo "Download references saved to ${DATA_DIR}/DOWNLOAD_URLS.txt"

# Option 3: Minimal test library (for quick verification)
echo ""
echo "Creating minimal test library for verification..."
cat > minimal_lib.dra << 'EOF'
LIB:  ::  EDIT 1
    GETXSLIB  MINIMAL  300.0
    ;
END:
EOF

if command -v dragon &>/dev/null; then
    dragon < minimal_lib.dra 2>&1 | tee minimal_lib.log
fi

echo ""
echo "Nuclear data setup complete."
echo "Full ENDF/B-VIII.0: Run after DRAGON build with 'dragon < get_endfb8.dra'"
echo "Minimal test lib: ${DATA_DIR}/minimal_lib.log"