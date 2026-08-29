#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

MANIFEST = (
    ROOT
    / "configs/generated/conditioning"
    / "manifest.tsv"
)

RESULTS = ROOT / "results/metrics"


def result_path(
    experiment_id,
    replicate_id,
    mode,
):
    suffix = (
        "_ascon-xof128"
        if mode == "ascon_xof128"
        else ""
    )

    return (
        RESULTS
        / (
            f"{experiment_id}_"
            f"rep{replicate_id:04d}"
            f"{suffix}.json"
        )
    )


def main():
    if not MANIFEST.exists():
        raise RuntimeError(
            f"Missing manifest: {MANIFEST}"
        )

    with MANIFEST.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        rows = list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )

    pairs = defaultdict(set)

    for row in rows:
        identity = (
            row["experiment_id"].strip(),
            int(row["replicate_id"]),
        )

        pairs[identity].add(
            row[
                "conditioning_mode"
            ].strip()
        )

    incomplete_configs = [
        identity
        for identity, modes
        in pairs.items()
        if modes != {
            "raw",
            "ascon_xof128",
        }
    ]

    if incomplete_configs:
        raise RuntimeError(
            "Manifest contains incomplete "
            "RAW/Ascon pairs"
        )

    complete = 0
    missing = []
    invalid = []

    for identity in sorted(pairs):
        experiment_id, replicate_id = (
            identity
        )

        raw_path = result_path(
            experiment_id,
            replicate_id,
            "raw",
        )

        ascon_path = result_path(
            experiment_id,
            replicate_id,
            "ascon_xof128",
        )

        if (
            not raw_path.exists()
            or not ascon_path.exists()
        ):
            missing.append(identity)
            continue

        try:
            raw = json.loads(
                raw_path.read_text()
            )

            ascon = json.loads(
                ascon_path.read_text()
            )

            if (
                raw["conditioning"]["mode"]
                != "raw"
            ):
                raise ValueError(
                    "wrong RAW mode"
                )

            if (
                ascon["conditioning"]["mode"]
                != "ascon_xof128"
            ):
                raise ValueError(
                    "wrong Ascon mode"
                )

            raw_sha = (
                raw["reproducibility"]
                ["bitstream_sha256"]
            )

            ascon_input_sha = (
                ascon["conditioning"]
                ["input_sha256"]
            )

            ascon_output_sha = (
                ascon["reproducibility"]
                ["bitstream_sha256"]
            )

            if (
                raw_sha
                != ascon_input_sha
            ):
                raise ValueError(
                    "paired source inputs differ"
                )

            if (
                raw_sha
                == ascon_output_sha
            ):
                raise ValueError(
                    "conditioning output equals "
                    "RAW input"
                )

            if (
                raw["statistics"]
                ["total_bits"]
                != ascon["statistics"]
                ["total_bits"]
            ):
                raise ValueError(
                    "bit lengths differ"
                )

            complete += 1

        except Exception as exc:
            invalid.append(
                (
                    experiment_id,
                    replicate_id,
                    str(exc),
                )
            )

    expected = len(pairs)

    print(
        "Conditioning campaign status"
    )
    print(
        "----------------------------"
    )

    print(
        f"Expected pairs : {expected}"
    )

    print(
        f"Complete       : {complete}"
    )

    print(
        f"Missing        : {len(missing)}"
    )

    print(
        f"Invalid        : {len(invalid)}"
    )

    progress = (
        100.0 * complete / expected
        if expected
        else 0.0
    )

    print(
        f"Progress       : {progress:.2f}%"
    )

    if missing:
        print()
        print("First missing pairs:")

        for experiment_id, rep in (
            missing[:10]
        ):
            print(
                f"  {experiment_id} "
                f"rep={rep}"
            )

    if invalid:
        print()
        print("Invalid pairs:")

        for item in invalid[:10]:
            print(
                f"  {item[0]} "
                f"rep={item[1]}: "
                f"{item[2]}"
            )

    if (
        complete == expected
        and not invalid
    ):
        print()
        print("PASSED: campaign complete")


if __name__ == "__main__":
    main()
