#!/usr/bin/env bash
set -euo pipefail

# ARMI Plugin Setup for DRAGON5
# Installs Terrapower's dragon-armi-plugin with local DRAGON5

ROOT_DIR="/home/wilkie/code/RBMK"
ARMI_DIR="${ROOT_DIR}/armi"
PREFIX="${ROOT_DIR}/install"

echo "=== ARMI Plugin Setup ==="
echo "DRAGON5 prefix: ${PREFIX}"
echo ""

# Verify DRAGON5 is built
if [[ ! -f "${PREFIX}/bin/dragon" ]]; then
    echo "ERROR: DRAGON5 not found at ${PREFIX}/bin/dragon"
    echo "Run build_all.sh first."
    exit 1
fi

# Clone or update ARMI plugin
if [[ -d "${ARMI_DIR}/.git" ]]; then
    echo "Updating existing ARMI plugin..."
    cd "${ARMI_DIR}"
    git pull
else
    echo "Cloning ARMI plugin..."
    git clone https://github.com/terrapower/dragon-armi-plugin "${ARMI_DIR}"
    cd "${ARMI_DIR}"
fi

# Install in development mode with DRAGON5 path
echo "Installing ARMI plugin..."
pip install -e . \
    --config-settings="dragon_prefix=${PREFIX}" \
    --config-settings="dragon_version=5" \
    2>&1 | tee armi_install.log

# Verify installation
echo ""
echo "Verifying ARMI plugin..."
python3 -c "
import armi
import armi.plugins
from armi import configure
configure(armi)
print('ARMI version:', armi.__version__)

# Check dragon plugin loaded
plugins = armi.plugins.getPluginManager().getPlugins()
dragon_plugin = [p for p in plugins if 'dragon' in p.name.lower()]
if dragon_plugin:
    print('DRAGON plugin:', dragon_plugin[0].name)
else:
    print('WARNING: DRAGON plugin not found in loaded plugins')
    print('Loaded plugins:', [p.name for p in plugins])
"

# Test DRAGON interface
echo ""
echo "Testing DRAGON interface..."
python3 -c "
from armi.utils import getDragonPath
print('Dragon path:', getDragonPath())

# Try importing dragon module if available
try:
    import dragon
    print('Dragon module: OK')
except ImportError as e:
    print('Dragon module not directly importable (expected):', e)
"

echo ""
echo "ARMI setup complete."
echo "Usage: armi run <case.py> --plugin dragon"