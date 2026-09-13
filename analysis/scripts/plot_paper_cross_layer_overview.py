#!/usr/bin/env python3

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "results/aggregated"
    / "cross_layer_source_summary_testu01.tsv"
)

OUTPUT = (
    ROOT
    / "results/figures"
)

df = pd.read_csv(
    INPUT,
    sep="\t",
)

df = df.sort_values(
    "nist_h_original_mean"
).reset_index(
    drop=True
)

y = list(range(len(df)))

fig, ax = plt.subplots(
    figsize=(10, 7)
)

ax.scatter(
    df["nist_h_original_mean"],
    y,
    marker="o",
    label="NIST H_original mean",
)

ax.scatter(
    df["dieharder_fail_fraction"],
    y,
    marker="x",
    label="Dieharder FAIL fraction",
)

for i, row in df.iterrows():
    status = (
        "SC PASS"
        if row[
            "testu01_smallcrush_status"
        ] == "PASSED"
        else (
            "SC flag="
            + str(
                int(
                    row[
                        "testu01_smallcrush_suspect_statistics"
                    ]
                )
            )
        )
    )

    ax.text(
        1.02,
        i,
        status,
        va="center",
        fontsize=8,
        transform=ax.get_yaxis_transform(),
    )

ax.set_yticks(y)

ax.set_yticklabels(
    df["source"]
)

ax.set_xlim(
    -0.03,
    1.03,
)

ax.set_xlabel(
    "Metric value"
)

ax.set_title(
    "Frozen local source profile: "
    "entropy estimate, Dieharder and SmallCrush"
)

ax.grid(
    axis="x",
    alpha=0.25,
)

ax.legend(
    loc="lower right"
)

fig.subplots_adjust(
    right=0.82
)

OUTPUT.mkdir(
    parents=True,
    exist_ok=True,
)

for suffix in (
    "png",
    "pdf",
):
    path = (
        OUTPUT
        / (
            "paper_cross_layer_overview."
            + suffix
        )
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
