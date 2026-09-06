#!/usr/bin/env bash

set -euo pipefail

ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/../.."
    pwd
)"

cd "${ROOT}"

CONFIG_DIR="${1:-configs/generated/dieharder-campaign}"
RESULT_DIR="${2:-results/external/dieharder-campaign}"
BITSTREAM_DIR="${3:-results/bitstreams/dieharder-campaign}"

KEEP_BITSTREAMS="${KEEP_BITSTREAMS:-0}"
RESUME="${RESUME:-1}"

TESTS=(
    0 2 4 8 9
    15 16
    100 101 102
)

mkdir -p \
    "${RESULT_DIR}" \
    "${BITSTREAM_DIR}"

mapfile -t CONFIGS < <(
    find "${CONFIG_DIR}" \
        -mindepth 2 \
        -maxdepth 2 \
        -name 'rep*.yaml' \
        -type f \
        | sort
)

if [[ ${#CONFIGS[@]} -eq 0 ]]; then
    echo "No campaign configs found."
    exit 1
fi

echo "Campaign configs : ${#CONFIGS[@]}"
echo "Resume           : ${RESUME}"
echo "Keep bitstreams  : ${KEEP_BITSTREAMS}"

for CONFIG in "${CONFIGS[@]}"
do
    GROUP="$(
        basename "$(dirname "${CONFIG}")"
    )"

    REP="$(
        basename "${CONFIG}" .yaml
    )"

    LABEL="${GROUP}-${REP}"
    BITSTREAM="${BITSTREAM_DIR}/${LABEL}.bin"
    SHA_FILE="${RESULT_DIR}/${LABEL}.sha256"

    COMPLETE=1

    for TEST in "${TESTS[@]}"
    do
        if [[ ! -f "${RESULT_DIR}/${LABEL}-d${TEST}.txt" \
           || ! -f "${RESULT_DIR}/${LABEL}-d${TEST}.txt.exit" ]]; then
            COMPLETE=0
            break
        fi
    done

    if [[ "${RESUME}" == "1" && "${COMPLETE}" == "1" ]]; then
        echo "SKIP complete: ${LABEL}"
        continue
    fi

    echo
    echo "========================================"
    echo "${LABEL}"
    echo "========================================"

    START="$(date +%s)"

    ./build/bioentropy-runner \
        --config "${CONFIG}" \
        --dump-bitstream "${BITSTREAM}"

    BYTES="$(wc -c < "${BITSTREAM}")"

    if [[ "${BYTES}" -ne 16777216 ]]; then
        echo "Unexpected bitstream size: ${BYTES}"
        exit 1
    fi

    sha256sum "${BITSTREAM}" \
        > "${SHA_FILE}"

    for TEST in "${TESTS[@]}"
    do
        OUTPUT="${RESULT_DIR}/${LABEL}-d${TEST}.txt"

        if [[ "${RESUME}" == "1" && -f "${OUTPUT}" ]]; then
            echo "  skip d${TEST}"
            continue
        fi

        echo "  run  d${TEST}"

        set +e

        dieharder \
            -g 201 \
            -f "${BITSTREAM}" \
            -d "${TEST}" \
            -p 1 \
            > "${OUTPUT}.tmp" \
            2>&1

        EXIT_CODE=$?

        set -e

        mv -f \
            "${OUTPUT}.tmp" \
            "${OUTPUT}"

        printf '%s\n' "${EXIT_CODE}" \
            > "${OUTPUT}.exit.tmp"

        mv -f \
            "${OUTPUT}.exit.tmp" \
            "${OUTPUT}.exit"
    done

    END="$(date +%s)"

    {
        printf 'label\t%s\n' "${LABEL}"
        printf 'elapsed_seconds\t%s\n' "$((END - START))"
        printf 'bitstream_bytes\t%s\n' "${BYTES}"
    } > "${RESULT_DIR}/${LABEL}.task.tsv"

    if [[ "${KEEP_BITSTREAMS}" != "1" ]]; then
        rm -f "${BITSTREAM}"
    fi
done

echo
echo "Dieharder campaign finished."
