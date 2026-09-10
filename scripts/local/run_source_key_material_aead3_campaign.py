#!/usr/bin/env python3

import argparse
import csv
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

RAW_ROOT = (
    ROOT
    / "configs/generated/dieharder-campaign"
)

ASCON_ROOT = (
    ROOT
    / "configs/generated/dieharder-campaign-ascon"
)

RUNNER = ROOT / "build/bioentropy-runner"

PROBE = (
    ROOT
    / "build/source-key-material-probe-aead3"
)

FROZEN_METRICS = ROOT / "results/metrics"

OUTPUT = (
    ROOT
    / "results/aggregated/"
    "source_key_material_aead3_campaign.tsv"
)

MATERIAL_BYTES = 104


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


def metric_sha(metric):
    return (
        metric["reproducibility"]
        ["bitstream_sha256"]
    )


def conditioning_input_sha(metric):
    conditioning = metric.get(
        "conditioning",
        {}
    )

    value = conditioning.get(
        "input_sha256"
    )

    if not value:
        raise RuntimeError(
            "Missing conditioning.input_sha256"
        )

    return value


def frozen_metric_path(
    source,
    replicate,
    mode,
):
    suffix = (
        ""
        if mode == "raw"
        else "_ascon-xof128"
    )

    return (
        FROZEN_METRICS
        / (
            f"dieharder-{source}"
            f"_rep{replicate:04d}"
            f"{suffix}.json"
        )
    )


def load_metric(path):
    if not path.is_file():
        raise FileNotFoundError(path)

    return json.loads(
        path.read_text()
    )


def generated_metric(run_dir):
    paths = list(
        (
            run_dir / "results/metrics"
        ).glob("*.json")
    )

    if len(paths) != 1:
        raise RuntimeError(
            "Expected exactly one generated "
            f"metric JSON, found {len(paths)}"
        )

    return load_metric(paths[0])


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
            "Expected one probe row"
        )

    return rows[0]


def discover_pairs(source_filter=None):
    pairs = []

    for raw_config in sorted(
        RAW_ROOT.glob("*/rep*.yaml")
    ):
        source = raw_config.parent.name

        if (
            source_filter
            and source != source_filter
        ):
            continue

        replicate = int(
            raw_config.stem.removeprefix(
                "rep"
            )
        )

        ascon_config = (
            ASCON_ROOT
            / source
            / raw_config.name
        )

        if not ascon_config.is_file():
            raise FileNotFoundError(
                ascon_config
            )

        pairs.append(
            (
                source,
                replicate,
                raw_config,
                ascon_config,
            )
        )

    return pairs


def load_existing():
    if not OUTPUT.is_file():
        return [], set()

    with OUTPUT.open(
        encoding="utf-8"
    ) as handle:
        rows = list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )

    completed = {
        (
            row["source"],
            int(row["replicate_id"]),
            row["mode"],
        )
        for row in rows
    }

    return rows, completed


def write_rows(rows):
    if not rows:
        return

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


def evaluate(
    source,
    replicate,
    mode,
    config,
    expected_raw_sha,
):
    frozen_path = frozen_metric_path(
        source,
        replicate,
        mode,
    )

    frozen = load_metric(
        frozen_path
    )

    expected_output_sha = metric_sha(
        frozen
    )

    if mode == "ascon_xof128":
        frozen_input_sha = (
            conditioning_input_sha(
                frozen
            )
        )

        if (
            frozen_input_sha
            != expected_raw_sha
        ):
            raise RuntimeError(
                f"{source} rep{replicate:03d}: "
                "frozen Ascon input SHA "
                "does not match RAW SHA"
            )

    with tempfile.TemporaryDirectory(
        prefix=(
            "bioentropy-aead3-"
            f"{source}-"
            f"rep{replicate:03d}-"
            f"{mode}-"
        )
    ) as tmp_name:
        tmp = Path(tmp_name)

        output_stream = (
            tmp / "evaluated.bin"
        )

        run(
            [
                str(RUNNER),
                "--config",
                str(config.resolve()),
                "--dump-bitstream",
                str(output_stream),
            ],
            cwd=tmp,
        )

        actual_output_sha = sha256_file(
            output_stream
        )

        generated = generated_metric(
            tmp
        )

        generated_output_sha = (
            metric_sha(generated)
        )

        if not (
            actual_output_sha
            == generated_output_sha
            == expected_output_sha
        ):
            raise RuntimeError(
                f"{source} rep{replicate:03d} "
                f"{mode}: output provenance mismatch"
            )

        if mode == "ascon_xof128":
            generated_input_sha = (
                conditioning_input_sha(
                    generated
                )
            )

            if (
                generated_input_sha
                != expected_raw_sha
            ):
                raise RuntimeError(
                    f"{source} rep{replicate:03d}: "
                    "generated Ascon input SHA "
                    "does not match RAW SHA"
                )

        with output_stream.open(
            "rb"
        ) as handle:
            material = handle.read(
                MATERIAL_BYTES
            )

        if len(material) != MATERIAL_BYTES:
            raise RuntimeError(
                "Evaluated stream shorter "
                "than 104 bytes"
            )

        material_path = (
            tmp / "material104.bin"
        )

        material_path.write_bytes(
            material
        )

        probe = parse_probe(
            run(
                [
                    str(PROBE),
                    str(material_path),
                    source,
                    f"{replicate:03d}",
                    mode,
                ]
            )
        )

        probe.update(
            {
                "full_stream_sha256":
                    actual_output_sha,

                "raw_input_sha256":
                    expected_raw_sha,

                "material_bytes":
                    MATERIAL_BYTES,

                "protocol":
                    "AEAD3-v1",

                "provenance_pass":
                    1,
            }
        )

        return probe


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--source"
    )

    parser.add_argument(
        "--limit-pairs",
        type=int,
    )

    args = parser.parse_args()

    pairs = discover_pairs(
        args.source
    )

    if args.limit_pairs is not None:
        pairs = pairs[
            : args.limit_pairs
        ]

    if not pairs:
        raise RuntimeError(
            "No RAW/Ascon config pairs found"
        )

    rows, completed = load_existing()

    total_pairs = len(pairs)

    for pair_index, (
        source,
        replicate,
        raw_config,
        ascon_config,
    ) in enumerate(
        pairs,
        start=1,
    ):
        print(
            f"[{pair_index}/{total_pairs}] "
            f"{source} rep{replicate:03d}"
        )

        raw_frozen = load_metric(
            frozen_metric_path(
                source,
                replicate,
                "raw",
            )
        )

        raw_sha = metric_sha(
            raw_frozen
        )

        for mode, config in (
            ("raw", raw_config),
            (
                "ascon_xof128",
                ascon_config,
            ),
        ):
            key = (
                source,
                replicate,
                mode,
            )

            if key in completed:
                print(
                    f"  {mode}: already complete"
                )
                continue

            row = evaluate(
                source,
                replicate,
                mode,
                config,
                raw_sha,
            )

            rows.append(row)
            completed.add(key)

            write_rows(rows)

            if not (
                int(row["ascon_roundtrip"])
                == 1
                and int(
                    row["chacha_roundtrip"]
                ) == 1
                and int(
                    row["aes_roundtrip"]
                ) == 1
            ):
                raise RuntimeError(
                    "AEAD round-trip failure"
                )

            print(
                f"  {mode}: PASS"
            )

    print()
    print("=== COMPLETE ===")
    print(
        "Result rows :",
        len(rows),
    )
    print(
        "Output      :",
        OUTPUT,
    )


if __name__ == "__main__":
    main()
