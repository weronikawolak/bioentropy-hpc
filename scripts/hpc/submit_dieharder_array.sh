#!/usr/bin/env bash

set -euo pipefail

ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/../.."
    pwd
)"

cd "${ROOT}"

MAX_PARALLEL="${1:?Usage: $0 PARALLEL [TAG] [TASKS]}"
TAG="${2:-p${MAX_PARALLEL}}"
TASKS="${3:-200}"

case "${MAX_PARALLEL}" in
    1|2|4|8|16|32)
        ;;
    *)
        echo "PARALLEL must be one of: 1 2 4 8 16 32"
        exit 1
        ;;
esac

if (( TASKS < 1 || TASKS > 200 )); then
    echo "TASKS must be between 1 and 200"
    exit 1
fi

MANIFEST="configs/generated/dieharder-campaign/manifest.tsv"

TOTAL="$(
    awk 'END {print NR - 1}' "${MANIFEST}"
)"

if [[ "${TOTAL}" -ne 200 ]]; then
    echo "Expected 200 configs, found ${TOTAL}"
    exit 1
fi

mkdir -p results/slurm

LAST="$((TASKS - 1))"

echo "Submitting BioEntropy Dieharder campaign"
echo "Tasks       : ${TASKS}"
echo "Concurrency : ${MAX_PARALLEL}"
echo "Tag         : ${TAG}"
echo "Array       : 0-${LAST}%${MAX_PARALLEL}"

sbatch \
    --array="0-${LAST}%${MAX_PARALLEL}" \
    --export="ALL,BIOENTROPY_ROOT=${ROOT},BIOENTROPY_RESULT_TAG=${TAG}" \
    scripts/hpc/run_dieharder_array.sbatch
