#!/usr/bin/env bash

set -u

ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/../.."
    pwd
)"

cd "${ROOT}"

INPUT_DIR="results/bitstreams/dieharder-smoke"
OUTPUT_DIR="results/external/dieharder-screening"

mkdir -p "${OUTPUT_DIR}"

SOURCES=(
    chen
    logistic-float64
    rule90
    chacha20
)

TESTS=(
    0
    2
    4
    8
    9
    15
    16
    100
    101
    102
)

for source in "${SOURCES[@]}"
do
    input="${INPUT_DIR}/${source}.bin"

    if [[ ! -f "${input}" ]]; then
        echo "Missing input: ${input}"
        exit 1
    fi

    for test in "${TESTS[@]}"
    do
        output="${OUTPUT_DIR}/${source}-d${test}.txt"

        echo
        echo "========================================"
        echo "source=${source} test=${test}"
        echo "========================================"

        dieharder \
            -g 201 \
            -f "${input}" \
            -d "${test}" \
            -p 1 \
            2>&1 \
            | tee "${output}"

        exit_code=${PIPESTATUS[0]}

        printf '%s\n' \
            "${exit_code}" \
            > "${output}.exit"
    done
done

echo
echo "Dieharder screening finished."
