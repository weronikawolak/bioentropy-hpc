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

STAMP="$(
    date -u +%Y%m%dT%H%M%SZ
)"

OUT_DIR="results/hpc/preflight"
OUT="${OUT_DIR}/preflight_${STAMP}.txt"

mkdir -p "$OUT_DIR"

exec > >(
    tee "$OUT"
) 2>&1


echo "BioEntropy HPC preflight"
echo "========================"
echo
echo "date_utc=$(date -u --iso-8601=seconds)"
echo "root=$ROOT"
echo "git_commit=$(git rev-parse HEAD)"
echo "hostname=$(hostname)"
echo


echo "=== OS ==="
uname -a
echo


echo "=== CPU ==="
if command -v lscpu >/dev/null 2>&1; then
    lscpu
else
    echo "WARN: lscpu unavailable"
fi
echo


echo "=== Git state ==="

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


echo "=== Required commands ==="

REQUIRED=(
    git
    cmake
    ninja
    c++
    python3
    openssl
    pkg-config
)

for cmd in "${REQUIRED[@]}"; do
    if command -v "$cmd" >/dev/null 2>&1; then
        printf "PASS: %-12s %s\n" \
            "$cmd" \
            "$(command -v "$cmd")"
    else
        echo "ERROR: missing command: $cmd"
        exit 1
    fi
done

echo


echo "=== Toolchain ==="
cmake --version | head -1
ninja --version
c++ --version | head -1
python3 --version
openssl version
echo


echo "=== Required libraries ==="

for pkg in openssl mpfr gmp; do
    if pkg-config --exists "$pkg"; then
        echo \
            "PASS: $pkg =" \
            "$(pkg-config --modversion "$pkg")"
    else
        echo "ERROR: pkg-config cannot find $pkg"
        exit 1
    fi
done

echo


echo "=== Optional TestU01 ==="

if \
    test -f /usr/include/testu01/bbattery.h \
    && ldconfig -p 2>/dev/null \
        | grep -q 'libtestu01'
then
    echo "PASS: TestU01 available"
else
    echo \
        "INFO: TestU01 unavailable; " \
        "not required for HPC scaling runs"
fi

echo


echo "=== Slurm ==="

SLURM_OK=1

for cmd in sbatch srun sinfo; do
    if command -v "$cmd" >/dev/null 2>&1; then
        printf "PASS: %-8s %s\n" \
            "$cmd" \
            "$(command -v "$cmd")"
    else
        echo "INFO: $cmd unavailable"
        SLURM_OK=0
    fi
done

if [[ "$REQUIRE_SLURM" -eq 1 && "$SLURM_OK" -ne 1 ]]; then
    echo "ERROR: Slurm required but incomplete"
    exit 1
fi

if [[ "$SLURM_OK" -eq 1 ]]; then
    echo
    echo "Slurm version:"
    sinfo --version || true

    echo
    echo "Visible partitions:"
    sinfo -s || true
fi

echo


echo "=== Configure Release build ==="

cmake \
    -S . \
    -B build \
    -G Ninja \
    -DCMAKE_BUILD_TYPE=Release

echo


echo "=== Build ==="

cmake \
    --build build \
    --parallel

echo


echo "=== Unit/integration tests ==="

ctest \
    --test-dir build \
    --output-on-failure

echo


echo "=== Runner ==="

test -x build/bioentropy-runner

./build/bioentropy-runner \
    --help \
    >/dev/null

echo "PASS: bioentropy-runner executable"
echo


echo "=== Python harness syntax ==="

python3 -m py_compile \
    scripts/hpc/prepare_scaling_workloads.py \
    scripts/hpc/run_manifest_shard.py \
    scripts/hpc/run_scaling_local.py \
    analysis/scripts/analyze_hpc_scaling.py

echo "PASS: Python HPC harness"
echo


echo "================================"
echo "PASSED: HPC preflight"
echo "Report: $OUT"
