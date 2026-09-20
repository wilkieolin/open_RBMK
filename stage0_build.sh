#!/usr/bin/env bash
set -euo pipefail

# Master Stage 0 Build Script
# Runs complete toolchain build: fetch -> build -> test -> nuclear data -> ARMI

ROOT_DIR="/home/wilkie/code/RBMK"

echo "=========================================="
echo "  RBMK-1000 Stage 0: Toolchain Build"
echo "=========================================="
echo ""

cd "${ROOT_DIR}"

# Make all scripts executable
chmod +x fetch_source.sh build_all.sh test_all.sh fetch_nuclear_data.sh setup_armi.sh

# Step 1: Fetch source
echo ">>> Step 1/5: Fetching source code..."
./fetch_source.sh

# Step 2: Build
echo ""
echo ">>> Step 2/5: Building toolchain..."
./build_all.sh

# Step 3: Test
echo ""
echo ">>> Step 3/5: Running non-regression tests..."
./test_all.sh

# Step 4: Nuclear data
echo ""
echo ">>> Step 4/5: Fetching nuclear data (minimal)..."
./fetch_nuclear_data.sh

# Step 5: ARMI
echo ""
echo ">>> Step 5/5: Setting up ARMI plugin..."
./setup_armi.sh

echo ""
echo "=========================================="
echo "  Stage 0 COMPLETE"
echo "=========================================="
echo ""
echo "Installation: ${ROOT_DIR}/install"
echo "Source: ${ROOT_DIR}/src"
echo "Build logs: ${ROOT_DIR}/build"
echo "Test results: ${ROOT_DIR}/regress"
echo "Nuclear data: ${ROOT_DIR}/nuclear-data"
echo "ARMI plugin: ${ROOT_DIR}/armi"
echo ""
echo "Next: Stage 1 - IAEA-3D Benchmark"
echo "  Create benchmark input and run with DONJON5"