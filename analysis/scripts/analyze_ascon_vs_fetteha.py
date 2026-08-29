#!/usr/bin/env python3

from pathlib import Path

import pandas as pd


INPUT = Path(
    "results/aggregated/"
    "ascon_vs_fetteha_64k.tsv"
)

OUTPUT = Path(
    "results/aggregated/"
    "ascon_vs_fetteha_64k_summary.tsv"
)


def main() -> None:
    frame = pd.read_csv(
        INPUT,
        sep="\t",
    )

    frame[
        "ascon_expansion_bytes"
    ] = (
        frame["ascon_ciphertext_bytes"]
        - frame["message_bytes"]
    )

    frame[
        "fetteha_expansion_bytes"
    ] = (
        frame["fetteha_ciphertext_bytes"]
        - frame["message_bytes"]
    )

    frame = frame.sort_values(
        "effective_passes"
    )

    frame.to_csv(
        OUTPUT,
        sep="\t",
        index=False,
    )

    print()
    print(
        "Ascon-AEAD128 vs Fetteha 2023"
    )
    print("=" * 115)

    print(
        frame[
            [
                "raw_p",
                "effective_passes",
                "ascon_encrypt_median_us",
                "fetteha_encrypt_median_us",
                "ascon_encrypt_mib_s",
                "fetteha_encrypt_mib_s",
                "fetteha_encrypt_slowdown",
                "ascon_decrypt_median_us",
                "fetteha_decrypt_median_us",
                "fetteha_decrypt_slowdown",
            ]
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:.3f}",
        )
    )

    print()
    print("Ciphertext expansion")
    print("=" * 70)

    print(
        frame[
            [
                "raw_p",
                "ascon_expansion_bytes",
                "fetteha_expansion_bytes",
            ]
        ].to_string(
            index=False,
        )
    )

    print()
    print(
        "Important semantic difference:"
    )
    print(
        "Ascon-AEAD128 provides authenticated "
        "encryption and a 16-byte tag."
    )
    print(
        "Fetteha comparator provides image "
        "encryption but no equivalent AEAD "
        "authentication property."
    )

    print()
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
