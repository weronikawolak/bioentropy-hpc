#!/usr/bin/env bash

#SBATCH --job-name=bioentropy-dieharder
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=02:00:00
#SBATCH --output=results/slurm/dieharder-%A_%a.out
#SBATCH --error=results/slurm/dieharder-%A_%a.err

set -euo pipefail

ROOT="${BIOENTROPY_ROOT:-${SLURM_SUBMIT_DIR:-$PWD}}"
TAG="${BIOENTROPY_RESULT_TAG:-main}"

cd "${ROOT}"

MANIFEST="configs/generated/dieharder-campaign/manifest.tsv"
RESULT_DIR="results/external/dieharder-campaign-${TAG}"

test -f "${MANIFEST}" || {
    echo "Missing manifest: ${MANIFEST}"
    exit 1
}

test -x ./build/bioentropy-runner || {
    echo "Missing build/bioentropy-runner"
    exit 1
}

command -v dieharder >/dev/null || {
    echo "dieharder not available"
    exit 1
}

TOTAL="$(
    awk 'END {print NR - 1}' "${MANIFEST}"
)"

if [[ "${TOTAL}" -ne 200 ]]; then
    echo "Expected 200 manifest entries, found ${TOTAL}"
    exit 1
fi

INDEX="${SLURM_ARRAY_TASK_ID:?Missing SLURM_ARRAY_TASK_ID}"

if (( INDEX < 0 || INDEX >= TOTAL )); then
    echo "Invalid array index: ${INDEX}"
    exit 1
fi

ROW="$(
    awk -F '\t' \
      -v target="$((INDEX + 2))" \
      'NR == target {print; exit}' \
      "${MANIFEST}"
)"

GROUP="$(printf '%s\n' "${ROW}" | cut -f1)"
REP_ID="$(printf '%s\n' "${ROW}" | cut -f2)"
CONFIG="$(printf '%s\n' "${ROW}" | cut -f3)"

REP="$(
    printf 'rep%03d' "${REP_ID}"
)"

LABEL="${GROUP}-${REP}"

mkdir -p \
    "${RESULT_DIR}" \
    results/slurm

echo "Index  : ${INDEX}"
echo "Group  : ${GROUP}"
echo "Rep    : ${REP_ID}"
echo "Config : ${CONFIG}"
echo "Label  : ${LABEL}"
echo "Host   : $(hostname)"

SCRATCH_ROOT="${
    SLURM_TMPDIR:-${TMPDIR:-${ROOT}/results/bitstreams/hpc-tmp}
}"

WORK_DIR="${
    SCRATCH_ROOT
}/bioentropy-${SLURM_JOB_ID}-${INDEX}"

mkdir -p "${WORK_DIR}"

trap 'rm -rf "${WORK_DIR}"' EXIT

BITSTREAM="${WORK_DIR}/${LABEL}.bin"

TASK_START_NS="$(date +%s%N)"
START_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

./build/bioentropy-runner \
    --config "${CONFIG}" \
    --dump-bitstream "${BITSTREAM}"

BYTES="$(wc -c < "${BITSTREAM}")"

if [[ "${BYTES}" -ne 16777216 ]]; then
    echo "Unexpected bitstream size: ${BYTES}"
    exit 1
fi

SHA256="$(
    sha256sum "${BITSTREAM}" \
    | awk '{print $1}'
)"

TESTS=(
    0 2 4 8 9
    15 16
    100 101 102
)

for TEST in "${TESTS[@]}"
do
    OUTPUT="${RESULT_DIR}/${LABEL}-d${TEST}.txt"
    META="${OUTPUT}.meta.tsv"

    TEST_START_NS="$(date +%s%N)"

    set +e

    dieharder \
        -g 201 \
        -f "${BITSTREAM}" \
        -d "${TEST}" \
        -p 1 \
        > "${OUTPUT}" \
        2>&1

    EXIT_CODE=$?

    set -e

    TEST_END_NS="$(date +%s%N)"

    ELAPSED_MS="$(
        echo "$((TEST_END_NS - TEST_START_NS)) / 1000000" \
        | bc
    )"

    {
        printf 'exit_code\t%s\n' "${EXIT_CODE}"
        printf 'elapsed_ms\t%s\n' "${ELAPSED_MS}"
    } > "${META}"
done

TASK_END_NS="$(date +%s%N)"
END_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

TASK_MS="$(
    echo "$((TASK_END_NS - TASK_START_NS)) / 1000000" \
    | bc
)"

TASK_META="${RESULT_DIR}/${LABEL}.task.tsv"

{
    printf 'field\tvalue\n'
    printf 'source_group\t%s\n' "${GROUP}"
    printf 'replicate_id\t%s\n' "${REP_ID}"
    printf 'config\t%s\n' "${CONFIG}"
    printf 'array_task_id\t%s\n' "${INDEX}"
    printf 'job_id\t%s\n' "${SLURM_JOB_ID}"
    printf 'hostname\t%s\n' "$(hostname)"
    printf 'cpus_per_task\t%s\n' "${SLURM_CPUS_PER_TASK:-1}"
    printf 'start_utc\t%s\n' "${START_UTC}"
    printf 'end_utc\t%s\n' "${END_UTC}"
    printf 'elapsed_ms\t%s\n' "${TASK_MS}"
    printf 'bitstream_bytes\t%s\n' "${BYTES}"
    printf 'bitstream_sha256\t%s\n' "${SHA256}"
} > "${TASK_META}"

echo
echo "Completed: ${LABEL}"
echo "Elapsed  : ${TASK_MS} ms"
