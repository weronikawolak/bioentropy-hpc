#!/usr/bin/env python3

import csv
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

RUNNER = ROOT / "build" / "bioentropy-runner"
PROBE = ROOT / "build" / "source-key-material-probe"

CONFIG_ROOT = (
    ROOT
    / "configs"
    / "generated"
    / "dieharder-campaign"
    / "logistic-float64"
)

METRIC_ROOT = (
    ROOT
    / "results"
    / "metrics"
)

OUTPUT = (
    ROOT
    / "results"
    / "aggregated"
    / "float64_collapse_key_material.tsv"
)

MATERIAL_BITS = 76 * 8

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
        while chunk := f.read(
            1024 * 1024
        ):
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
            "Command failed:\n"
            + " ".join(
                str(x)
                for x in command
            )
            + "\n\n"
            + result.stdout
        )

    return result.stdout


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
            "bit range outside stream"
        )

    output = bytearray(
        count_bits // 8
    )

    for out_bit in range(
        count_bits
    ):
        source_bit = (
            start_bit + out_bit
        )

        source_byte = (
            source_bit // 8
        )

        source_offset = (
            source_bit % 8
        )

        bit = (
            data[source_byte]
            >> (7 - source_offset)
        ) & 1

        output_byte = (
            out_bit // 8
        )

        output_offset = (
            out_bit % 8
        )

        output[output_byte] |= (
            bit << (7 - output_offset)
        )

    return bytes(output)


def parse_probe(text):
    lines = [
        x
        for x in text.splitlines()
        if x.strip()
    ]

    if len(lines) != 2:
        raise RuntimeError(
            "Unexpected probe output:\n"
            + text
        )

    return next(
        csv.DictReader(
            lines,
            delimiter="\t",
        )
    )


def main():
    rows = []

    for rep, collapse_bit in (
        COLLAPSE.items()
    ):
        print(
            f"=== rep{rep:03d} "
            f"collapse={collapse_bit} ==="
        )

        config = (
            CONFIG_ROOT
            / f"rep{rep:03d}.yaml"
        )

        metric_path = (
            METRIC_ROOT
            / (
                "dieharder-logistic-float64"
                f"_rep{rep:04d}.json"
            )
        )

        metric = json.loads(
            metric_path.read_text()
        )

        expected_sha = (
            metric["reproducibility"]
            ["bitstream_sha256"]
        )

        with tempfile.TemporaryDirectory(
            prefix=(
                "float64-collapse-"
                f"rep{rep:03d}-"
            )
        ) as tmp:
            tmp = Path(tmp)

            raw_path = (
                tmp / "raw.bin"
            )

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

            actual_sha = (
                sha256_file(
                    raw_path
                )
            )

            if actual_sha != expected_sha:
                raise RuntimeError(
                    f"rep{rep:03d}: "
                    "RAW provenance mismatch"
                )

            raw = raw_path.read_bytes()

            windows = {
                "pre_collapse_raw":
                    extract_bits(
                        raw,
                        collapse_bit
                        - MATERIAL_BITS,
                        MATERIAL_BITS,
                    ),

                "post_collapse_raw":
                    extract_bits(
                        raw,
                        collapse_bit,
                        MATERIAL_BITS,
                    ),
            }

            for mode, material in (
                windows.items()
            ):
                material_path = (
                    tmp
                    / f"{mode}.bin"
                )

                material_path.write_bytes(
                    material
                )

                probe = parse_probe(
                    run(
                        [
                            str(PROBE),
                            str(material_path),
                            "logistic-float64",
                            f"{rep:03d}",
                            mode,
                        ]
                    )
                )

                probe.update(
                    {
                        "collapse_bit":
                            collapse_bit,
                        "window_start_bit":
                            (
                                collapse_bit
                                - MATERIAL_BITS
                                if mode
                                == "pre_collapse_raw"
                                else collapse_bit
                            ),
                        "window_bits":
                            MATERIAL_BITS,
                        "full_raw_sha256":
                            actual_sha,
                        "provenance_pass":
                            1,
                    }
                )

                rows.append(
                    probe
                )

                print(
                    f"{mode:<20} "
                    f"zero={probe['zero_bytes']} "
                    f"unique="
                    f"{probe['unique_bytes']} "
                    f"p1={float(probe['p1']):.6f}"
                )

    fields = [
        "source",
        "replicate_id",
        "mode",
        "collapse_bit",
        "window_start_bit",
        "window_bits",
        "material_sha256",
        "zero_bytes",
        "unique_bytes",
        "p1",
        "ascon_key_sha256",
        "ascon_nonce_sha256",
        "ascon_ciphertext_sha256",
        "ascon_roundtrip",
        "chacha_key_sha256",
        "chacha_nonce_sha256",
        "chacha_ciphertext_sha256",
        "chacha_roundtrip",
        "full_raw_sha256",
        "provenance_pass",
    ]

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
            fieldnames=fields,
            delimiter="\t",
        )

        writer.writeheader()
        writer.writerows(rows)

    print()
    print("Saved:", OUTPUT)


if __name__ == "__main__":
    main()
