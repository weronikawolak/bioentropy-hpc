#!/usr/bin/env python3

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT / "results/aggregated"
    / "cross_layer_source_summary.tsv"
)

OUTPUT = (
    ROOT / "results/figures"
)

df = pd.read_csv(INPUT, sep="\t")

df = df.sort_values(
    "nist_h_original_mean",
    ascending=True,
).reset_index(drop=True)

matrix = pd.DataFrame(
    {
        "NIST H mean":
            df["nist_h_original_mean"],

        "Dieharder FAIL":
            df["dieharder_failed_reps"]
            / 20.0,

        "RAW material unique":
            df["raw_material_unique"]
            / 20.0,

        "Conditioned unique":
            df[
                "conditioned_material_unique"
            ]
            / 20.0,
    }
)

fig, ax = plt.subplots(
    figsize=(9.5, 7.0)
)

image = ax.imshow(
    matrix.to_numpy(),
    aspect="auto",
    vmin=0,
    vmax=1,
)

ax.set_xticks(
    range(len(matrix.columns))
)

ax.set_xticklabels(
    matrix.columns,
    rotation=25,
    ha="right",
)

ax.set_yticks(
    range(len(df))
)

ax.set_yticklabels(
    df["source"]
)

for row in range(
    len(df)
):
    for col in range(
        len(matrix.columns)
    ):
        value = matrix.iloc[
            row,
            col,
        ]

        ax.text(
            col,
            row,
            f"{value:.2f}",
            ha="center",
            va="center",
        )

ax.set_title(
    "Cross-layer source profile\n"
    "Entropy estimate, statistical screening "
    "and short-material diversity"
)

fig.colorbar(
    image,
    ax=ax,
    label="Normalized value [0, 1]",
)

fig.tight_layout()

OUTPUT.mkdir(
    parents=True,
    exist_ok=True,
)

for suffix in ("png", "pdf"):
    path = (
        OUTPUT
        / f"cross_layer_source_profile.{suffix}"
    )

    fig.savefig(
        path,
        dpi=300
        if suffix == "png"
        else None,
        bbox_inches="tight",
    )

    print("Saved:", path)

plt.close(fig)
