#!/usr/bin/env python3

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "results/aggregated"
    / "ascon_aead128_avalanche.tsv"
)

OUTPUT = (
    ROOT
    / "results/aggregated"
    / "ascon_aead128_avalanche_summary.tsv"
)


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

    if not (counts == 100).all():
        raise RuntimeError(
            "expected 100 avalanche trials "
            "per message size"
        )

    metrics = [
        "ciphertext_change_percent",
        "payload_change_percent",
        "tag_change_percent",
        "tag_changed_bits",
    ]

    rows = []

    for message_bytes, group in (
        df.groupby(
            "message_bytes",
            sort=True,
        )
    ):
        row = {
            "message_bytes":
                int(message_bytes),

            "trials":
                len(group),
        }

        for metric in metrics:
            row[
                f"median_{metric}"
            ] = group[metric].median()

            row[
                f"q1_{metric}"
            ] = group[metric].quantile(
                0.25
            )

            row[
                f"q3_{metric}"
            ] = group[metric].quantile(
                0.75
            )

        rows.append(row)

    summary = pd.DataFrame(rows)

    summary.to_csv(
        OUTPUT,
        sep="\t",
        index=False,
    )

    print(
        "Ascon-AEAD128 avalanche summary"
    )
    print(
        "================================"
    )

    for _, row in summary.iterrows():
        print()
        print(
            f"Message: "
            f"{int(row['message_bytes'])} B"
        )

        print(
            "  whole ciphertext : "
            f"{row['median_ciphertext_change_percent']:.4f}%"
        )

        print(
            "  payload           : "
            f"{row['median_payload_change_percent']:.4f}%"
        )

        print(
            "  authentication tag: "
            f"{row['median_tag_change_percent']:.2f}%"
        )

        print(
            "  tag changed bits  : "
            f"{row['median_tag_changed_bits']:.1f}/128"
        )

    print()
    print(
        "Important: ~50% is primarily "
        "expected for the authentication tag; "
        "whole-ciphertext percentage is not "
        "interpreted as a block-cipher avalanche criterion."
    )

    print()
    print(
        "Output:",
        OUTPUT.relative_to(ROOT),
    )


if __name__ == "__main__":
    main()
