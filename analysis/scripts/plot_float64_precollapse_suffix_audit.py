#!/usr/bin/env python3

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "results/aggregated"
    / "float64_precollapse_suffix_audit.tsv"
)

OUTPUT = (
    ROOT
    / "results/figures"
)

df = pd.read_csv(
    INPUT,
    sep="\t",
    dtype={
        "rep_a": str,
        "rep_b": str,
    },
)

labels = [
    f"{a}-{b}"
    for a, b in zip(
        df["rep_a"],
        df["rep_b"],
    )
]

values = (
    df["common_suffix_bits"]
    .astype(int)
    .tolist()
)

fig, ax = plt.subplots(
    figsize=(10, 5.5)
)

bars = ax.bar(
    labels,
    values,
)

ax.set_yscale("log")

ax.set_ylabel(
    "Common collapse-aligned suffix length [bits]"
)

ax.set_xlabel(
    "Frozen Logistic float64 realization pair"
)

ax.set_title(
    "Long pre-collapse output convergence in float64 Logistic Map"
)

ax.tick_params(
    axis="x",
    rotation=45,
)

for bar, value in zip(
    bars,
    values,
):
    if value >= 1000:
        label = f"{value / 1_000_000:.3f}M"
    else:
        label = str(value)

    ax.text(
        bar.get_x()
        + bar.get_width() / 2,
        value * 1.15,
        label,
        ha="center",
        va="bottom",
        fontsize=8,
    )

fig.tight_layout()

OUTPUT.mkdir(
    parents=True,
    exist_ok=True,
)

for suffix in ("png", "pdf"):
    path = (
        OUTPUT
        / f"float64_precollapse_suffix_audit.{suffix}"
    )

    fig.savefig(
        path,
        dpi=300 if suffix == "png" else None,
        bbox_inches="tight",
    )

    print("Saved:", path)

plt.close(fig)
