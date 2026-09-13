#!/usr/bin/env python3

import csv
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "results"
    / "aggregated"
    / "nist90b_dna_corpus_summary.tsv"
)

OUTPUT_DIR = (
    ROOT
    / "results"
    / "figures"
)


def main():
    with INPUT.open(
        encoding="utf-8",
    ) as handle:
        rows = list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )

    if len(rows) != 5:
        raise RuntimeError(
            f"Expected 5 DNA corpora, "
            f"got {len(rows)}"
        )

    labels = [
        row["corpus"]
        for row in rows
    ]

    means = [
        float(row["h_mean"])
        for row in rows
    ]

    mins = [
        float(row["h_min"])
        for row in rows
    ]

    maxs = [
        float(row["h_max"])
        for row in rows
    ]

    lower = [
        mean - minimum
        for mean, minimum
        in zip(means, mins)
    ]

    upper = [
        maximum - mean
        for mean, maximum
        in zip(means, maxs)
    ]

    x = list(
        range(len(rows))
    )

    fig, ax = plt.subplots(
        figsize=(8.8, 5.6)
    )

    ax.errorbar(
        x,
        means,
        yerr=[
            lower,
            upper,
        ],
        fmt="o",
        capsize=5,
        linewidth=1.5,
    )

    ax.set_xticks(x)

    ax.set_xticklabels(
        labels,
        rotation=30,
        ha="right",
    )

    ax.set_xlabel(
        "Frozen genomic corpus"
    )

    ax.set_ylabel(
        "NIST SP 800-90B "
        "H_original (bits/bit)"
    )

    ax.set_title(
        "Empirical non-IID min-entropy "
        "of encoded DNA pairs"
    )

    ax.set_ylim(
        -0.03,
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
        / "nist90b_dna_corpora.png"
    )

    pdf = (
        OUTPUT_DIR
        / "nist90b_dna_corpora.pdf"
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
