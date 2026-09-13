#!/usr/bin/env python3

from pathlib import Path
import argparse
import json

import pandas as pd


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
        root.rglob("job.json")
    ):
        data = json.loads(
            path.read_text()
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
            f"Missing columns: {missing}"
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
        "throughput_mib_s"
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
        "speedup"
    ] = float("nan")

    grouped[
        "parallel_efficiency"
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
                "exactly one p=1 aggregate "
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

            if mode == "strong":
                speedup = t1 / tp

                efficiency = (
                    speedup / p
                )

                grouped.loc[
                    index,
                    "speedup",
                ] = speedup

                grouped.loc[
                    index,
                    "parallel_efficiency",
                ] = efficiency

            elif mode == "weak":
                grouped.loc[
                    index,
                    "parallel_efficiency",
                ] = (
                    t1 / tp
                )

    output = Path(
        args.output
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    grouped = grouped.sort_values(
        [
            "profile",
            "mode",
            "world_size",
        ]
    )

    grouped.to_csv(
        output,
        sep="\t",
        index=False,
    )

    print(
        grouped.to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    print()
    print("Saved:", output)


if __name__ == "__main__":
    main()
