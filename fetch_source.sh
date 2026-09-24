#!/usr/bin/env bash
set -euo pipefail

# DRAGON5/DONJON5 Source Fetch Script
# Downloads from NEA GitLab: https://git.oecd-nea.org/dragon
# REQUIRES: NEA Data Bank access with Personal Access Token
#   Export NEA_TOKEN=your_token before running
#   Or: git config --global credential.helper store  (then enter credentials once)

ROOT_DIR="${RBMK_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
SRC_DIR="${ROOT_DIR}/src"
NEA_BASE="https://git.oecd-nea.org"

# Package repositories (NEA GitLab structure)
declare -A REPOS=(
    ["ganlib5"]="ganlib5/ganlib5.git"
    ["utilib"]="utilib/utilib.git"
    ["dragon5"]="dragon5/dragon5.git"
    ["trivac5"]="trivac5/trivac5.git"
    ["donjon5"]="donjon5/donjon5.git"
)

# Target version/tag
TARGET_VERSION="${TARGET_VERSION:-5.1.0}"

# Build authenticated URL if token provided
build_url() {
    local path=$1
    if [[ -n "${NEA_TOKEN:-}" ]]; then
        echo "https://oauth2:${NEA_TOKEN}@git.oecd-nea.org/${path}"
    else
        echo "https://git.oecd-nea.org/${path}"
    fi
}

mkdir -p "${SRC_DIR}"
cd "${SRC_DIR}"

echo "=== DRAGON5/DONJON5 Source Fetch ==="
echo "Root: ${ROOT_DIR}"
echo "Target version: ${TARGET_VERSION}"
if [[ -n "${NEA_TOKEN:-}" ]]; then
    echo "Authentication: Using NEA_TOKEN"
else
    echo "Authentication: None (will prompt for credentials)"
fi
echo ""

fetch_repo() {
    local name=$1
    local path=$2
    local url=$(build_url "${path}")

    if [[ -d "${name}/.git" ]]; then
        echo "[${name}] Already cloned, fetching updates..."
        cd "${name}"
        git fetch --all --tags --prune
        cd ..
    else
        echo "[${name}] Cloning from NEA..."
        if git clone "${url}" "${name}"; then
            echo "[${name}] Cloned successfully"
        else
            echo "[${name}] ERROR: Clone failed"
            echo "  URL: ${url}"
            echo "  Ensure NEA_TOKEN is set or credentials are configured"
            return 1
        fi
    fi

    cd "${name}"
    echo "[${name}] Available tags:"
    git tag -l "5.*" | tail -10

    if git rev-parse "v${TARGET_VERSION}" >/dev/null 2>&1; then
        git checkout "v${TARGET_VERSION}"
        echo "[${name}] Checked out v${TARGET_VERSION}"
    elif git rev-parse "${TARGET_VERSION}" >/dev/null 2>&1; then
        git checkout "${TARGET_VERSION}"
        echo "[${name}] Checked out ${TARGET_VERSION}"
    else
        echo "[${name}] WARNING: Tag ${TARGET_VERSION} not found, using latest"
        git checkout main 2>/dev/null || git checkout master 2>/dev/null
    fi

    local commit=$(git rev-parse --short HEAD)
    local date=$(git log -1 --format=%ci HEAD)
    echo "[${name}] HEAD: ${commit} (${date})"
    cd ..
}

# Fetch all repositories
failed=()
for name in ganlib5 utilib dragon5 trivac5 donjon5; do
    if ! fetch_repo "${name}" "${REPOS[${name}]}"; then
        failed+=("${name}")
    fi
done

echo ""
echo "=== Fetch Summary ==="
if [[ ${#failed[@]} -eq 0 ]]; then
    echo "All repositories fetched successfully."
else
    echo "Failed: ${failed[*]}"
    echo "Manual intervention required for failed repos."
    exit 1
fi

# Verify structure
echo ""
echo "=== Source Tree ==="
find "${SRC_DIR}" -maxdepth 2 -name "configure*" -o -name "CMakeLists.txt" -o -name "Makefile*" | head -20

# Check for install scripts in doc directories
echo ""
echo "=== Install Scripts ==="
for name in ganlib5 utilib dragon5 trivac5 donjon5; do
    if [[ -d "${SRC_DIR}/${name}/doc" ]]; then
        find "${SRC_DIR}/${name}/doc" -name "install*" -type f 2>/dev/null | head -3
    fi
done

echo ""
echo "Done. Next: run build_all.sh"