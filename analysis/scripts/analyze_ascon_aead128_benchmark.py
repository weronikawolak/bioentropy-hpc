#!/usr/bin/env python3

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "results/aggregated"
    / "ascon_aead128_benchmark.tsv"
)

OUTPUT = (
    ROOT
    / "results/aggregated"
    / "ascon_aead128_benchmark_summary.tsv"
)


def q1(series):
    return series.quantile(0.25)


def q3(series):
    return series.quantile(0.75)


def main():
    df = pd.read_csv(
        INPUT,
        sep="\t",
    )

    expected_sizes = {
        64,
        1024,
        65536,
        1048576,
    }

    if set(df["message_bytes"]) != expected_sizes:
        raise RuntimeError(
            "unexpected message sizes"
        )

    counts = (
        df.groupby("message_bytes")
        .size()
    )

    if not (counts == 20).all():
        raise RuntimeError(
            "expected 20 samples per size"
        )

    if not df["decryption_ok"].all():
        raise RuntimeError(
            "decryption failure found"
        )

    metrics = [
        "encrypt_ns_per_op",
        "decrypt_ns_per_op",
        "encrypt_mib_per_s",
        "decrypt_mib_per_s",
        "expansion_bytes",
        "expansion_percent",
        "ciphertext_bit_shannon",
        "ciphertext_byte_shannon",
        "plaintext_ciphertext_correlation",
    ]

    grouped = df.groupby(
        "message_bytes",
        sort=True,
    )

    rows = []

    for message_bytes, group in grouped:
        row = {
            "message_bytes":
                message_bytes,

            "samples":
                len(group),

            "ciphertext_bytes":
                int(
                    group[
                        "ciphertext_bytes"
                    ].iloc[0]
                ),
        }

        for metric in metrics:
            row[
                f"median_{metric}"
            ] = group[metric].median()

            row[
                f"q1_{metric}"
            ] = q1(group[metric])

            row[
                f"q3_{metric}"
            ] = q3(group[metric])

        rows.append(row)

    summary = pd.DataFrame(rows)

    summary.to_csv(
        OUTPUT,
        sep="\t",
        index=False,
    )

    print(
        "Ascon-AEAD128 benchmark summary"
    )
    print(
        "==============================="
    )

    for _, row in summary.iterrows():
        print()
        print(
            f"Message: "
            f"{int(row['message_bytes'])} B"
        )

        print(
            "  encrypt throughput : "
            f"{row['median_encrypt_mib_per_s']:.2f} MiB/s"
        )

        print(
            "  decrypt throughput : "
            f"{row['median_decrypt_mib_per_s']:.2f} MiB/s"
        )

        print(
            "  byte entropy       : "
            f"{row['median_ciphertext_byte_shannon']:.6f}"
        )

        print(
            "  plaintext/cipher corr: "
            f"{row['median_plaintext_ciphertext_correlation']:.6f}"
        )

        print(
            "  expansion          : "
            f"{row['median_expansion_bytes']:.0f} B"
        )

    print()
    print(
        "Output:",
        OUTPUT.relative_to(ROOT),
    )


if __name__ == "__main__":
    main()
