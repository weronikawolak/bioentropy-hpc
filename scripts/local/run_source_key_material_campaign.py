#!/usr/bin/env python3

import argparse
import csv
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

RAW_ROOT = (
    ROOT
    / "configs"
    / "generated"
    / "dieharder-campaign"
)

ASCON_ROOT = (
    ROOT
    / "configs"
    / "generated"
    / "dieharder-campaign-ascon"
)

RUNNER = (
    ROOT
    / "build"
    / "bioentropy-runner"
)

PROBE = (
    ROOT
    / "build"
    / "source-key-material-probe"
)

FROZEN_METRICS = (
    ROOT
    / "results"
    / "metrics"
)

OUTPUT = (
    ROOT
    / "results"
    / "aggregated"
    / "source_key_material_campaign.tsv"
)

REP_RE = re.compile(
    r"^rep(\d{3})\.yaml$"
)


def sha256_file(path):
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while chunk := handle.read(
            1024 * 1024
        ):
            digest.update(chunk)

    return digest.hexdigest()


def run_command(command, cwd=None):
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


def frozen_metric_path(
    source,
    rep,
    mode,
):
    suffix = (
        "_ascon-xof128"
        if mode == "ascon_xof128"
        else ""
    )

    return (
        FROZEN_METRICS
        / (
            f"dieharder-{source}"
            f"_rep{rep:04d}"
            f"{suffix}.json"
        )
    )


def read_frozen_metric(
    source,
    rep,
    mode,
):
    path = frozen_metric_path(
        source,
        rep,
        mode,
    )

    if not path.is_file():
        raise FileNotFoundError(
            path
        )

    return json.loads(
        path.read_text()
    )


def find_generated_metric(
    temp,
):
    candidates = list(
        (
            temp
            / "results"
            / "metrics"
        ).glob("*.json")
    )

    if len(candidates) != 1:
        raise RuntimeError(
            "Expected exactly one generated "
            f"metric JSON, got {len(candidates)}"
        )

    return json.loads(
        candidates[0].read_text()
    )


def parse_probe_output(text):
    lines = [
        line
        for line in text.splitlines()
        if line.strip()
    ]

    if len(lines) != 2:
        raise RuntimeError(
            "Unexpected key-material probe output:\n"
            + text
        )

    reader = csv.DictReader(
        lines,
        delimiter="\t",
    )

    rows = list(reader)

    if len(rows) != 1:
        raise RuntimeError(
            "Expected one probe result row"
        )

    return rows[0]


def run_mode(
    source,
    rep,
    config,
    mode,
    expected_raw_sha,
):
    frozen = read_frozen_metric(
        source,
        rep,
        mode,
    )

    expected_output_sha = (
        frozen["reproducibility"][
            "bitstream_sha256"
        ]
    )

    if mode == "ascon_xof128":
        frozen_input_sha = (
            frozen["conditioning"][
                "input_sha256"
            ]
        )

        if (
            frozen_input_sha
            != expected_raw_sha
        ):
            raise RuntimeError(
                f"{source} rep{rep:03d}: "
                "frozen Ascon input SHA "
                "does not match frozen RAW SHA"
            )

    with tempfile.TemporaryDirectory(
        prefix=(
            f"key-material-"
            f"{source}-"
            f"rep{rep:03d}-"
            f"{mode}-"
        )
    ) as temp_name:
        temp = Path(temp_name)

        bitstream = (
            temp / "stream.bin"
        )

        run_command(
            [
                str(RUNNER),
                "--config",
                str(config.resolve()),
                "--dump-bitstream",
                str(bitstream),
            ],
            cwd=temp,
        )

        if not bitstream.is_file():
            raise RuntimeError(
                "Runner did not create bitstream"
            )

        generated_metric = (
            find_generated_metric(temp)
        )

        actual_output_sha = (
            sha256_file(bitstream)
        )

        metric_output_sha = (
            generated_metric[
                "reproducibility"
            ]["bitstream_sha256"]
        )

        if (
            actual_output_sha
            != metric_output_sha
        ):
            raise RuntimeError(
                f"{source} rep{rep:03d} "
                f"{mode}: generated metric "
                "SHA mismatch"
            )

        if (
            actual_output_sha
            != expected_output_sha
        ):
            raise RuntimeError(
                f"{source} rep{rep:03d} "
                f"{mode}: frozen output "
                "SHA mismatch"
            )

        if mode == "raw":
            if (
                actual_output_sha
                != expected_raw_sha
            ):
                raise RuntimeError(
                    f"{source} rep{rep:03d}: "
                    "RAW provenance mismatch"
                )

        else:
            generated_input_sha = (
                generated_metric[
                    "conditioning"
                ]["input_sha256"]
            )

            if (
                generated_input_sha
                != expected_raw_sha
            ):
                raise RuntimeError(
                    f"{source} rep{rep:03d}: "
                    "generated Ascon input "
                    "SHA mismatch"
                )

        with bitstream.open("rb") as handle:
            material_bytes = handle.read(76)

        if len(material_bytes) != 76:
            raise RuntimeError(
                "Could not read 76 material bytes"
            )

        material = (
            temp / "material.bin"
        )

        material.write_bytes(
            material_bytes
        )

        probe_output = run_command(
            [
                str(PROBE),
                str(material),
                source,
                f"{rep:03d}",
                mode,
            ]
        )

        row = parse_probe_output(
            probe_output
        )

        row.update(
            {
                "full_stream_sha256":
                    actual_output_sha,
                "raw_input_sha256":
                    expected_raw_sha,
                "provenance_pass":
                    "1",
            }
        )

        return row


