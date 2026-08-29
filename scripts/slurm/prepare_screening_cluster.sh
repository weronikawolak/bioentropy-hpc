#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(
    cd "$(dirname "${BASH_SOURCE[0]}")"
    pwd
)"

ROOT="$(
    cd "${SCRIPT_DIR}/../.."
    pwd
)"

cd "${ROOT}"

echo "BioEntropy HPC screening preparation"
echo "====================================="

REQUIRED=(
    cmake
    ninja
    g++
    python3
)

for cmd in "${REQUIRED[@]}"; do
    if ! command -v "${cmd}" >/dev/null 2>&1; then
        echo "ERROR: missing command: ${cmd}"
        exit 1
    fi
done

echo
echo "[1/5] Configure Release build"

cmake \
    -S . \
    -B build \
    -G Ninja \
    -DCMAKE_BUILD_TYPE=Release

echo
echo "[2/5] Build"

cmake \
    --build build \
    --parallel

echo
echo "[3/5] Run tests"

ctest \
    --test-dir build \
    --output-on-failure

echo
echo "[4/5] Generate screening campaign"

python3 \
    scripts/preprocessing/generate_screening_campaign.py

MANIFEST="configs/generated/screening/manifest.tsv"

if [ ! -f "${MANIFEST}" ]; then
    echo "ERROR: manifest was not generated."
    exit 1
fi

TASKS="$(
    tail -n +2 "${MANIFEST}" |
    wc -l
)"

if [ "${TASKS}" -ne 2100 ]; then
    echo "ERROR: expected 2100 screening tasks."
    echo "Found: ${TASKS}"
    exit 1
fi

echo
echo "[5/5] Validate scripts"

bash -n \
    scripts/slurm/run_screening_array.sh

bash -n \
    scripts/slurm/submit_screening_array.sh

python3 -m py_compile \
    scripts/preprocessing/generate_screening_campaign.py \
    analysis/scripts/check_screening_campaign.py

mkdir -p \
    results/metrics \
    results/logs/screening \
    results/aggregated

echo
echo "Preparation complete."
echo "Generated tasks : ${TASKS}"
echo "Runner          : build/bioentropy-runner"
echo "Manifest        : ${MANIFEST}"
