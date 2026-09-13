#!/usr/bin/env python3

import csv
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

RUNNER = ROOT / "build" / "bioentropy-runner"

CONDITIONER = (
    ROOT
    / "build"
    / "ascon-xof128-condition-material"
)

PROBE = (
    ROOT
    / "build"
    / "source-key-material-probe"
)

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
    / "float64_collapse_conditioned_material.tsv"
)

MATERIAL_BITS = 76 * 8

COLLAPSE = {
    1: 5_919_555,
    5: 16_181_612,
    7: 21_156_926,
    8: 10_996_001,
    12: 9_423_224,
}


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)

    return digest.hexdigest()


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


def extract_bits(
    data,
    start_bit,
    count_bits,
):
    if count_bits % 8 != 0:
        raise ValueError(
            "count_bits must be byte aligned"
        )

    if (
        start_bit < 0
        or start_bit + count_bits
        > len(data) * 8
    ):
        raise ValueError(
            "requested range outside stream"
        )

    output = bytearray(count_bits // 8)

    for out_bit in range(count_bits):
        source_bit = start_bit + out_bit
        source_byte = source_bit // 8
        source_offset = source_bit % 8

        bit = (
            data[source_byte]
            >> (7 - source_offset)
        ) & 1

        output[out_bit // 8] |= (
            bit
            << (7 - (out_bit % 8))
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
                "float64-collapse-conditioned-"
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

            post_raw = extract_bits(
                raw,
                collapse_bit,
                MATERIAL_BITS,
            )

            if post_raw != bytes(76):
                raise RuntimeError(
                    f"rep{rep:03d}: "
                    "post-collapse material "
                    "is not exactly all-zero"
                )

            input_path = (
                tmp / "post-raw.bin"
            )

            conditioned_path = (
                tmp / "post-conditioned.bin"
            )

            input_path.write_bytes(
                post_raw
            )

            run(
                [
                    str(CONDITIONER),
                    str(input_path),
                    str(conditioned_path),
                    "76",
                ]
            )

            conditioned = (
                conditioned_path.read_bytes()
            )

            if len(conditioned) != 76:
                raise RuntimeError(
                    "Conditioned output is "
                    "not 76 bytes"
                )

            probe = parse_probe(
                run(
                    [
                        str(PROBE),
                        str(conditioned_path),
                        "logistic-float64",
                        f"{rep:03d}",
                        "post_collapse_local_ascon_xof128",
                    ]
                )
            )

            row = {
                "replicate_id":
                    f"{rep:03d}",

                "collapse_bit":
                    collapse_bit,

                "input_material_sha256":
                    sha256_bytes(post_raw),

                "input_zero_bytes":
                    post_raw.count(0),

                "conditioned_material_sha256":
                    probe["material_sha256"],

                "conditioned_zero_bytes":
                    probe["zero_bytes"],

                "conditioned_unique_bytes":
                    probe["unique_bytes"],

                "conditioned_p1":
                    probe["p1"],

                "ascon_key_sha256":
                    probe["ascon_key_sha256"],

                "ascon_nonce_sha256":
                    probe["ascon_nonce_sha256"],

                "ascon_ciphertext_sha256":
                    probe[
                        "ascon_ciphertext_sha256"
                    ],

                "ascon_roundtrip":
                    probe["ascon_roundtrip"],

                "chacha_key_sha256":
                    probe["chacha_key_sha256"],

                "chacha_nonce_sha256":
                    probe["chacha_nonce_sha256"],

                "chacha_ciphertext_sha256":
                    probe[
                        "chacha_ciphertext_sha256"
                    ],

                "chacha_roundtrip":
                    probe["chacha_roundtrip"],

                "full_raw_sha256":
                    actual_sha,

                "provenance_pass":
                    1,
            }

            rows.append(row)

            print(
                "  RAW zero="
                f"{row['input_zero_bytes']}/76 "
                "conditioned unique="
                f"{row['conditioned_unique_bytes']} "
                "P1="
                f"{float(row['conditioned_p1']):.6f}"
            )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(
                rows[0].keys()
            ),
            delimiter="\t",
        )

        writer.writeheader()
        writer.writerows(rows)

    print()
    print("Saved:", OUTPUT)


if __name__ == "__main__":
    main()
