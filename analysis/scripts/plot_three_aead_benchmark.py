#!/usr/bin/env python3

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "results/aggregated"
    / "three_aead_benchmark_summary.tsv"
)

OUTPUT = (
    ROOT
    / "results/figures"
)

LABELS = {
    "ascon_aead128": "Ascon-AEAD128",
    "chacha20_poly1305": "ChaCha20-Poly1305",
    "aes128_gcm": "AES-128-GCM",
}


def plot_metric(
    df,
    operation,
):
    median_col = (
        f"{operation}_median_mib_s"
    )

    low_col = (
        f"{operation}_ci95_low_mib_s"
    )

    high_col = (
        f"{operation}_ci95_high_mib_s"
    )

    fig, ax = plt.subplots(
        figsize=(8.5, 5.5)
    )

    for algorithm in [
        "ascon_aead128",
        "chacha20_poly1305",
        "aes128_gcm",
    ]:
        group = (
            df[
                df["algorithm"]
                == algorithm
            ]
            .sort_values(
                "message_bytes"
            )
        )

        x = group[
            "message_bytes"
        ].to_numpy()

        y = group[
            median_col
        ].to_numpy()

        low = group[
            low_col
        ].to_numpy()

        high = group[
            high_col
        ].to_numpy()

        error = [
            y - low,
            high - y,
        ]

        ax.errorbar(
            x,
            y,
            yerr=error,
            marker="o",
            capsize=3,
            label=LABELS[algorithm],
        )

    ax.set_xscale("log", base=2)
    ax.set_yscale("log")

    ax.set_xlabel(
        "Message size [bytes]"
    )

    ax.set_ylabel(
        "Throughput [MiB/s]"
    )

    ax.set_title(
        f"AEAD {operation} throughput "
        "(median and bootstrap 95% CI)"
    )

    ax.grid(
        alpha=0.25
    )

    ax.legend()

    fig.tight_layout()

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
                f"three_aead_"
                f"{operation}_throughput."
                f"{suffix}"
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


def main():
    df = pd.read_csv(
        INPUT,
        sep="\t",
    )

    if len(df) != 12:
        raise RuntimeError(
            f"Expected 12 summary rows, "
            f"got {len(df)}"
        )

    plot_metric(
        df,
        "encrypt",
    )

    plot_metric(
        df,
        "decrypt",
    )


if __name__ == "__main__":
    main()
