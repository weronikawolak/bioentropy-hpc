#!/usr/bin/env python3

from pathlib import Path

import pandas as pd


INPUT = Path(
    "results/aggregated/"
    "fetteha_p_performance.tsv"
)

OUTPUT = Path(
    "results/aggregated/"
    "fetteha_p_performance_summary.tsv"
)


def main() -> None:
    frame = pd.read_csv(
        INPUT,
        sep="\t",
    )

    frame[
        "encrypt_relative_to_p1"
    ] = (
        frame["encrypt_median_us"]
        / frame.loc[
            frame["effective_passes"] == 1,
            "encrypt_median_us",
        ].iloc[0]
    )

    frame[
        "decrypt_relative_to_p1"
    ] = (
        frame["decrypt_median_us"]
        / frame.loc[
            frame["effective_passes"] == 1,
            "decrypt_median_us",
        ].iloc[0]
    )

    frame = frame.sort_values(
        "effective_passes"
    )

    frame.to_csv(
        OUTPUT,
        sep="\t",
        index=False,
    )

    print()
    print(
        "Fetteha 2023 performance by effective P"
    )
    print("=" * 120)

    print(
        frame[
            [
                "raw_p",
                "effective_passes",
                "encrypt_median_us",
                "decrypt_median_us",
                "encrypt_mib_s",
                "decrypt_mib_s",
                "encrypt_amortized_us_per_pass",
                "decrypt_amortized_us_per_pass",
                "encrypt_relative_to_p1",
            ]
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}",
        )
    )

    correlation = frame[
        [
            "effective_passes",
            "encrypt_median_us",
            "decrypt_median_us",
        ]
    ].corr()

    print()
    print("Correlation with effective pass count:")
    print(
        "encrypt:",
        f"{correlation.loc['effective_passes', 'encrypt_median_us']:.6f}",
    )
    print(
        "decrypt:",
        f"{correlation.loc['effective_passes', 'decrypt_median_us']:.6f}",
    )

    import numpy as np

    x = frame["effective_passes"].to_numpy(
        dtype=float
    )

    print()
    print("Linear cost model:")
    print("=" * 70)

    for label, column in [
        ("encrypt", "encrypt_median_us"),
        ("decrypt", "decrypt_median_us"),
    ]:
        y = frame[column].to_numpy(
            dtype=float
        )

        slope, intercept = np.polyfit(
            x,
            y,
            1,
        )

        predicted = (
            slope * x
            + intercept
        )

        ss_res = (
            (y - predicted) ** 2
        ).sum()

        ss_tot = (
            (y - y.mean()) ** 2
        ).sum()

        r_squared = (
            1.0
            - ss_res / ss_tot
        )

        print(
            f"{label}: "
            f"time_us = "
            f"{intercept:.3f} "
            f"+ {slope:.3f} * passes"
        )

        print(
            f"{label} R^2 = "
            f"{r_squared:.6f}"
        )

    print()
    print(
        "Encryption throughput range:"
    )
    print(
        f"{frame['encrypt_mib_s'].min():.3f}"
        " .. "
        f"{frame['encrypt_mib_s'].max():.3f}"
        " MiB/s"
    )

    print()
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
