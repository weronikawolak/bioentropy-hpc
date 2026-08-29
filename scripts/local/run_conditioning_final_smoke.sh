#!/usr/bin/env bash

set -euo pipefail

ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/../.."
    pwd
)"

cd "${ROOT}"

CONFIG_DIR="configs/generated/conditioning-final-smoke"

SOURCES=(
    logistic
    rule30
    rule90
    dna
    chacha20
)

for source in "${SOURCES[@]}"
do
    echo
    echo "========================================"
    echo "SOURCE: ${source}"
    echo "========================================"

    ./build/bioentropy-runner \
        --config \
        "${CONFIG_DIR}/${source}-raw.yaml"

    ./build/bioentropy-runner \
        --config \
        "${CONFIG_DIR}/${source}-ascon.yaml"
done

echo
echo "All 10 conditioning executions finished."
