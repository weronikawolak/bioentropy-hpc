#!/usr/bin/env bash

#SBATCH --job-name=bioentropy-screen
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:10:00
#SBATCH --output=results/logs/screening/%A_%a.out
#SBATCH --error=results/logs/screening/%A_%a.err

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
RUNNER="build/bioentropy-runner"

TASK_ID="${SLURM_ARRAY_TASK_ID:-${1:-}}"

if [ -z "${TASK_ID}" ]; then
    echo "ERROR: no task ID supplied."
    echo
    echo "Use either:"
    echo "  SLURM_ARRAY_TASK_ID=<id> $0"
    echo "or:"
    echo "  $0 <id>"
    exit 1
fi

if ! [[ "${TASK_ID}" =~ ^[0-9]+$ ]]; then
    echo "ERROR: task ID must be an integer."
    exit 1
fi

if [ ! -f "${MANIFEST}" ]; then
    echo "ERROR: manifest not found:"
    echo "${MANIFEST}"
    exit 1
fi

if [ ! -x "${RUNNER}" ]; then
    echo "ERROR: runner not found:"
    echo "${RUNNER}"
    exit 1
fi

TOTAL_TASKS="$(
    tail -n +2 "${MANIFEST}" |
    wc -l
)"

if [ "${TASK_ID}" -ge "${TOTAL_TASKS}" ]; then
    echo "ERROR: task ID ${TASK_ID} outside range."
    echo "Valid range: 0-$((TOTAL_TASKS - 1))"
    exit 1
fi

MANIFEST_LINE=$((TASK_ID + 2))

CONFIG_FILE="$(
    awk \
        -F $'\t' \
        -v line="${MANIFEST_LINE}" \
        'NR == line { gsub(/\\r$/, "", $11); print $11 }' \
        "${MANIFEST}"
)"

if [ -z "${CONFIG_FILE}" ]; then
    echo "ERROR: could not resolve config for task."
    exit 1
fi

if [ ! -f "${CONFIG_FILE}" ]; then
    echo "ERROR: config file does not exist:"
    echo "${CONFIG_FILE}"
    exit 1
fi

mkdir -p results/logs/screening

echo "BioEntropy HPC screening task"
echo "============================="
echo "SLURM job ID   : ${SLURM_JOB_ID:-local}"
echo "Array task ID  : ${TASK_ID}"
echo "Total tasks    : ${TOTAL_TASKS}"
echo "Config         : ${CONFIG_FILE}"
echo "Host           : $(hostname)"
echo "Started        : $(date --iso-8601=seconds)"
echo

"${RUNNER}" \
    --config "${CONFIG_FILE}"

echo
echo "Finished       : $(date --iso-8601=seconds)"
echo "Task ${TASK_ID} completed successfully."
