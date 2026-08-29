#!/usr/bin/env bash

set -euo pipefail

ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/../.."
    pwd
)"

cd "${ROOT}"

CONFIG_DIR="${1:-configs/generated/dieharder-campaign-smoke}"

RESULT_DIR="${2:-results/external/dieharder-campaign-smoke}"

BITSTREAM_DIR="${3:-results/bitstreams/dieharder-campaign-smoke}"

KEEP_BITSTREAMS="${KEEP_BITSTREAMS:-0}"

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

mkdir -p \
    "${RESULT_DIR}" \
    "${BITSTREAM_DIR}"

mapfile -t configs < <(
    find "${CONFIG_DIR}" \
        -mindepth 2 \
        -maxdepth 2 \
        -name 'rep*.yaml' \
        -type f \
        | sort
)

if [[ ${#configs[@]} -eq 0 ]]; then
    echo "No campaign configs found."
    exit 1
fi

echo "Campaign configs: ${#configs[@]}"

for config in "${configs[@]}"
do
    group="$(
        basename "$(dirname "${config}")"
    )"

    replicate="$(
        basename "${config}" .yaml
    )"

    label="${group}-${replicate}"

    bitstream="${BITSTREAM_DIR}/${label}.bin"

    echo
    echo "========================================"
    echo "${label}"
    echo "========================================"

    ./build/bioentropy-runner \
        --config "${config}" \
        --dump-bitstream "${bitstream}"

    size="$(
        wc -c < "${bitstream}"
    )"

    if [[ "${size}" -ne 16777216 ]]; then
        echo "Unexpected bitstream size: ${size}"
        exit 1
    fi

    sha256sum \
        "${bitstream}" \
        > "${RESULT_DIR}/${label}.sha256"

    for test in "${TESTS[@]}"
    do
        output="${RESULT_DIR}/${label}-d${test}.txt"

        set +e

        dieharder \
            -g 201 \
            -f "${bitstream}" \
            -d "${test}" \
            -p 1 \
            > "${output}" \
            2>&1

        exit_code=$?
        set -e

        printf '%s\n' \
            "${exit_code}" \
            > "${output}.exit"
    done

    if [[ "${KEEP_BITSTREAMS}" != "1" ]]; then
        rm -f "${bitstream}"
    fi
done

echo
echo "Dieharder campaign finished."
