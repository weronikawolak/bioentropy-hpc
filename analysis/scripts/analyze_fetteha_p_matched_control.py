#!/usr/bin/env python3

from pathlib import Path

import pandas as pd


INPUT = Path(
    "results/aggregated/"
    "fetteha_p_matched_control.tsv"
)

OUTPUT = Path(
    "results/aggregated/"
    "fetteha_p_matched_control_summary.tsv"
)


def main() -> None:
    frame = pd.read_csv(
        INPUT,
        sep="\t",
    )

    summary = (
        frame
        .groupby(
            [
                "raw_p_base",
                "effective_p_base",
                "mode",
            ],
            as_index=False,
        )
        .agg(
            trials=(
                "trial",
                "count",
            ),
            modified_raw_p=(
                "raw_p_modified",
                "first",
            ),
            modified_effective_p=(
                "effective_p_modified",
                "first",
            ),
            pass_delta=(
                "effective_pass_delta",
                "first",
            ),
            plaintext_changed_pixels=(
                "plaintext_changed_pixels",
                "first",
            ),
            plaintext_total_abs_delta=(
                "plaintext_total_abs_delta",
                "first",
            ),
            npcr_mean=(
                "npcr_percent",
                "mean",
            ),
            npcr_std=(
                "npcr_percent",
                "std",
            ),
            uaci_mean=(
                "uaci_percent",
                "mean",
            ),
            uaci_std=(
                "uaci_percent",
                "std",
            ),
        )
    )

    summary.to_csv(
        OUTPUT,
        sep="\t",
        index=False,
    )

    print()
    print(
        "Fetteha matched-magnitude P control"
    )
    print("=" * 135)

    print(
        summary.to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    change = summary[
        summary["mode"]
        == "change_p_plus1"
    ].copy()

    preserve = summary[
        summary["mode"]
        == "preserve_p_plus1_minus1"
    ].copy()

    merged = change.merge(
        preserve,
        on=[
            "raw_p_base",
            "effective_p_base",
        ],
        suffixes=(
            "_change",
            "_preserve",
        ),
    )

    merged[
        "npcr_difference"
    ] = (
        merged["npcr_mean_change"]
        - merged["npcr_mean_preserve"]
    )

    merged[
        "uaci_difference"
    ] = (
        merged["uaci_mean_change"]
        - merged["uaci_mean_preserve"]
    )

    print()
    print(
        "Matched contrast"
    )
    print("=" * 120)

    columns = [
        "raw_p_base",
        "effective_p_base",
        "modified_effective_p_change",
        "pass_delta_change",
        "npcr_mean_change",
        "npcr_mean_preserve",
        "npcr_difference",
        "uaci_mean_change",
        "uaci_mean_preserve",
        "uaci_difference",
    ]

    print(
        merged[columns].to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    print()
    print("Overall means")
    print("=" * 70)

    for mode in [
        "change_p_plus1",
        "preserve_p_plus1_minus1",
    ]:
        subset = frame[
            frame["mode"] == mode
        ]

        print(
            f"{mode}: "
            f"NPCR={subset['npcr_percent'].mean():.6f}%  "
            f"UACI={subset['uaci_percent'].mean():.6f}%"
        )

    print()
    print("Reference:")
    print("  NPCR ~ 99.61%")
    print("  UACI ~ 33.46%")
    print()
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
