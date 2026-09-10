#!/usr/bin/env python3

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT / "results/aggregated/"
    "integrated_source_quality.tsv"
)

OUTPUT_DIR = (
    ROOT / "results/figures"
)


df = pd.read_csv(
    INPUT,
    sep="\t",
)

if len(df) != 10:
    raise RuntimeError(
        f"Expected 10 sources, got {len(df)}"
    )

x = df[
    "nist_h_original_mean"
]

y = df[
    "dieharder_fail_fraction"
]

fig, ax = plt.subplots(
    figsize=(9.5, 6.3)
)

ax.scatter(
    x,
    y,
    s=75,
)

for _, row in df.iterrows():
    label = (
        str(row["source"])
        .replace("logistic-", "")
        .replace("cells", "")
    )

    ax.annotate(
        label,
        (
            row[
                "nist_h_original_mean"
            ],
            row[
                "dieharder_fail_fraction"
            ],
        ),
        xytext=(6, 5),
        textcoords="offset points",
        fontsize=8,
    )

ax.set_xlabel(
    "Mean empirical non-IID H_original\n"
    "(first 1,000,000 bits)"
)

ax.set_ylabel(
    "Fraction of frozen realizations "
    "classified FAILED by Dieharder"
)

ax.set_xlim(
    -0.03,
    1.0,
)

ax.set_ylim(
    -0.05,
    1.05,
)

ax.set_title(
    "Cross-view of empirical entropy "
    "and statistical screening"
)

ax.grid(
    alpha=0.25
)

fig.tight_layout()

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

png = (
    OUTPUT_DIR
    / "integrated_source_quality.png"
)

pdf = (
    OUTPUT_DIR
    / "integrated_source_quality.pdf"
)

fig.savefig(
    png,
    dpi=300,
    bbox_inches="tight",
)

fig.savefig(
    pdf,
    bbox_inches="tight",
)

plt.close(fig)

print("Saved:", png)
print("Saved:", pdf)
