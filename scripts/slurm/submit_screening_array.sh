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

MANIFEST="configs/generated/screening/manifest.tsv"

if ! command -v sbatch >/dev/null 2>&1; then
    echo "ERROR: sbatch command not found."
    echo "Run this script on the SLURM cluster."
    exit 1
fi

if [ ! -f "${MANIFEST}" ]; then
    echo "ERROR: screening manifest missing:"
    echo "${MANIFEST}"
    exit 1
fi

TASKS="$(
    tail -n +2 "${MANIFEST}" |
    wc -l
)"

if [ "${TASKS}" -ne 2100 ]; then
    echo "ERROR: expected 2100 tasks."
    echo "Found: ${TASKS}"
    exit 1
fi

mkdir -p \
    results/logs/screening \
    results/metrics

MAX_CONCURRENT=64

echo "Submitting BioEntropy screening campaign"
echo "Tasks          : ${TASKS}"
echo "Array range    : 0-$((TASKS - 1))"
echo "Max concurrent : ${MAX_CONCURRENT}"
echo

sbatch \
    --array="0-$((TASKS - 1))%${MAX_CONCURRENT}" \
    scripts/slurm/run_screening_array.sh
