#!/usr/bin/env python3

import argparse
from pathlib import Path

import pandas as pd


def family_outcome(group):
    valid = group[group["valid"]]
    values = set(valid["assessment"])

    if "FAILED" in values:
        return "FAILED"
    if "WEAK" in values:
        return "WEAK"
    if "PASSED" in values:
        return "PASSED"

    return "INVALID"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--output-prefix",
        type=Path,
        required=True,
    )
    args = parser.parse_args()

    df = pd.read_csv(
        args.input,
        sep="\t",
        dtype={"replicate_id": str},
    )

    if df["valid"].dtype != bool:
        df["valid"] = (
            df["valid"]
            .astype(str)
            .str.lower()
            .map({
                "true": True,
                "false": False,
            })
        )

    keys = [
        "source",
        "replicate_id",
        "test_number",
        "test_name",
    ]

    family_rows = []

    for key, group in df.groupby(
        keys,
        sort=True,
    ):
        family_rows.append({
            **dict(zip(keys, key)),
            "outcome": family_outcome(group),
            "raw_rows": len(group),
            "valid_rows": int(
                group["valid"].sum()
            ),
            "invalid_rows": int(
                (~group["valid"]).sum()
            ),
        })

    family = pd.DataFrame(
        family_rows
    )

    family.to_csv(
        str(args.output_prefix)
        + "_family.tsv",
        sep="\t",
        index=False,
    )

    replicate_rows = []

    for key, group in family.groupby(
        ["source", "replicate_id"],
        sort=True,
    ):
        outcomes = set(group["outcome"])

        if "FAILED" in outcomes:
            overall = "FAILED"
        elif "WEAK" in outcomes:
            overall = "WEAK"
        elif "PASSED" in outcomes:
            overall = "PASSED"
        else:
            overall = "INVALID"

        replicate_rows.append({
            "source": key[0],
            "replicate_id": key[1],
            "outcome": overall,
            "failed_families": int(
                (
                    group["outcome"]
                    == "FAILED"
                ).sum()
            ),
            "weak_families": int(
                (
                    group["outcome"]
                    == "WEAK"
                ).sum()
            ),
            "invalid_families": int(
                (
                    group["outcome"]
                    == "INVALID"
                ).sum()
            ),
        })

    replicates = pd.DataFrame(
        replicate_rows
    )

    replicates.to_csv(
        str(args.output_prefix)
        + "_replicates.tsv",
        sep="\t",
        index=False,
    )

    summary = (
        replicates
        .groupby("source")
        .agg(
            replicates=(
                "replicate_id",
                "nunique",
            ),
            reps_failed=(
                "outcome",
                lambda x:
                int((x == "FAILED").sum()),
            ),
            reps_weak=(
                "outcome",
                lambda x:
                int((x == "WEAK").sum()),
            ),
            reps_passed=(
                "outcome",
                lambda x:
                int((x == "PASSED").sum()),
            ),
            reps_invalid=(
                "outcome",
                lambda x:
                int((x == "INVALID").sum()),
            ),
        )
        .reset_index()
    )

    summary.to_csv(
        str(args.output_prefix)
        + "_sources.tsv",
        sep="\t",
        index=False,
    )

    recurrence = (
        family
        .groupby(
            [
                "source",
                "test_number",
                "test_name",
            ]
        )
        .agg(
            replicates=(
                "replicate_id",
                "nunique",
            ),
            fail_reps=(
                "outcome",
                lambda x:
                int((x == "FAILED").sum()),
            ),
            weak_reps=(
                "outcome",
                lambda x:
                int((x == "WEAK").sum()),
            ),
            pass_reps=(
                "outcome",
                lambda x:
                int((x == "PASSED").sum()),
            ),
            invalid_reps=(
                "outcome",
                lambda x:
                int((x == "INVALID").sum()),
            ),
        )
        .reset_index()
    )

    recurrence.to_csv(
        str(args.output_prefix)
        + "_recurrence.tsv",
        sep="\t",
        index=False,
    )

    print()
    print("SOURCE-LEVEL REPLICATE SUMMARY")
    print("=" * 80)
    print(
        summary.to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()
