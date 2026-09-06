#!/usr/bin/env bash

set -euo pipefail

ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/../.."
    pwd
)"

cd "${ROOT}"

RAW_CONFIG="configs/campaigns/conditioning-smoke/raw.yaml"
ASCON_CONFIG="configs/campaigns/conditioning-smoke/ascon.yaml"

RAW_RESULT="results/metrics/conditioning-smoke-001_rep0000.json"
ASCON_RESULT="results/metrics/conditioning-smoke-001_rep0000_ascon-xof128.json"

./build/bioentropy-runner \
    --config "${RAW_CONFIG}"

./build/bioentropy-runner \
    --config "${ASCON_CONFIG}"

python3 - <<'PY'
import json
from pathlib import Path

raw_path = Path(
    "results/metrics/"
    "conditioning-smoke-001_rep0000.json"
)

ascon_path = Path(
    "results/metrics/"
    "conditioning-smoke-001_rep0000_ascon-xof128.json"
)

if not raw_path.exists():
    raise SystemExit(
        f"FAILED: missing {raw_path}"
    )

if not ascon_path.exists():
    raise SystemExit(
        f"FAILED: missing {ascon_path}"
    )

raw = json.loads(raw_path.read_text())
ascon = json.loads(ascon_path.read_text())

raw_sha = (
    raw["reproducibility"]
    ["bitstream_sha256"]
)

input_sha = (
    ascon["conditioning"]
    ["input_sha256"]
)

output_sha = (
    ascon["reproducibility"]
    ["bitstream_sha256"]
)

if raw["conditioning"]["mode"] != "raw":
    raise SystemExit(
        "FAILED: RAW result has wrong mode"
    )

if (
    ascon["conditioning"]["mode"]
    != "ascon_xof128"
):
    raise SystemExit(
        "FAILED: Ascon result has wrong mode"
    )

if raw_sha != input_sha:
    raise SystemExit(
        "FAILED: paired runs used "
        "different raw source streams"
    )

if raw_sha == output_sha:
    raise SystemExit(
        "FAILED: conditioning did not "
        "change the stream"
    )

if (
    raw["statistics"]["total_bits"]
    != ascon["statistics"]["total_bits"]
):
    raise SystemExit(
        "FAILED: output lengths differ"
    )

print()
print("Conditioning paired smoke test")
print("------------------------------")
print("Same source input : True")
print("Output changed    : True")
print(
    "Bits preserved    :",
    raw["statistics"]["total_bits"],
)

print()
print("RAW")
print(
    "  bias   =",
    raw["statistics"]["bias"],
)
print(
    "  H      =",
    raw["statistics"]["shannon_entropy"],
)
print(
    "  AC1    =",
    raw["statistics"]["autocorrelation_lag1"],
)
print(
    "  runs z =",
    raw["statistics"]["runs_z_score"],
)

print()
print("ASCON-XOF128")
print(
    "  bias   =",
    ascon["statistics"]["bias"],
)
print(
    "  H      =",
    ascon["statistics"]["shannon_entropy"],
)
print(
    "  AC1    =",
    ascon["statistics"]["autocorrelation_lag1"],
)
print(
    "  runs z =",
    ascon["statistics"]["runs_z_score"],
)

print()
print("PASSED: paired conditioning smoke test")
PY
