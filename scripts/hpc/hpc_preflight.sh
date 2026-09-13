#!/usr/bin/env bash

set -euo pipefail

REQUIRE_SLURM=0
STRICT_CLEAN=0

for arg in "$@"; do
    case "$arg" in
        --require-slurm)
            REQUIRE_SLURM=1
            ;;
        --strict-clean)
            STRICT_CLEAN=1
            ;;
        *)
            echo "Unknown argument: $arg" >&2
            exit 2
            ;;
    esac
done

ROOT="$(
    git rev-parse --show-toplevel
)"

cd "$ROOT"

echo "BioEntropy HPC preflight"
echo "========================"
echo
echo "date_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "git_commit=$(git rev-parse HEAD)"
echo "hostname=$(hostname)"
echo

echo "=== Git ==="

if [[ -n "$(git status --porcelain)" ]]; then
    echo "WARN: working tree is not clean"
    git status --short

    if [[ "$STRICT_CLEAN" -eq 1 ]]; then
        echo "ERROR: --strict-clean requested"
        exit 1
    fi
else
    echo "PASS: clean working tree"
fi

echo

echo "=== Toolchain ==="

for cmd in \
    git \
    cmake \
    ninja \
    c++ \
    python3 \
    openssl \
    pkg-config
do
    if command -v "$cmd" >/dev/null 2>&1; then
        echo "PASS: $cmd"
    else
        echo "ERROR: missing $cmd"
        exit 1
    fi
done

echo

cmake --version | head -1
c++ --version | head -1
python3 --version
openssl version

echo

echo "=== Libraries ==="

for pkg in openssl mpfr gmp; do
    if pkg-config --exists "$pkg"; then
        echo \
            "PASS: $pkg =" \
            "$(pkg-config --modversion "$pkg")"
    else
        echo "ERROR: missing library: $pkg"
        exit 1
    fi
done

echo

echo "=== Slurm ==="

SLURM_OK=1

for cmd in sbatch srun sinfo; do
    if command -v "$cmd" >/dev/null 2>&1; then
        echo "PASS: $cmd"
    else
        echo "INFO: $cmd unavailable"
        SLURM_OK=0
    fi
done

if [[ "$REQUIRE_SLURM" -eq 1 && "$SLURM_OK" -ne 1 ]]; then
    echo "ERROR: Slurm required but unavailable"
    exit 1
fi

if [[ "$SLURM_OK" -eq 1 ]]; then
    sinfo --version || true
    sinfo -s || true
fi

echo

echo "=== Release build ==="

cmake \
    -S . \
    -B build \
    -G Ninja \
    -DCMAKE_BUILD_TYPE=Release

cmake \
    --build build \
    --parallel

ctest \
    --test-dir build \
    --output-on-failure

echo

echo "PASSED: HPC preflight"
