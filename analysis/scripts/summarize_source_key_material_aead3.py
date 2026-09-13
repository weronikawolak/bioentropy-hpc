#!/usr/bin/env python3

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "results/aggregated"
    / "source_key_material_aead3_campaign.tsv"
)

OUTPUT = (
    ROOT
    / "results/aggregated"
    / "source_key_material_aead3_summary.tsv"
)


def collision_count(series):
    return len(series) - series.nunique()


def main():
    df = pd.read_csv(
        INPUT,
        sep="\t",
    )

    if len(df) != 400:
        raise RuntimeError(
            f"Expected 400 records, got {len(df)}"
        )

    required = [
        "material_sha256",
        "ascon_key_sha256",
        "ascon_nonce_sha256",
        "ascon_ciphertext_sha256",
        "chacha_key_sha256",
        "chacha_nonce_sha256",
        "chacha_ciphertext_sha256",
        "aes_key_sha256",
        "aes_nonce_sha256",
        "aes_ciphertext_sha256",
    ]

    rows = []

    grouped = df.groupby(
        ["source", "mode"],
        sort=True,
    )

    for (source, mode), group in grouped:
        if len(group) != 20:
            raise RuntimeError(
                f"{source}/{mode}: "
                f"expected 20 rows, got {len(group)}"
            )

        row = {
            "source":
                source,

            "mode":
                mode,

            "replicates":
                len(group),

            "material_unique":
                group[
                    "material_sha256"
                ].nunique(),

            "material_collisions":
                collision_count(
                    group["material_sha256"]
                ),

            "ascon_key_unique":
                group[
                    "ascon_key_sha256"
                ].nunique(),

            "ascon_key_collisions":
                collision_count(
                    group["ascon_key_sha256"]
                ),

            "ascon_nonce_unique":
                group[
                    "ascon_nonce_sha256"
                ].nunique(),

            "ascon_nonce_collisions":
                collision_count(
                    group["ascon_nonce_sha256"]
                ),

            "ascon_ciphertext_unique":
                group[
                    "ascon_ciphertext_sha256"
                ].nunique(),

            "ascon_ciphertext_collisions":
                collision_count(
                    group[
                        "ascon_ciphertext_sha256"
                    ]
                ),

            "chacha_key_unique":
                group[
                    "chacha_key_sha256"
                ].nunique(),

            "chacha_key_collisions":
                collision_count(
                    group["chacha_key_sha256"]
                ),

            "chacha_nonce_unique":
                group[
                    "chacha_nonce_sha256"
                ].nunique(),

            "chacha_nonce_collisions":
                collision_count(
                    group["chacha_nonce_sha256"]
                ),

            "chacha_ciphertext_unique":
                group[
                    "chacha_ciphertext_sha256"
                ].nunique(),

            "chacha_ciphertext_collisions":
                collision_count(
                    group[
                        "chacha_ciphertext_sha256"
                    ]
                ),

            "aes_key_unique":
                group[
                    "aes_key_sha256"
                ].nunique(),

            "aes_key_collisions":
                collision_count(
                    group["aes_key_sha256"]
                ),

            "aes_nonce_unique":
                group[
                    "aes_nonce_sha256"
                ].nunique(),

            "aes_nonce_collisions":
                collision_count(
                    group["aes_nonce_sha256"]
                ),

            "aes_ciphertext_unique":
                group[
                    "aes_ciphertext_sha256"
                ].nunique(),

            "aes_ciphertext_collisions":
                collision_count(
                    group[
                        "aes_ciphertext_sha256"
                    ]
                ),

            "all_zero_materials":
                int(
                    group[
                        "zero_bytes"
                    ].eq(104).sum()
                ),

            "zero_bytes_mean":
                group[
                    "zero_bytes"
                ].mean(),

            "zero_bytes_max":
                group[
                    "zero_bytes"
                ].max(),

            "unique_bytes_mean":
                group[
                    "unique_bytes"
                ].mean(),

            "unique_bytes_min":
                group[
                    "unique_bytes"
                ].min(),

            "p1_mean":
                group["p1"].mean(),

            "p1_min":
                group["p1"].min(),

            "p1_max":
                group["p1"].max(),

            "provenance_pass":
                int(
                    group[
                        "provenance_pass"
                    ].sum()
                ),

            "ascon_roundtrip_pass":
                int(
                    group[
                        "ascon_roundtrip"
                    ].sum()
                ),

            "chacha_roundtrip_pass":
                int(
                    group[
                        "chacha_roundtrip"
                    ].sum()
                ),

            "aes_roundtrip_pass":
                int(
                    group[
                        "aes_roundtrip"
                    ].sum()
                ),
        }

        rows.append(row)

    result = pd.DataFrame(rows)

    if len(result) != 20:
        raise RuntimeError(
            f"Expected 20 groups, got {len(result)}"
        )

    result.to_csv(
        OUTPUT,
        sep="\t",
        index=False,
    )

    print(
        "PASSED: 400 input realizations"
    )
    print(
        "PASSED: 20 source/mode groups"
    )
    print("Saved:", OUTPUT)
    print()

    columns = [
        "source",
        "mode",
        "material_unique",
        "material_collisions",
        "ascon_key_collisions",
        "chacha_key_collisions",
        "aes_key_collisions",
        "ascon_nonce_collisions",
        "chacha_nonce_collisions",
        "aes_nonce_collisions",
        "all_zero_materials",
        "unique_bytes_min",
        "p1_mean",
    ]

    print(
        result[
            columns
        ].to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()
