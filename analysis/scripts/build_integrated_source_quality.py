#!/usr/bin/env python3

from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

NIST = (
    ROOT / "results/aggregated/"
    "nist90b_prefix1m_source_summary.tsv"
)

DIEHARDER = (
    ROOT / "results/aggregated/"
    "dieharder_campaign_full20_sources.tsv"
)

KEYS = (
    ROOT / "results/aggregated/"
    "source_key_material_summary.tsv"
)

COLLAPSE = (
    ROOT / "results/aggregated/"
    "float64_collapse_conditioned_material.tsv"
)

OUTPUT = (
    ROOT / "results/aggregated/"
    "integrated_source_quality.tsv"
)


def pick(frame, candidates, description):
    lower = {
        str(column).lower(): column
        for column in frame.columns
    }

    for candidate in candidates:
        if candidate.lower() in lower:
            return lower[candidate.lower()]

    raise RuntimeError(
        f"Could not locate {description} column.\n"
        f"Available: {list(frame.columns)}"
    )


def main():
    for path in (
        NIST,
        DIEHARDER,
        KEYS,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)

    nist = pd.read_csv(
        NIST,
        sep="\t",
    )

    dieharder = pd.read_csv(
        DIEHARDER,
        sep="\t",
    )

    keys = pd.read_csv(
        KEYS,
        sep="\t",
    )

    n_source = pick(
        nist,
        ["source"],
        "NIST source",
    )

    n_mean = pick(
        nist,
        [
            "h_original_mean",
            "mean_h_original",
            "h_mean",
            "mean_h",
            "mean",
        ],
        "NIST mean H_original",
    )

    n_min = pick(
        nist,
        [
            "h_original_min",
            "min_h_original",
            "h_min",
            "min_h",
            "min",
        ],
        "NIST minimum H_original",
    )

    n_max = pick(
        nist,
        [
            "h_original_max",
            "max_h_original",
            "h_max",
            "max_h",
            "max",
        ],
        "NIST maximum H_original",
    )

    d_source = pick(
        dieharder,
        ["source"],
        "Dieharder source",
    )

    required_dieharder = [
        "replicates",
        "reps_failed",
        "reps_weak",
        "reps_passed",
    ]

    for column in required_dieharder:
        if column not in dieharder.columns:
            raise RuntimeError(
                f"Missing Dieharder column: {column}"
            )

    expected_sources = set(
        nist[n_source]
    )

    if expected_sources != set(
        dieharder[d_source]
    ):
        raise RuntimeError(
            "NIST and Dieharder source sets differ"
        )

    if expected_sources != set(
        keys["source"]
    ):
        raise RuntimeError(
            "NIST and key-material source sets differ"
        )

    if len(expected_sources) != 10:
        raise RuntimeError(
            f"Expected 10 sources, "
            f"got {len(expected_sources)}"
        )

    raw = (
        keys[
            keys["mode"] == "raw"
        ]
        .set_index("source")
    )

    conditioned = (
        keys[
            keys["mode"] == "ascon_xof128"
        ]
        .set_index("source")
    )

    nist = nist.set_index(
        n_source
    )

    dieharder = dieharder.set_index(
        d_source
    )

    rows = []

    for source in sorted(
        expected_sources
    ):
        d = dieharder.loc[source]

        row = {
            "source":
                source,

            "nist_h_original_mean":
                float(
                    nist.loc[
                        source,
                        n_mean,
                    ]
                ),

            "nist_h_original_min":
                float(
                    nist.loc[
                        source,
                        n_min,
                    ]
                ),

            "nist_h_original_max":
                float(
                    nist.loc[
                        source,
                        n_max,
                    ]
                ),

            "dieharder_replicates":
                int(
                    d["replicates"]
                ),

            "dieharder_reps_failed":
                int(
                    d["reps_failed"]
                ),

            "dieharder_reps_weak":
                int(
                    d["reps_weak"]
                ),

            "dieharder_reps_passed":
                int(
                    d["reps_passed"]
                ),

            "dieharder_fail_fraction":
                float(
                    d["reps_failed"]
                    / d["replicates"]
                ),

            "raw_material_unique":
                int(
                    raw.loc[
                        source,
                        "material_unique",
                    ]
                ),

            "raw_material_collisions":
                int(
                    raw.loc[
                        source,
                        "material_collisions",
                    ]
                ),

            "conditioned_material_unique":
                int(
                    conditioned.loc[
                        source,
                        "material_unique",
                    ]
                ),

            "conditioned_material_collisions":
                int(
                    conditioned.loc[
                        source,
                        "material_collisions",
                    ]
                ),

            "raw_ascon_key_collisions":
                int(
                    raw.loc[
                        source,
                        "ascon_key_collisions",
                    ]
                ),

            "raw_chacha_key_collisions":
                int(
                    raw.loc[
                        source,
                        "chacha_key_collisions",
                    ]
                ),

            "conditioned_ascon_key_collisions":
                int(
                    conditioned.loc[
                        source,
                        "ascon_key_collisions",
                    ]
                ),

            "conditioned_chacha_key_collisions":
                int(
                    conditioned.loc[
                        source,
                        "chacha_key_collisions",
                    ]
                ),
        }

        rows.append(row)

    result = pd.DataFrame(rows)

    result[
        "targeted_postcollapse_raw_unique"
    ] = pd.NA

    result[
        "targeted_postcollapse_conditioned_unique"
    ] = pd.NA

    result[
        "targeted_postcollapse_ascon_keys_unique"
    ] = pd.NA

    result[
        "targeted_postcollapse_chacha_keys_unique"
    ] = pd.NA

    if COLLAPSE.is_file():
        collapse = pd.read_csv(
            COLLAPSE,
            sep="\t",
        )

        if len(collapse) != 5:
            raise RuntimeError(
                "Expected 5 targeted collapse rows"
            )

        mask = (
            result["source"]
            == "logistic-float64"
        )

        result.loc[
            mask,
            "targeted_postcollapse_raw_unique",
        ] = collapse[
            "input_material_sha256"
        ].nunique()

        result.loc[
            mask,
            "targeted_postcollapse_conditioned_unique",
        ] = collapse[
            "conditioned_material_sha256"
        ].nunique()

        result.loc[
            mask,
            "targeted_postcollapse_ascon_keys_unique",
        ] = collapse[
            "ascon_key_sha256"
        ].nunique()

        result.loc[
            mask,
            "targeted_postcollapse_chacha_keys_unique",
        ] = collapse[
            "chacha_key_sha256"
        ].nunique()

    result.to_csv(
        OUTPUT,
        sep="\t",
        index=False,
    )

    print(
        "PASSED: integrated 10-source table"
    )

    print(
        "Collapse targeted data:",
        "included"
        if COLLAPSE.is_file()
        else "not yet available",
    )

    print()
    print(
        result[
            [
                "source",
                "nist_h_original_mean",
                "dieharder_reps_failed",
                "raw_material_unique",
                "conditioned_material_unique",
                "targeted_postcollapse_raw_unique",
                "targeted_postcollapse_conditioned_unique",
            ]
        ].to_string(
            index=False
        )
    )

    print()
    print("Saved:", OUTPUT)


if __name__ == "__main__":
    main()