def write_output(rows):
    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fields = [
        "source",
        "replicate_id",
        "mode",
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
        "full_stream_sha256",
        "raw_input_sha256",
        "provenance_pass",
    ]

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


def discover_pairs(
    source_filter=None,
):
    pairs = []

    for raw in sorted(
        RAW_ROOT.glob("*/rep*.yaml")
    ):
        source = raw.parent.name

        if (
            source_filter is not None
            and source != source_filter
        ):
            continue

        match = REP_RE.fullmatch(
            raw.name
        )

        if not match:
            continue

        rep = int(
            match.group(1)
        )

        rel = raw.relative_to(
            RAW_ROOT
        )

        ascon = (
            ASCON_ROOT / rel
        )

        if not ascon.is_file():
            raise FileNotFoundError(
                ascon
            )

        pairs.append(
            (
                source,
                rep,
                raw,
                ascon,
            )
        )

    return pairs


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit-pairs",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--source",
        default=None,
    )

    args = parser.parse_args()

    if not RUNNER.is_file():
        raise FileNotFoundError(
            RUNNER
        )

    if not PROBE.is_file():
        raise FileNotFoundError(
            PROBE
        )

    pairs = discover_pairs(
        args.source
    )

    if args.limit_pairs is not None:
        pairs = pairs[
            :args.limit_pairs
        ]

    if not pairs:
        raise RuntimeError(
            "No config pairs found"
        )

    print(
        "Config pairs:",
        len(pairs),
    )

    rows = []

    for index, (
        source,
        rep,
        raw_config,
        ascon_config,
    ) in enumerate(
        pairs,
        start=1,
    ):
        print(
            f"[{index:03d}/{len(pairs):03d}] "
            f"{source} rep{rep:03d}",
            flush=True,
        )

        raw_frozen = (
            read_frozen_metric(
                source,
                rep,
                "raw",
            )
        )

        expected_raw_sha = (
            raw_frozen[
                "reproducibility"
            ]["bitstream_sha256"]
        )

        raw_row = run_mode(
            source,
            rep,
            raw_config,
            "raw",
            expected_raw_sha,
        )

        rows.append(
            raw_row
        )

        ascon_row = run_mode(
            source,
            rep,
            ascon_config,
            "ascon_xof128",
            expected_raw_sha,
        )

        rows.append(
            ascon_row
        )

        write_output(rows)

        print(
            "  RAW   material "
            + raw_row[
                "material_sha256"
            ][:12]
            + "..."
        )

        print(
            "  ASCON material "
            + ascon_row[
                "material_sha256"
            ][:12]
            + "..."
        )

    print()
    print("=== COMPLETE ===")
    print(
        "Pairs       :",
        len(pairs),
    )
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
