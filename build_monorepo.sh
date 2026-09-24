#!/usr/bin/env bash
set -euo pipefail

# Build script for DRAGON5/DONJON5 monorepo in the 5.1 submodule
# Uses the native Makefile system with environment variable controls

ROOT_DIR="${RBMK_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
MONOREPO="${ROOT_DIR}/5.1"
BUILD_DIR="${ROOT_DIR}/build"
PREFIX="${ROOT_DIR}/install"

# HDF5 paths (Ubuntu 24.04)
export HDF5_INC="/usr/include/hdf5/serial"
MULTIARCH="$(gcc -print-multiarch 2>/dev/null || echo "$(uname -m)-linux-gnu")"
export HDF5_API="/usr/lib/${MULTIARCH}/hdf5/serial"

# Build configuration
export openmp=1
export hdf5=1
export intel=0
export nvidia=0
export llvm=0

# Compiler selection (gfortran/gcc default)
export FC=gfortran
export CC=gcc

# Parallel jobs
NJOBS="${NJOBS:-$(nproc)}"

mkdir -p "${BUILD_DIR}" "${PREFIX}/bin" "${PREFIX}/lib" "${PREFIX}/include"

echo "=== DRAGON5/DONJON5 Monorepo Build ==="
echo "Monorepo: ${MONOREPO}"
echo "Install prefix: ${PREFIX}"
echo "HDF5_INC: ${HDF5_INC}"
echo "HDF5_API: ${HDF5_API}"
echo "OpenMP: ${openmp}"
echo "Jobs: ${NJOBS}"
echo ""

# The monorepo Makefiles build everything via sub-make from Donjon/src
# We just need to run make in Donjon/src with the right environment
cd "${MONOREPO}/Donjon/src"

echo "Building all packages (Ganlib -> Utilib -> Trivac -> Dragon -> Donjon)..."
make -j"${NJOBS}" 2>&1 | tee "${BUILD_DIR}/build.log"

echo ""
echo "Build complete. Checking executables..."

# Find the built executables (they're in bin/<DIRNAME>/)
DIRNAME="Linux_aarch64"
for pkg in Ganlib Utilib Trivac Dragon Donjon; do
    exe="${MONOREPO}/${pkg}/bin/${DIRNAME}/${pkg}"
    if [[ -x "${exe}" ]]; then
        echo "  ${pkg}: OK at ${exe}"
        # Copy to install prefix
        cp "${exe}" "${PREFIX}/bin/${pkg,,}"
    else
        echo "  ${pkg}: NOT FOUND at ${exe}"
        # Try to find it
        find "${MONOREPO}/${pkg}/bin" -name "${pkg}" -executable 2>/dev/null | head -3
    fi
done

# Copy libraries and modules
for pkg in Ganlib Utilib Trivac Dragon Donjon; do
    libdir="${MONOREPO}/${pkg}/lib/${DIRNAME}"
    if [[ -d "${libdir}" ]]; then
        cp -r "${libdir}"/* "${PREFIX}/lib/" 2>/dev/null || true
    fi
    moddir="${MONOREPO}/${pkg}/lib/${DIRNAME}/modules"
    if [[ -d "${moddir}" ]]; then
        cp -r "${moddir}"/* "${PREFIX}/include/" 2>/dev/null || true
    fi
done

echo ""
echo "Installation: ${PREFIX}"
echo "Binaries: ${PREFIX}/bin/"
echo "Libraries: ${PREFIX}/lib/"
echo "Modules: ${PREFIX}/include/"
echo ""
echo "Run tests with: ./test_monorepo.sh"