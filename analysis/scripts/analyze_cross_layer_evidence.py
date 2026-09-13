#!/usr/bin/env python3

from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT / "results/aggregated"
    / "cross_layer_source_summary.tsv"
)

OUTPUT = (
    ROOT / "results/aggregated"
    / "cross_layer_descriptive_stats.tsv"
)


def spearman(a, b):
    return (
        pd.Series(a).rank()
        .corr(pd.Series(b).rank())
    )


def main():
    df = pd.read_csv(INPUT, sep="\t")

    if len(df) != 10:
        raise RuntimeError(
            f"Expected 10 sources, got {len(df)}"
        )

    low_h = (
        df["nist_h_original_mean"] < 0.01
    )

    raw_unique_all = (
        df["raw_material_unique"] == 20
    )

    cond_unique_all = (
        df["conditioned_material_unique"] == 20
    )

    rho = spearman(
        df["nist_h_original_mean"],
        df["dieharder_fail_fraction"],
    )

    result = pd.DataFrame(
        [
            {
                "sources": len(df),
                "very_low_h_sources":
                    int(low_h.sum()),

                "very_low_h_with_20of20_raw_unique":
                    int(
                        (
                            low_h
                            & raw_unique_all
                        ).sum()
                    ),

                "sources_with_any_dieharder_fail":
                    int(
                        (
                            df[
                                "dieharder_failed_reps"
                            ] > 0
                        ).sum()
                    ),

                "sources_with_20of20_raw_unique":
                    int(
                        raw_unique_all.sum()
                    ),

                "sources_with_20of20_conditioned_unique":
                    int(
                        cond_unique_all.sum()
                    ),

                "spearman_h_vs_dieharder_fail_fraction":
                    rho,
            }
        ]
    )

    result.to_csv(
        OUTPUT,
        sep="\t",
        index=False,
    )

    print(result.to_string(index=False))

    print()
    print(
        "NOTE: Spearman rho is descriptive only; "
        "n=10 heterogeneous deterministic source groups."
    )

    print()
    print("Low-H sources:")

    print(
        df.loc[
            low_h,
            [
                "source",
                "nist_h_original_mean",
                "dieharder_failed_reps",
                "raw_material_unique",
            ],
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:.8f}",
        )
    )

    print()
    print("Saved:", OUTPUT)


if __name__ == "__main__":
    main()
