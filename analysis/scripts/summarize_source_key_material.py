#!/usr/bin/env python3

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "results"
    / "aggregated"
    / "source_key_material_campaign.tsv"
)

OUTPUT = (
    ROOT
    / "results"
    / "aggregated"
    / "source_key_material_summary.tsv"
)

df = pd.read_csv(
    INPUT,
    sep="\t",
    dtype={"replicate_id": str},
)

if len(df) != 400:
    raise RuntimeError(
        f"Expected 400 rows, got {len(df)}"
    )

rows = []

for (source, mode), group in df.groupby(
    ["source", "mode"],
    sort=True,
):
    if len(group) != 20:
        raise RuntimeError(
            f"{source}/{mode}: "
            f"expected 20 rows, got {len(group)}"
        )

    def unique_and_collisions(column):
        unique = group[column].nunique()
        return unique, len(group) - unique

    material_u, material_c = (
        unique_and_collisions(
            "material_sha256"
        )
    )

    ascon_key_u, ascon_key_c = (
        unique_and_collisions(
            "ascon_key_sha256"
        )
    )

    ascon_nonce_u, ascon_nonce_c = (
        unique_and_collisions(
            "ascon_nonce_sha256"
        )
    )

    ascon_ct_u, ascon_ct_c = (
        unique_and_collisions(
            "ascon_ciphertext_sha256"
        )
    )

    chacha_key_u, chacha_key_c = (
        unique_and_collisions(
            "chacha_key_sha256"
        )
    )

    chacha_nonce_u, chacha_nonce_c = (
        unique_and_collisions(
            "chacha_nonce_sha256"
        )
    )

    chacha_ct_u, chacha_ct_c = (
        unique_and_collisions(
            "chacha_ciphertext_sha256"
        )
    )

    rows.append({
        "source": source,
        "mode": mode,
        "realizations": len(group),

        "material_unique": material_u,
        "material_collisions": material_c,

        "ascon_key_unique": ascon_key_u,
        "ascon_key_collisions": ascon_key_c,

        "ascon_nonce_unique": ascon_nonce_u,
        "ascon_nonce_collisions": ascon_nonce_c,

        "ascon_ciphertext_unique": ascon_ct_u,
        "ascon_ciphertext_collisions": ascon_ct_c,

        "chacha_key_unique": chacha_key_u,
        "chacha_key_collisions": chacha_key_c,

        "chacha_nonce_unique": chacha_nonce_u,
        "chacha_nonce_collisions": chacha_nonce_c,

        "chacha_ciphertext_unique": chacha_ct_u,
        "chacha_ciphertext_collisions": chacha_ct_c,

        "all_zero_materials": int(
            (group["zero_bytes"] == 76).sum()
        ),

        "zero_bytes_mean": (
            group["zero_bytes"].mean()
        ),

        "zero_bytes_max": (
            group["zero_bytes"].max()
        ),

        "unique_bytes_mean": (
            group["unique_bytes"].mean()
        ),

        "unique_bytes_min": (
            group["unique_bytes"].min()
        ),

        "p1_mean": group["p1"].mean(),
        "p1_min": group["p1"].min(),
        "p1_max": group["p1"].max(),

        "provenance_pass": int(
            group["provenance_pass"].sum()
        ),

        "ascon_roundtrip_pass": int(
            group["ascon_roundtrip"].sum()
        ),

        "chacha_roundtrip_pass": int(
            group["chacha_roundtrip"].sum()
        ),
    })

summary = pd.DataFrame(rows)

if len(summary) != 20:
    raise RuntimeError(
        f"Expected 20 summary rows, "
        f"got {len(summary)}"
    )

summary.to_csv(
    OUTPUT,
    sep="\t",
    index=False,
)

print("PASSED: 400 input realizations")
print("PASSED: 20 source/mode groups")
print("Saved:", OUTPUT)
print()

print(
    summary[
        [
            "source",
            "mode",
            "material_unique",
            "material_collisions",
            "ascon_key_collisions",
            "chacha_key_collisions",
            "all_zero_materials",
            "unique_bytes_min",
            "p1_mean",
        ]
    ].to_string(index=False)
)
