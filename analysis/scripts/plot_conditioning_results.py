#!/usr/bin/env python3

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path("results/aggregated")
OUT = Path("results/figures")
OUT.mkdir(parents=True, exist_ok=True)


def read_tsv(path):
    with path.open() as f:
        return list(csv.DictReader(f, delimiter="\t"))


def plot_source_failures():
    rows = read_tsv(
        ROOT / "table_source_raw_vs_ascon.tsv"
    )

    labels = [r["source"] for r in rows]
    raw = [int(r["raw_failed"]) for r in rows]
    asc = [int(r["ascon_failed"]) for r in rows]

    x = np.arange(len(labels))
    width = 0.38

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.bar(
        x - width / 2,
        raw,
        width,
        label="RAW",
    )

    ax.bar(
        x + width / 2,
        asc,
        width,
        label="Ascon-XOF128",
    )

    ax.set_ylabel("FAILED replicates out of 20")
    ax.set_xlabel("Source")
    ax.set_title(
        "Replicate-level Dieharder failures "
        "before and after conditioning"
    )

    ax.set_xticks(x)
    ax.set_xticklabels(
        labels,
        rotation=45,
        ha="right",
    )

    ax.set_ylim(0, 21)
    ax.legend()

    fig.tight_layout()

    fig.savefig(
        OUT / "raw_vs_ascon_failed_replicates.png",
        dpi=300,
    )

    fig.savefig(
        OUT / "raw_vs_ascon_failed_replicates.pdf"
    )

    plt.close(fig)


def plot_collapsed_float64():
    rows = read_tsv(
        ROOT / "table_float64_collapsed_conditioning.tsv"
    )

    labels = [r["condition"] for r in rows]

    failed = [int(r["failed"]) for r in rows]
    weak = [int(r["weak"]) for r in rows]
    passed = [int(r["passed"]) for r in rows]
    invalid = [int(r["invalid"]) for r in rows]

    x = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(7, 6))

    bottom = np.zeros(len(labels))

    for values, name in [
        (failed, "FAILED"),
        (weak, "WEAK"),
        (passed, "PASSED"),
        (invalid, "INVALID"),
    ]:
        ax.bar(
            x,
            values,
            bottom=bottom,
            label=name,
        )

        bottom += np.array(values)

    ax.set_ylabel("Test-family outcomes")
    ax.set_title(
        "Collapsed Logistic float64 realizations\n"
        "RAW versus Ascon-XOF128"
    )

    ax.set_xticks(x)
    ax.set_xticklabels(labels)

    ax.set_ylim(0, 52)
    ax.legend()

    fig.tight_layout()

    fig.savefig(
        OUT / "float64_collapsed_conditioning.png",
        dpi=300,
    )

    fig.savefig(
        OUT / "float64_collapsed_conditioning.pdf"
    )

    plt.close(fig)


def main():
    plot_source_failures()
    plot_collapsed_float64()

    print("Saved figures in:", OUT)


if __name__ == "__main__":
    main()
