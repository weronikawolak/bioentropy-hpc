#!/usr/bin/env python3

from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

CROSS = (
    ROOT
    / "results/aggregated"
    / "cross_layer_source_summary.tsv"
)

TESTU01 = (
    ROOT
    / "results/aggregated"
    / "testu01_smallcrush_detailed_summary.tsv"
)

OUTPUT = (
    ROOT
    / "results/aggregated"
    / "cross_layer_source_summary_testu01.tsv"
)


def main():
    cross = pd.read_csv(
        CROSS,
        sep="\t",
    )

    test = pd.read_csv(
        TESTU01,
        sep="\t",
    )

    # CTR_DRBG was added after the original frozen
    # 10-source cross-layer campaign.
    test = test[
        test["source"]
        != "ctr-drbg-aes256"
    ].copy()

    if len(cross) != 10:
        raise RuntimeError(
            f"Expected 10 cross-layer rows, "
            f"got {len(cross)}"
        )

    missing = (
        set(cross["source"])
        - set(test["source"])
    )

    extra = (
        set(test["source"])
        - set(cross["source"])
    )

    if missing or extra:
        raise RuntimeError(
            f"Source mismatch. "
            f"missing={sorted(missing)}, "
            f"extra={sorted(extra)}"
        )

    keep = test[
        [
            "source",
            "testu01_status",
            "suspect_statistics",
            "words_consumed",
            "bytes_consumed",
        ]
    ].rename(
        columns={
            "testu01_status":
                "testu01_smallcrush_status",
            "suspect_statistics":
                "testu01_smallcrush_suspect_statistics",
            "words_consumed":
                "testu01_smallcrush_words_consumed",
            "bytes_consumed":
                "testu01_smallcrush_bytes_consumed",
        }
    )

    result = cross.merge(
        keep,
        on="source",
        how="left",
        validate="one_to_one",
    )

    result.to_csv(
        OUTPUT,
        sep="\t",
        index=False,
    )

    print(
        result[
            [
                "source",
                "nist_h_original_mean",
                "dieharder_failed_reps",
                "testu01_smallcrush_status",
                "testu01_smallcrush_suspect_statistics",
            ]
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    print()
    print("Saved:", OUTPUT)


if __name__ == "__main__":
    main()
