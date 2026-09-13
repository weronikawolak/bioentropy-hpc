#!/usr/bin/env python3

from pathlib import Path
import argparse
import json

import pandas as pd


VALID_MODES = {
    "ensemble-strong",
    "ensemble-weak",
}


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        required=True,
    )

    parser.add_argument(
        "--output",
        required=True,
    )

    args = parser.parse_args()

    root = Path(
        args.input
    )

    jobs = []

    for path in sorted(
        root.rglob(
            "job.json"
        )
    ):
        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        data["path"] = str(path)

        jobs.append(data)

    if not jobs:
        raise RuntimeError(
            f"No job.json under {root}"
        )

    raw = pd.DataFrame(
        jobs
    )

    required = {
        "profile",
        "mode",
        "world_size",
        "repetition",
        "wall_seconds",
        "total_output_bits",
    }

    missing = (
        required
        - set(raw.columns)
    )

    if missing:
        raise RuntimeError(
            f"Missing columns: "
            f"{sorted(missing)}"
        )

    invalid_modes = (
        set(raw["mode"])
        - VALID_MODES
    )

    if invalid_modes:
        raise RuntimeError(
            f"Invalid scaling modes: "
            f"{sorted(invalid_modes)}"
        )

    if (
        raw["wall_seconds"]
        <= 0
    ).any():
        raise RuntimeError(
            "Non-positive wall time"
        )

    duplicates = raw.duplicated(
        subset=[
            "profile",
            "mode",
            "world_size",
            "repetition",
        ],
        keep=False,
    )

    if duplicates.any():
        raise RuntimeError(
            "Duplicate scaling point/"
            "repetition detected"
        )

    grouped = (
        raw.groupby(
            [
                "profile",
                "mode",
                "world_size",
            ],
            as_index=False,
        )
        .agg(
            repetitions=(
                "wall_seconds",
                "size",
            ),

            wall_median_seconds=(
                "wall_seconds",
                "median",
            ),

            wall_min_seconds=(
                "wall_seconds",
                "min",
            ),

            wall_max_seconds=(
                "wall_seconds",
                "max",
            ),

            total_output_bits=(
                "total_output_bits",
                "median",
            ),
        )
    )

    grouped[
        "aggregate_throughput_mib_s"
    ] = (
        grouped[
            "total_output_bits"
        ]
        / 8
        / (1024 ** 2)
        / grouped[
            "wall_median_seconds"
        ]
    )

    grouped[
        "ensemble_speedup"
    ] = float("nan")

    grouped[
        "ensemble_parallel_efficiency"
    ] = float("nan")

    grouped[
        "weak_scaling_efficiency"
    ] = float("nan")

    for (
        profile,
        mode,
    ), indices in grouped.groupby(
        [
            "profile",
            "mode",
        ]
    ).groups.items():

        subset = grouped.loc[
            indices
        ]

        baseline = subset[
            subset[
                "world_size"
            ] == 1
        ]

        if len(baseline) != 1:
            raise RuntimeError(
                f"{profile}/{mode}: "
                "exactly one p=1 baseline "
                "is required"
            )

        t1 = float(
            baseline[
                "wall_median_seconds"
            ].iloc[0]
        )

        for index in indices:
            p = int(
                grouped.loc[
                    index,
                    "world_size",
                ]
            )

            tp = float(
                grouped.loc[
                    index,
                    "wall_median_seconds",
                ]
            )

            if (
                mode
                == "ensemble-strong"
            ):
                speedup = t1 / tp

                grouped.loc[
                    index,
                    "ensemble_speedup",
                ] = speedup

                grouped.loc[
                    index,
                    "ensemble_parallel_efficiency",
                ] = (
                    speedup / p
                )

            else:
                grouped.loc[
                    index,
                    "weak_scaling_efficiency",
                ] = (
                    t1 / tp
                )

    grouped = grouped.sort_values(
        [
            "profile",
            "mode",
            "world_size",
        ]
    )

    output = Path(
        args.output
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    grouped.to_csv(
        output,
        sep="\t",
        index=False,
    )

    print(
        grouped.to_string(
            index=False,
            float_format=lambda x:
                f"{x:.6f}",
        )
    )

    print()
    print("Saved:", output)


if __name__ == "__main__":
    main()
