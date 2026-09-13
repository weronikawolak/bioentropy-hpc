#!/usr/bin/env python3

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

QUALITY = (
    ROOT
    / "results/aggregated"
    / "integrated_source_quality.tsv"
)

AEAD3 = (
    ROOT
    / "results/aggregated"
    / "source_key_material_aead3_summary.tsv"
)

COLLAPSE = (
    ROOT
    / "results/aggregated"
    / "float64_collapse_aead3.tsv"
)

OUTPUT = (
    ROOT
    / "results/aggregated"
    / "cross_layer_source_summary.tsv"
)


def unique_for_mode(
    frame,
    mode,
    column,
):
    subset = frame[
        frame["mode"] == mode
    ]

    if subset.empty:
        return pd.NA

    return int(
        subset[column].nunique()
    )


def main():
    quality = pd.read_csv(
        QUALITY,
        sep="\t",
    )

    aead = pd.read_csv(
        AEAD3,
        sep="\t",
    )

    collapse = pd.read_csv(
        COLLAPSE,
        sep="\t",
    )

    if len(quality) != 10:
        raise RuntimeError(
            f"Expected 10 quality rows, got {len(quality)}"
        )

    if len(aead) != 20:
        raise RuntimeError(
            f"Expected 20 AEAD3 rows, got {len(aead)}"
        )

    rows = []

    for _, q in quality.iterrows():
        source = q["source"]

        source_aead = aead[
            aead["source"] == source
        ]

        raw = source_aead[
            source_aead["mode"] == "raw"
        ]

        conditioned = source_aead[
            source_aead["mode"]
            == "ascon_xof128"
        ]

        if (
            len(raw) != 1
            or len(conditioned) != 1
        ):
            raise RuntimeError(
                f"{source}: invalid AEAD3 mode structure"
            )

        raw = raw.iloc[0]
        conditioned = conditioned.iloc[0]

        row = {
            "source":
                source,

            "nist_h_original_mean":
                float(
                    q["nist_h_original_mean"]
                ),

            "nist_h_original_min":
                float(
                    q["nist_h_original_min"]
                ),

            "nist_h_original_max":
                float(
                    q["nist_h_original_max"]
                ),

            "dieharder_failed_reps":
                int(
                    q["dieharder_reps_failed"]
                ),

            "dieharder_weak_reps":
                int(
                    q["dieharder_reps_weak"]
                ),

            "dieharder_passed_reps":
                int(
                    q["dieharder_reps_passed"]
                ),

            "dieharder_fail_fraction":
                float(
                    q["dieharder_fail_fraction"]
                ),

            "raw_material_unique":
                int(
                    raw["material_unique"]
                ),

            "raw_material_collisions":
                int(
                    raw["material_collisions"]
                ),

            "conditioned_material_unique":
                int(
                    conditioned[
                        "material_unique"
                    ]
                ),

            "conditioned_material_collisions":
                int(
                    conditioned[
                        "material_collisions"
                    ]
                ),

            "raw_ascon_key_collisions":
                int(
                    raw[
                        "ascon_key_collisions"
                    ]
                ),

            "raw_chacha_key_collisions":
                int(
                    raw[
                        "chacha_key_collisions"
                    ]
                ),

            "raw_aes_key_collisions":
                int(
                    raw[
                        "aes_key_collisions"
                    ]
                ),

            "conditioned_ascon_key_collisions":
                int(
                    conditioned[
                        "ascon_key_collisions"
                    ]
                ),

            "conditioned_chacha_key_collisions":
                int(
                    conditioned[
                        "chacha_key_collisions"
                    ]
                ),

            "conditioned_aes_key_collisions":
                int(
                    conditioned[
                        "aes_key_collisions"
                    ]
                ),

            "raw_ascon_ciphertext_collisions":
                int(
                    raw[
                        "ascon_ciphertext_collisions"
                    ]
                ),

            "raw_chacha_ciphertext_collisions":
                int(
                    raw[
                        "chacha_ciphertext_collisions"
                    ]
                ),

            "raw_aes_ciphertext_collisions":
                int(
                    raw[
                        "aes_ciphertext_collisions"
                    ]
                ),
        }

        rows.append(row)

    result = pd.DataFrame(rows)

    # Targeted float64 collapse evidence.
    mask = (
        result["source"]
        == "logistic-float64"
    )

    for column in [
        "collapse_pre_raw_unique",
        "collapse_pre_conditioned_unique",
        "collapse_post_raw_unique",
        "collapse_post_conditioned_unique",
    ]:
        result[column] = pd.NA

    result.loc[
        mask,
        "collapse_pre_raw_unique",
    ] = unique_for_mode(
        collapse,
        "pre_collapse_raw",
        "material_sha256",
    )

    result.loc[
        mask,
        "collapse_pre_conditioned_unique",
    ] = unique_for_mode(
        collapse,
        "pre_collapse_local_ascon_xof128",
        "material_sha256",
    )

    result.loc[
        mask,
        "collapse_post_raw_unique",
    ] = unique_for_mode(
        collapse,
        "post_collapse_raw",
        "material_sha256",
    )

    result.loc[
        mask,
        "collapse_post_conditioned_unique",
    ] = unique_for_mode(
        collapse,
        "post_collapse_local_ascon_xof128",
        "material_sha256",
    )

    result.to_csv(
        OUTPUT,
        sep="\t",
        index=False,
    )

    print(
        "PASSED: final cross-layer "
        "source table built"
    )

    print()
    print(
        result[
            [
                "source",
                "nist_h_original_mean",
                "dieharder_failed_reps",
                "raw_material_unique",
                "conditioned_material_unique",
                "collapse_pre_raw_unique",
                "collapse_post_raw_unique",
                "collapse_post_conditioned_unique",
            ]
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    print()
    print("Saved:", OUTPUT)


if __name__ == "__main__":
    main()
