#!/usr/bin/env python3

from pathlib import Path

import pandas as pd


INPUT = Path(
    "results/aggregated/"
    "fetteha_p_confounding.tsv"
)

OUTPUT = Path(
    "results/aggregated/"
    "fetteha_p_confounding_summary.tsv"
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
            cipher_entropy=(
                "cipher_entropy_base",
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
        "Fetteha P-confounding analysis"
    )
    print("=" * 130)

    print(
        summary.to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    change = summary[
        summary["mode"] == "change_p"
    ].copy()

    preserve = summary[
        summary["mode"] == "preserve_p"
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
        "npcr_change_minus_preserve"
    ] = (
        merged["npcr_mean_change"]
        - merged["npcr_mean_preserve"]
    )

    merged[
        "uaci_change_minus_preserve"
    ] = (
        merged["uaci_mean_change"]
        - merged["uaci_mean_preserve"]
    )

    print()
    print(
        "Direct change-P vs preserve-P contrast"
    )
    print("=" * 110)

    print(
        merged[
            [
                "raw_p_base",
                "effective_p_base",
                "modified_effective_p_change",
                "pass_delta_change",
                "npcr_mean_change",
                "npcr_mean_preserve",
                "npcr_change_minus_preserve",
                "uaci_mean_change",
                "uaci_mean_preserve",
                "uaci_change_minus_preserve",
            ]
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    print()
    print("Reference:")
    print("  NPCR ~ 99.61%")
    print("  UACI ~ 33.46%")
    print()
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
