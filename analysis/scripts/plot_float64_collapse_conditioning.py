#!/usr/bin/env python3

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "results"
    / "aggregated"
    / "float64_collapse_conditioned_material.tsv"
)

OUTPUT = (
    ROOT
    / "results"
    / "figures"
)

df = pd.read_csv(
    INPUT,
    sep="\t",
    dtype={"replicate_id": str},
)

if len(df) != 5:
    raise RuntimeError(
        f"Expected 5 realizations, got {len(df)}"
    )

labels = [
    f"rep{x}"
    for x in df["replicate_id"]
]

raw_p1 = [0.0] * len(df)

conditioned_p1 = (
    df["conditioned_p1"]
    .astype(float)
    .tolist()
)

x = list(range(len(df)))
width = 0.36

fig, ax = plt.subplots(
    figsize=(8.5, 5.2)
)

ax.bar(
    [i - width / 2 for i in x],
    raw_p1,
    width,
    label="Post-collapse RAW",
)

ax.bar(
    [i + width / 2 for i in x],
    conditioned_p1,
    width,
    label="Ascon-XOF128 conditioned",
)

ax.set_xticks(x)
ax.set_xticklabels(labels)

ax.set_ylim(0, 0.65)

ax.set_ylabel("P(1) in 608-bit key-material window")

ax.set_xlabel(
    "Frozen Logistic float64 realization"
)

ax.set_title(
    "Conditioning masks visible post-collapse degeneracy"
)

ax.legend()

fig.tight_layout()

OUTPUT.mkdir(
    parents=True,
    exist_ok=True,
)

for suffix in ("png", "pdf"):
    path = (
        OUTPUT
        / f"float64_collapse_conditioning.{suffix}"
    )

    fig.savefig(
        path,
        dpi=300 if suffix == "png" else None,
        bbox_inches="tight",
    )

    print("Saved:", path)

plt.close(fig)
