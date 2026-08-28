#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

MANIFEST = (
    ROOT /
    "configs/generated/screening/"
    "manifest.tsv"
)

RESULT_ROOT = (
    ROOT /
    "results/metrics"
)


def result_name(
    experiment_id: str,
    replicate_id: int,
) -> str:
    return (
        f"{experiment_id}_"
        f"rep{replicate_id:04d}.json"
    )


def main():
    if not MANIFEST.exists():
        raise RuntimeError(
            f"Manifest not found: {MANIFEST}"
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

    missing = []
    invalid = []
    completed = []

    for row in rows:
        experiment_id = (
            row["experiment_id"]
        )

        replicate_id = int(
            row["replicate_id"]
        )

        path = (
            RESULT_ROOT
            / result_name(
                experiment_id,
                replicate_id,
            )
        )

        if not path.exists():
            missing.append(
                (
                    experiment_id,
                    replicate_id,
                )
            )
            continue

        try:
            with path.open(
                encoding="utf-8",
            ) as handle:
                data = json.load(handle)

            assert (
                data["experiment"]["id"]
                == experiment_id
            )

            assert (
                data["experiment"]
                ["replicate_id"]
                == replicate_id
            )

            assert (
                data["statistics"]
                ["total_bits"]
                == int(row["output_bits"])
            )

            assert (
                len(
                    data["reproducibility"]
                    ["bitstream_sha256"]
                )
                == 64
            )

            completed.append(path)

        except Exception as exc:
            invalid.append(
                (
                    path,
                    str(exc),
                )
            )

    total = len(rows)

    print(
        "BioEntropy screening status"
    )

    print(
        "---------------------------"
    )

    print(
        f"Expected : {total}"
    )

    print(
        f"Complete : {len(completed)}"
    )

    print(
        f"Missing  : {len(missing)}"
    )

    print(
        f"Invalid  : {len(invalid)}"
    )

    percentage = (
        100.0
        * len(completed)
        / total
        if total
        else 0.0
    )

    print(
        f"Progress : {percentage:.2f}%"
    )

    if invalid:
        print(
            "\nInvalid results:"
        )

        for path, reason in invalid[:20]:
            print(
                f"  {path.name}: "
                f"{reason}"
            )

    if missing:
        print(
            "\nFirst missing experiments:"
        )

        for experiment_id, replicate_id in (
            missing[:10]
        ):
            print(
                f"  {experiment_id} "
                f"rep={replicate_id}"
            )

    if (
        not missing
        and not invalid
    ):
        print()
        print(
            "Screening campaign PASSED"
        )


if __name__ == "__main__":
    main()
