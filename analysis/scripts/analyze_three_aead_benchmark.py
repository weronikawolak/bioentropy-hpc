#!/usr/bin/env python3

from pathlib import Path
import zlib

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "results/aggregated"
    / "three_aead_benchmark.tsv"
)

OUTPUT = (
    ROOT
    / "results/aggregated"
    / "three_aead_benchmark_summary.tsv"
)

BOOTSTRAP_REPS = 10000
BASE_SEED = 20260911


def bootstrap_median_ci(
    values,
    label,
):
    values = np.asarray(
        values,
        dtype=float,
    )

    seed = (
        BASE_SEED
        + zlib.crc32(
            label.encode("utf-8")
        )
    ) % (2**32)

    rng = np.random.default_rng(seed)

    samples = rng.choice(
        values,
        size=(
            BOOTSTRAP_REPS,
            len(values),
        ),
        replace=True,
    )

    medians = np.median(
        samples,
        axis=1,
    )

    low, high = np.quantile(
        medians,
        [0.025, 0.975],
    )

    return float(low), float(high)


def summarize_metric(
    values,
    label,
):
    values = np.asarray(
        values,
        dtype=float,
    )

    q1, q3 = np.quantile(
        values,
        [0.25, 0.75],
    )

    ci_low, ci_high = (
        bootstrap_median_ci(
            values,
            label,
        )
    )

    return {
        "median":
            float(np.median(values)),

        "q1":
            float(q1),

        "q3":
            float(q3),

        "iqr":
            float(q3 - q1),

        "ci95_low":
            ci_low,

        "ci95_high":
            ci_high,
    }


def main():
    df = pd.read_csv(
        INPUT,
        sep="\t",
    )

    if len(df) != 240:
        raise RuntimeError(
            f"Expected 240 rows, got {len(df)}"
        )

    if not df["decryption_ok"].eq(1).all():
        raise RuntimeError(
            "Decryption failure in benchmark"
        )

    rows = []

    for (
        algorithm,
        message_bytes,
    ), group in df.groupby(
        [
            "algorithm",
            "message_bytes",
        ],
        sort=True,
    ):
        if len(group) != 20:
            raise RuntimeError(
                f"{algorithm}/{message_bytes}: "
                f"expected 20 samples"
            )

        enc_ns = summarize_metric(
            group[
                "encrypt_ns_per_op"
            ],
            f"{algorithm}-{message_bytes}-enc-ns",
        )

        dec_ns = summarize_metric(
            group[
                "decrypt_ns_per_op"
            ],
            f"{algorithm}-{message_bytes}-dec-ns",
        )

        enc_speed = summarize_metric(
            group[
                "encrypt_mib_per_s"
            ],
            f"{algorithm}-{message_bytes}-enc-speed",
        )

        dec_speed = summarize_metric(
            group[
                "decrypt_mib_per_s"
            ],
            f"{algorithm}-{message_bytes}-dec-speed",
        )

        row = {
            "algorithm":
                algorithm,

            "message_bytes":
                message_bytes,

            "samples":
                len(group),

            "encrypt_median_us":
                enc_ns["median"] / 1000,

            "encrypt_q1_us":
                enc_ns["q1"] / 1000,

            "encrypt_q3_us":
                enc_ns["q3"] / 1000,

            "encrypt_iqr_us":
                enc_ns["iqr"] / 1000,

            "encrypt_ci95_low_us":
                enc_ns["ci95_low"] / 1000,

            "encrypt_ci95_high_us":
                enc_ns["ci95_high"] / 1000,

            "decrypt_median_us":
                dec_ns["median"] / 1000,

            "decrypt_q1_us":
                dec_ns["q1"] / 1000,

            "decrypt_q3_us":
                dec_ns["q3"] / 1000,

            "decrypt_iqr_us":
                dec_ns["iqr"] / 1000,

            "decrypt_ci95_low_us":
                dec_ns["ci95_low"] / 1000,

            "decrypt_ci95_high_us":
                dec_ns["ci95_high"] / 1000,

            "encrypt_median_mib_s":
                enc_speed["median"],

            "encrypt_ci95_low_mib_s":
                enc_speed["ci95_low"],

            "encrypt_ci95_high_mib_s":
                enc_speed["ci95_high"],

            "decrypt_median_mib_s":
                dec_speed["median"],

            "decrypt_ci95_low_mib_s":
                dec_speed["ci95_low"],

            "decrypt_ci95_high_mib_s":
                dec_speed["ci95_high"],
        }

        rows.append(row)

    result = pd.DataFrame(rows)

    # Descriptive speed ratios relative to Ascon.
    for message_bytes in sorted(
        result["message_bytes"].unique()
    ):
        mask = (
            result["message_bytes"]
            == message_bytes
        )

        subset = result[mask]

        ascon = subset[
            subset["algorithm"]
            == "ascon_aead128"
        ].iloc[0]

        result.loc[
            mask,
            "encrypt_speed_ratio_vs_ascon",
        ] = (
            result.loc[
                mask,
                "encrypt_median_mib_s",
            ]
            / ascon[
                "encrypt_median_mib_s"
            ]
        )

        result.loc[
            mask,
            "decrypt_speed_ratio_vs_ascon",
        ] = (
            result.loc[
                mask,
                "decrypt_median_mib_s",
            ]
            / ascon[
                "decrypt_median_mib_s"
            ]
        )

    result.to_csv(
        OUTPUT,
        sep="\t",
        index=False,
    )

    print(
        result[
            [
                "algorithm",
                "message_bytes",
                "encrypt_median_us",
                "encrypt_median_mib_s",
                "encrypt_speed_ratio_vs_ascon",
                "decrypt_median_us",
                "decrypt_median_mib_s",
                "decrypt_speed_ratio_vs_ascon",
            ]
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:.3f}",
        )
    )

    print()
    print("Saved:", OUTPUT)


if __name__ == "__main__":
    main()
