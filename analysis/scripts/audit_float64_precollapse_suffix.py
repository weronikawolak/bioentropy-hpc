#!/usr/bin/env python3

import csv
import hashlib
import json
import subprocess
import tempfile
from itertools import combinations
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]

RUNNER = ROOT / "build/bioentropy-runner"

CONFIG_ROOT = (
    ROOT
    / "configs/generated/dieharder-campaign"
    / "logistic-float64"
)

METRIC_ROOT = ROOT / "results/metrics"

OUTPUT = (
    ROOT
    / "results/aggregated"
    / "float64_precollapse_suffix_audit.tsv"
)

COLLAPSE = {
    1: 5_919_555,
    5: 16_181_612,
    7: 21_156_926,
    8: 10_996_001,
    12: 9_423_224,
}


def sha256_file(path):
    h = hashlib.sha256()

    with path.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)

    return h.hexdigest()


def run(command, cwd=None):
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stdout
        )

    return result.stdout


def extract_bits(
    data,
    start_bit,
    count_bits,
):
    if start_bit < 0:
        raise ValueError("negative start")

    first_byte = start_bit // 8
    bit_offset = start_bit % 8

    end_bit = start_bit + count_bits
    end_byte = (end_bit + 7) // 8

    byte_view = np.frombuffer(
        data[first_byte:end_byte],
        dtype=np.uint8,
    )

    bits = np.unpackbits(
        byte_view,
        bitorder="big",
    )

    return bits[
        bit_offset:
        bit_offset + count_bits
    ]


def common_suffix_pair(
    data_a,
    collapse_a,
    data_b,
    collapse_b,
):
    count = min(
        collapse_a,
        collapse_b,
    )

    a = extract_bits(
        data_a,
        collapse_a - count,
        count,
    )

    b = extract_bits(
        data_b,
        collapse_b - count,
        count,
    )

    equal_reversed = (
        a == b
    )[::-1]

    mismatch = np.flatnonzero(
        ~equal_reversed
    )

    if mismatch.size == 0:
        return count

    return int(mismatch[0])


def common_suffix_group(
    streams,
    reps,
):
    count = min(
        COLLAPSE[rep]
        for rep in reps
    )

    arrays = []

    for rep in reps:
        arrays.append(
            extract_bits(
                streams[rep],
                COLLAPSE[rep] - count,
                count,
            )
        )

    equal = np.ones(
        count,
        dtype=bool,
    )

    reference = arrays[0]

    for current in arrays[1:]:
        equal &= (
            reference == current
        )

    mismatch = np.flatnonzero(
        ~equal[::-1]
    )

    if mismatch.size == 0:
        return count

    return int(mismatch[0])


def main():
    streams = {}
    full_shas = {}

    with tempfile.TemporaryDirectory(
        prefix="float64-suffix-audit-"
    ) as tmp_name:
        tmp = Path(tmp_name)

        for rep in COLLAPSE:
            print(
                f"Regenerating rep{rep:03d}..."
            )

            work = (
                tmp / f"rep{rep:03d}"
            )
            work.mkdir()

            output = work / "raw.bin"

            config = (
                CONFIG_ROOT
                / f"rep{rep:03d}.yaml"
            )

            frozen_path = (
                METRIC_ROOT
                / (
                    "dieharder-logistic-float64"
                    f"_rep{rep:04d}.json"
                )
            )

            frozen = json.loads(
                frozen_path.read_text()
            )

            expected = (
                frozen["reproducibility"]
                ["bitstream_sha256"]
            )

            run(
                [
                    str(RUNNER),
                    "--config",
                    str(config.resolve()),
                    "--dump-bitstream",
                    str(output),
                ],
                cwd=work,
            )

            actual = sha256_file(output)

            if actual != expected:
                raise RuntimeError(
                    f"rep{rep:03d}: "
                    "provenance mismatch"
                )

            streams[rep] = (
                output.read_bytes()
            )

            full_shas[rep] = actual

    if len(set(full_shas.values())) != 5:
        raise RuntimeError(
            "Full streams are not 5/5 unique"
        )

    rows = []

    for a, b in combinations(
        COLLAPSE.keys(),
        2,
    ):
        common = common_suffix_pair(
            streams[a],
            COLLAPSE[a],
            streams[b],
            COLLAPSE[b],
        )

        rows.append(
            {
                "rep_a": f"{a:03d}",
                "rep_b": f"{b:03d}",
                "collapse_a": COLLAPSE[a],
                "collapse_b": COLLAPSE[b],
                "common_suffix_bits": common,
                "common_suffix_bytes_floor":
                    common // 8,
                "at_least_832_bits":
                    int(common >= 832),
            }
        )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(
                rows[0].keys()
            ),
            delimiter="\t",
        )

        writer.writeheader()
        writer.writerows(rows)

    triple = common_suffix_group(
        streams,
        [7, 8, 12],
    )

    print()
    print("=== PAIRWISE ALIGNED SUFFIX ===")

    for row in rows:
        print(
            f"rep{row['rep_a']} "
            f"vs rep{row['rep_b']}: "
            f"{row['common_suffix_bits']} bits "
            f"({row['common_suffix_bytes_floor']} "
            "full bytes)"
        )

    print()
    print(
        "rep007 + rep008 + rep012 common suffix:",
        triple,
        "bits",
        f"({triple // 8} full bytes)",
    )

    print()
    print(
        "PASSED: full streams unique 5/5"
    )
    print("Saved:", OUTPUT)


if __name__ == "__main__":
    main()
