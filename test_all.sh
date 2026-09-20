#!/usr/bin/env bash
set -euo pipefail

# Non-Regression Test Runner for DRAGON5/DONJON5

ROOT_DIR="/home/wilkie/code/RBMK"
BUILD_DIR="${ROOT_DIR}/build"
PREFIX="${ROOT_DIR}/install"
REGRESS_DIR="${ROOT_DIR}/regress"
NJOBS="${NJOBS:-$(nproc)}"

export PATH="${PREFIX}/bin:${PATH}"
export LD_LIBRARY_PATH="${PREFIX}/lib:${LD_LIBRARY_PATH:-}"

mkdir -p "${REGRESS_DIR}"

echo "=== Non-Regression Test Suite ==="
echo "Results: ${REGRESS_DIR}"
echo ""

run_test() {
    local name=$1
    local build="${BUILD_DIR}/${name}"
    local log="${REGRESS_DIR}/${name}_test.log"

    if [[ ! -d "${build}" ]]; then
        echo "[${name}] SKIP: Build directory not found"
        return 0
    fi

    echo "[${name}] Running tests..."
    cd "${build}"

    # Capture output
    if make check 2>&1 | tee "${log}"; then
        echo "[${name}] PASSED"
        return 0
    else
        echo "[${name}] FAILED (see ${log})"
        return 1
    fi
}

# Test each package
failed=()

for pkg in ganlib5 utilib dragon5 trivac5 donjon5; do
    if ! run_test "${pkg}"; then
        failed+=("${pkg}")
    fi
done

echo ""
echo "=== Test Summary ==="
if [[ ${#failed[@]} -eq 0 ]]; then
    echo "All test suites PASSED."
else
    echo "FAILED: ${failed[*]}"
    echo ""
    echo "Details:"
    for pkg in "${failed[@]}"; do
        echo "  ${pkg}: ${REGRESS_DIR}/${pkg}_test.log"
        tail -20 "${REGRESS_DIR}/${pkg}_test.log" | head -10
    done
    exit 1
fi

# Quick functional verification
echo ""
echo "=== Functional Verification ==="
cd "${REGRESS_DIR}"

# Test DRAGON can start
if "${PREFIX}/bin/dragon" <<< "END" 2>&1 | grep -q "DRAGON"; then
    echo "DRAGON executable: OK"
else
    echo "DRAGON executable: FAIL"
    failed+=("dragon_exec")
fi

# Test DONJON can start
if "${PREFIX}/bin/donjon" <<< "END" 2>&1 | grep -q "DONJON"; then
    echo "DONJON executable: OK"
else
    echo "DONJON executable: FAIL"
    failed+=("donjon_exec")
fi

if [[ ${#failed[@]} -eq 0 ]]; then
    echo ""
    echo "All verifications PASSED. Ready for Stage 1 (IAEA-3D benchmark)."
else
    echo ""
    echo "Verifications FAILED: ${failed[*]}"
    exit 1
fi