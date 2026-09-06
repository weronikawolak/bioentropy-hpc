#!/usr/bin/env python3

from pathlib import Path

import pandas as pd


INPUT = Path(
    "results/aggregated/"
    "fetteha_synthetic_probe.tsv"
)

OUTPUT = Path(
    "results/aggregated/"
    "fetteha_synthetic_probe_summary.tsv"
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
                "image",
                "mode",
            ],
            as_index=False,
        )
        .agg(
            trials=(
                "trial",
                "count",
            ),
            raw_p_base=(
                "raw_p_base",
                "first",
            ),
            effective_p_base=(
                "effective_p_base",
                "first",
            ),
            modified_p_min=(
                "raw_p_modified",
                "min",
            ),
            modified_p_max=(
                "raw_p_modified",
                "max",
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

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary.to_csv(
        OUTPUT,
        sep="\t",
        index=False,
    )

    print()
    print(
        "Fetteha 2023 synthetic image probe"
    )
    print("=" * 105)

    print(
        summary.to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    print()
    print("Reference context:")
    print("  NPCR ~ 99.61%")
    print("  UACI ~ 33.46%")

    print()
    print("Modes:")
    print(
        "  single_pixel_plus1       "
        "-> changes raw P"
    )
    print(
        "  single_pixel_preserve_p  "
        "-> keeps raw P unchanged"
    )

    print()
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
