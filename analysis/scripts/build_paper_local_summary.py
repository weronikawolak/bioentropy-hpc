#!/usr/bin/env python3

from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

CROSS = (
    ROOT
    / "results/aggregated"
    / "cross_layer_source_summary_testu01.tsv"
)

OUTPUT_TSV = (
    ROOT
    / "results/tables"
    / "paper_local_source_summary.tsv"
)

OUTPUT_MD = (
    ROOT
    / "results/tables"
    / "paper_local_source_summary.md"
)


def main():
    df = pd.read_csv(
        CROSS,
        sep="\t",
    )

    if len(df) != 10:
        raise RuntimeError(
            f"Expected 10 frozen source groups, "
            f"got {len(df)}"
        )

    table = pd.DataFrame(
        {
            "source":
                df["source"],

            "nist90b_h_original_estimate_mean":
                df[
                    "nist_h_original_mean"
                ],

            "nist90b_h_original_estimate_min":
                df[
                    "nist_h_original_min"
                ],

            "dieharder_failed":
                df[
                    "dieharder_failed_reps"
                ],

            "dieharder_weak":
                df[
                    "dieharder_weak_reps"
                ],

            "dieharder_passed":
                df[
                    "dieharder_passed_reps"
                ],

            "smallcrush":
                df[
                    "testu01_smallcrush_status"
                ],

            "smallcrush_suspect_statistics":
                df[
                    "testu01_smallcrush_suspect_statistics"
                ],

            "raw_material_unique":
                df[
                    "raw_material_unique"
                ],

            "conditioned_material_unique":
                df[
                    "conditioned_material_unique"
                ],
        }
    )

    OUTPUT_TSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    table.to_csv(
        OUTPUT_TSV,
        sep="\t",
        index=False,
    )

    lines = [
        "| Source | NIST 90B H_original estimate mean | NIST 90B H_original estimate min | "
        "Dieharder F/W/P | SmallCrush | "
        "SmallCrush suspect statistics | RAW unique | "
        "Conditioned unique |",
        "|---|---:|---:|---:|---|---:|---:|---:|",
    ]

    for _, row in table.iterrows():
        lines.append(
            f"| {row['source']} "
            f"| {row['nist90b_h_original_estimate_mean']:.6f} "
            f"| {row['nist90b_h_original_estimate_min']:.6f} "
            f"| {int(row['dieharder_failed'])}/"
            f"{int(row['dieharder_weak'])}/"
            f"{int(row['dieharder_passed'])} "
            f"| {row['smallcrush']} "
            f"| {int(row['smallcrush_suspect_statistics'])} "
            f"| {int(row['raw_material_unique'])}/20 "
            f"| {int(row['conditioned_material_unique'])}/20 |"
        )

    OUTPUT_MD.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print(
        table.to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    print()
    print("Saved:", OUTPUT_TSV)
    print("Saved:", OUTPUT_MD)


if __name__ == "__main__":
    main()
