#!/usr/bin/env python3

import csv
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "results"
    / "aggregated"
    / "nist90b_prefix1m_source_summary.tsv"
)

OUTPUT_DIR = (
    ROOT
    / "results"
    / "figures"
)


def main():
    with INPUT.open(
        encoding="utf-8",
    ) as f:
        rows = list(
            csv.DictReader(
                f,
                delimiter="\t",
            )
        )

    if len(rows) != 10:
        raise RuntimeError(
            f"Expected 10 sources, got {len(rows)}"
        )

    labels = [
        r["source"]
        for r in rows
    ]

    means = [
        float(r["h_mean"])
        for r in rows
    ]

    mins = [
        float(r["h_min"])
        for r in rows
    ]

    maxs = [
        float(r["h_max"])
        for r in rows
    ]

    lower = [
        mean - low
        for mean, low
        in zip(means, mins)
    ]

    upper = [
        high - mean
        for mean, high
        in zip(means, maxs)
    ]

    fig, ax = plt.subplots(
        figsize=(10.5, 6.0)
    )

    x = range(len(labels))

    ax.errorbar(
        x,
        means,
        yerr=[
            lower,
            upper,
        ],
        fmt="o",
        capsize=4,
        linewidth=1.5,
    )

    ax.set_xticks(
        list(x)
    )

    ax.set_xticklabels(
        labels,
        rotation=45,
        ha="right",
    )

    ax.set_ylabel(
        "NIST SP 800-90B H_original (bits/bit)"
    )

    ax.set_xlabel(
        "Frozen source group"
    )

    ax.set_title(
        "Empirical non-IID min-entropy "
        "for 1M-bit source prefixes"
    )

    ax.set_ylim(
        -0.04,
        1.0,
    )

    ax.grid(
        True,
        axis="y",
        alpha=0.25,
    )

    fig.tight_layout()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    png = (
        OUTPUT_DIR
        / "nist90b_prefix1m_sources.png"
    )

    pdf = (
        OUTPUT_DIR
        / "nist90b_prefix1m_sources.pdf"
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

    print("PNG:", png)
    print("PDF:", pdf)


if __name__ == "__main__":
    main()
