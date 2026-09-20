#!/usr/bin/env bash
set -euo pipefail

# DRAGON5/DONJON5 Build Script
# Builds in dependency order: GANLIB5 -> UTILIB -> DRAGON5 -> TRIVAC5 -> DONJON5

ROOT_DIR="/home/wilkie/code/RBMK"
SRC_DIR="${ROOT_DIR}/src"
BUILD_DIR="${ROOT_DIR}/build"
PREFIX="${ROOT_DIR}/install"
NJOBS="${NJOBS:-$(nproc)}"

export FC=gfortran
export CC=gcc
export CXX=g++
export FCFLAGS="-O2 -fPIC -fallow-argument-mismatch -fno-range-check -std=f2003"
export CFLAGS="-O2 -fPIC"
export CXXFLAGS="-O2 -fPIC"
export LDFLAGS="-L${PREFIX}/lib -Wl,-rpath,${PREFIX}/lib"
export CPPFLAGS="-I${PREFIX}/include"

# HDF5 paths (Ubuntu 24.04)
export HDF5_DIR="/usr/lib/aarch64-linux-gnu/hdf5/serial"
export CPPFLAGS="${CPPFLAGS} -I${HDF5_DIR}/include"
export LDFLAGS="${LDFLAGS} -L${HDF5_DIR}/lib"

mkdir -p "${BUILD_DIR}" "${PREFIX}"

echo "=== Build Configuration ==="
echo "Prefix: ${PREFIX}"
echo "Jobs: ${NJOBS}"
echo "FC: ${FC} $(${FC} --version | head -1)"
echo "HDF5: ${HDF5_DIR}"
echo ""

build_package() {
    local name=$1
    local src="${SRC_DIR}/${name}"
    local build="${BUILD_DIR}/${name}"
    shift
    local extra_args=("$@")

    if [[ ! -d "${src}" ]]; then
        echo "ERROR: Source not found: ${src}"
        return 1
    fi

    echo "=== Building ${name} ==="
    mkdir -p "${build}"
    cd "${build}"

    # Clean previous failed attempts
    [[ -f "Makefile" ]] && make distclean 2>/dev/null || true

    # Configure
    echo "[${name}] Configuring..."
    "${src}/configure" \
        --prefix="${PREFIX}" \
        --enable-shared \
        --disable-static \
        "${extra_args[@]}" \
        2>&1 | tee configure.log

    # Build
    echo "[${name}] Building (make -j${NJOBS})..."
    make -j"${NJOBS}" 2>&1 | tee build.log

    # Install
    echo "[${name}] Installing..."
    make install 2>&1 | tee install.log

    echo "[${name}] Done."
    cd "${ROOT_DIR}"
}

run_tests() {
    local name=$1
    local build="${BUILD_DIR}/${name}"

    echo "=== Testing ${name} ==="
    cd "${build}"
    make check 2>&1 | tee test.log
    cd "${ROOT_DIR}"
}

# Build sequence with package-specific flags
echo "Starting build sequence..."
echo ""

# 1. GANLIB5 - Foundation library
build_package ganlib5 \
    --with-hdf5="${HDF5_DIR}" \
    --enable-fortran2003

# 2. UTILIB - Utility library (depends on GANLIB5)
build_package utilib \
    --with-ganlib="${PREFIX}"

# 3. DRAGON5 - Lattice code (depends on GANLIB5, UTILIB)
build_package dragon5 \
    --with-ganlib="${PREFIX}" \
    --with-utilib="${PREFIX}" \
    --enable-openmp

# 4. TRIVAC5 - Transport/kinetics (depends on GANLIB5, DRAGON5)
build_package trivac5 \
    --with-ganlib="${PREFIX}" \
    --with-dragon="${PREFIX}"

# 5. DONJON5 - Core simulator (depends on all above)
build_package donjon5 \
    --with-ganlib="${PREFIX}" \
    --with-trivac="${PREFIX}" \
    --with-dragon="${PREFIX}"

echo ""
echo "=== All packages built ==="
echo "Installation: ${PREFIX}"
echo ""
echo "Verifying executables..."
for exe in dragon donjon; do
    if [[ -x "${PREFIX}/bin/${exe}" ]]; then
        echo "  ${exe}: OK"
        "${PREFIX}/bin/${exe}" --version 2>/dev/null || "${PREFIX}/bin/${exe}" -v 2>/dev/null || true
    else
        echo "  ${exe}: NOT FOUND"
    fi
done

echo ""
echo "Run tests with: ./test_all.sh"