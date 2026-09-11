#!/usr/bin/env python3

import csv
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

RUNNER = ROOT / "build/bioentropy-runner"
PROBE = ROOT / "build/source-key-material-probe-aead3"

CONDITIONER = (
    ROOT
    / "build/ascon-xof128-condition-material"
)

CONFIG_ROOT = (
    ROOT
    / "configs/generated/dieharder-campaign/"
    "logistic-float64"
)

METRIC_ROOT = ROOT / "results/metrics"

OUTPUT = (
    ROOT
    / "results/aggregated/"
    "float64_collapse_aead3.tsv"
)

MATERIAL_BYTES = 104
MATERIAL_BITS = MATERIAL_BYTES * 8

COLLAPSE = {
    1: 5_919_555,
    5: 16_181_612,
    7: 21_156_926,
    8: 10_996_001,
    12: 9_423_224,
}


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
            "Command failed:\n"
            + " ".join(str(x) for x in command)
            + "\n\n"
            + result.stdout
        )

    return result.stdout


def sha256_file(path):
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)

    return digest.hexdigest()


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def extract_bits(
    data,
    start_bit,
    count_bits,
):
    if count_bits % 8 != 0:
        raise ValueError(
            "count_bits must be divisible by 8"
        )

    if (
        start_bit < 0
        or start_bit + count_bits
        > len(data) * 8
    ):
        raise ValueError(
            "requested range outside stream"
        )

    output = bytearray(
        count_bits // 8
    )

    for out_bit in range(count_bits):
        source_bit = start_bit + out_bit

        source_byte = source_bit // 8
        source_offset = source_bit % 8

        bit = (
            data[source_byte]
            >> (7 - source_offset)
        ) & 1

        output[out_bit // 8] |= (
            bit << (7 - (out_bit % 8))
        )

    return bytes(output)


def parse_probe(text):
    lines = [
        line
        for line in text.splitlines()
        if line.strip()
    ]

    if len(lines) != 2:
        raise RuntimeError(
            "Unexpected probe output:\n"
            + text
        )

    rows = list(
        csv.DictReader(
            lines,
            delimiter="\t",
        )
    )

    if len(rows) != 1:
        raise RuntimeError(
            "Expected exactly one probe row"
        )

    return rows[0]


def condition_local(
    material,
    tmp,
    name,
):
    input_path = (
        tmp / f"{name}-input.bin"
    )

    output_path = (
        tmp / f"{name}-ascon.bin"
    )

    input_path.write_bytes(material)

    run(
        [
            str(CONDITIONER),
            str(input_path),
            str(output_path),
            str(MATERIAL_BYTES),
        ]
    )

    conditioned = output_path.read_bytes()

    if len(conditioned) != MATERIAL_BYTES:
        raise RuntimeError(
            "local conditioned length mismatch"
        )

    return conditioned


def probe_material(
    material,
    tmp,
    rep,
    mode,
):
    path = tmp / f"{mode}.bin"

    path.write_bytes(material)

    return parse_probe(
        run(
            [
                str(PROBE),
                str(path),
                "logistic-float64",
                f"{rep:03d}",
                mode,
            ]
        )
    )


def main():
    rows = []

    for rep, collapse_bit in COLLAPSE.items():
        print(
            f"=== rep{rep:03d} "
            f"collapse={collapse_bit} ==="
        )

        config = (
            CONFIG_ROOT
            / f"rep{rep:03d}.yaml"
        )

        frozen_metric_path = (
            METRIC_ROOT
            / (
                "dieharder-logistic-float64"
                f"_rep{rep:04d}.json"
            )
        )

        frozen = json.loads(
            frozen_metric_path.read_text()
        )

        expected_sha = (
            frozen["reproducibility"]
            ["bitstream_sha256"]
        )

        with tempfile.TemporaryDirectory(
            prefix=(
                "float64-collapse-aead3-"
                f"rep{rep:03d}-"
            )
        ) as tmp_name:
            tmp = Path(tmp_name)

            raw_path = tmp / "raw.bin"

            run(
                [
                    str(RUNNER),
                    "--config",
                    str(config.resolve()),
                    "--dump-bitstream",
                    str(raw_path),
                ],
                cwd=tmp,
            )

            actual_sha = sha256_file(
                raw_path
            )

            if actual_sha != expected_sha:
                raise RuntimeError(
                    f"rep{rep:03d}: "
                    "RAW provenance mismatch"
                )

            raw = raw_path.read_bytes()

            pre_raw = extract_bits(
                raw,
                collapse_bit - MATERIAL_BITS,
                MATERIAL_BITS,
            )

            post_raw = extract_bits(
                raw,
                collapse_bit,
                MATERIAL_BITS,
            )

            if post_raw != bytes(
                MATERIAL_BYTES
            ):
                raise RuntimeError(
                    f"rep{rep:03d}: "
                    "post-collapse window "
                    "is not all-zero"
                )

            pre_ascon = condition_local(
                pre_raw,
                tmp,
                "pre",
            )

            post_ascon = condition_local(
                post_raw,
                tmp,
                "post",
            )

            variants = [
                (
                    "pre_collapse_raw",
                    "pre",
                    "raw",
                    pre_raw,
                    collapse_bit
                    - MATERIAL_BITS,
                ),
                (
                    "post_collapse_raw",
                    "post",
                    "raw",
                    post_raw,
                    collapse_bit,
                ),
                (
                    "pre_collapse_local_ascon_xof128",
                    "pre",
                    "local_ascon_xof128",
                    pre_ascon,
                    collapse_bit
                    - MATERIAL_BITS,
                ),
                (
                    "post_collapse_local_ascon_xof128",
                    "post",
                    "local_ascon_xof128",
                    post_ascon,
                    collapse_bit,
                ),
            ]

            for (
                mode,
                phase,
                conditioning,
                material,
                start_bit,
            ) in variants:
                probe = probe_material(
                    material,
                    tmp,
                    rep,
                    mode,
                )

                probe.update(
                    {
                        "phase":
                            phase,

                        "conditioning_scope":
                            conditioning,

                        "collapse_bit":
                            collapse_bit,

                        "window_start_bit":
                            start_bit,

                        "window_bits":
                            MATERIAL_BITS,

                        "input_raw_window_sha256":
                            (
                                sha256_bytes(
                                    pre_raw
                                )
                                if phase == "pre"
                                else sha256_bytes(
                                    post_raw
                                )
                            ),

                        "full_raw_sha256":
                            actual_sha,

                        "provenance_pass":
                            1,

                        "protocol":
                            "AEAD3-collapse-v1",
                    }
                )

                rows.append(probe)

                print(
                    f"  {mode:<37} "
                    f"zero={probe['zero_bytes']:<3} "
                    f"unique={probe['unique_bytes']:<3} "
                    f"p1={float(probe['p1']):.6f}"
                )

    if len(rows) != 20:
        raise RuntimeError(
            f"Expected 20 rows, got {len(rows)}"
        )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fields = list(
        rows[0].keys()
    )

    with OUTPUT.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
        )

        writer.writeheader()
        writer.writerows(rows)

    print()
    print("=== COMPLETE ===")
    print("Rows  :", len(rows))
    print("Output:", OUTPUT)


if __name__ == "__main__":
    main()
