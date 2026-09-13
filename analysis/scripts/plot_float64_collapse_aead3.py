#!/usr/bin/env python3

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "results/aggregated"
    / "float64_collapse_aead3.tsv"
)

OUT = ROOT / "results/figures"


df = pd.read_csv(
    INPUT,
    sep="\t",
)

order = [
    "pre_collapse_raw",
    "pre_collapse_local_ascon_xof128",
    "post_collapse_raw",
    "post_collapse_local_ascon_xof128",
]

labels = [
    "Pre\nRAW",
    "Pre\nAscon-XOF",
    "Post\nRAW",
    "Post\nAscon-XOF",
]

unique_material = []
p1 = []

for mode in order:
    group = df[
        df["mode"] == mode
    ]

    unique_material.append(
        group[
            "material_sha256"
        ].nunique()
    )

    p1.append(
        group["p1"].mean()
    )

x = list(range(len(order)))

fig, ax = plt.subplots(
    figsize=(8.5, 5.3)
)

bars = ax.bar(
    x,
    unique_material,
)

ax.set_xticks(x)
ax.set_xticklabels(labels)

ax.set_ylabel(
    "Unique 104-byte materials (out of 5)"
)

ax.set_ylim(0, 5.6)

ax.set_title(
    "Finite-precision collapse propagates through conditioning"
)

for bar, value in zip(
    bars,
    unique_material,
):
    ax.text(
        bar.get_x()
        + bar.get_width() / 2,
        value + 0.08,
        f"{value}/5",
        ha="center",
        va="bottom",
    )

fig.tight_layout()

OUT.mkdir(
    parents=True,
    exist_ok=True,
)

for suffix in ("png", "pdf"):
    path = (
        OUT
        / f"float64_collapse_aead3.{suffix}"
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
