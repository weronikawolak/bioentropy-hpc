#!/usr/bin/env bash

set -euo pipefail

echo "BioEntropy HPC environment check"
echo "================================"

REQUIRED=(
    git
    cmake
    ninja
    g++
    python3
    sbatch
    squeue
)

FAILED=0

for cmd in "${REQUIRED[@]}"; do
    if command -v "${cmd}" >/dev/null 2>&1; then
        printf "%-12s OK  %s\n" \
            "${cmd}" \
            "$(command -v "${cmd}")"
    else
        printf "%-12s MISSING\n" "${cmd}"
        FAILED=1
    fi
done

echo

if command -v g++ >/dev/null 2>&1; then
    echo "Compiler:"
    g++ --version | head -1
fi

if command -v cmake >/dev/null 2>&1; then
    echo "CMake:"
    cmake --version | head -1
fi

if command -v sbatch >/dev/null 2>&1; then
    echo "SLURM:"
    sbatch --version
fi

echo

if [ "${FAILED}" -ne 0 ]; then
    echo "FAILED: required commands are missing."
    exit 1
fi

echo "PASSED: basic HPC toolchain is available."
