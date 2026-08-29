#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
    )

    args = parser.parse_args()

    df = pd.read_csv(
        args.input,
        sep="\t",
        dtype={
            "replicate_id": str,
        },
    )

    if "valid" not in df.columns:
        raise SystemExit(
            "Input does not contain 'valid' column."
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

    rows = []

    for source, group in df.groupby(
        "source",
        sort=True,
    ):
        valid = group[group["valid"]]

        rows.append({
            "source": source,
            "rows_total": len(group),
            "valid_rows": len(valid),
            "passed": int(
                (
                    valid["assessment"]
                    == "PASSED"
                ).sum()
            ),
            "weak": int(
                (
                    valid["assessment"]
                    == "WEAK"
                ).sum()
            ),
            "failed": int(
                (
                    valid["assessment"]
                    == "FAILED"
                ).sum()
            ),
            "invalid": int(
                (
                    group["assessment"]
                    == "INVALID"
                ).sum()
            ),
        })

    summary = pd.DataFrame(rows)

    print(summary.to_string(index=False))

    interesting = df[
        df["valid"]
        & df["assessment"].isin(
            ["WEAK", "FAILED"]
        )
    ]

    print()
    print("Valid WEAK/FAILED rows")
    print("=" * 90)

    columns = [
        column
        for column in (
            "source",
            "replicate_id",
            "test_number",
            "test_name",
            "ntup",
            "p_value",
            "assessment",
        )
        if column in interesting.columns
    ]

    if interesting.empty:
        print("None")
    else:
        print(
            interesting[
                columns
            ].to_string(index=False)
        )

    output = args.output

    if output is None:
        output = (
            args.input.parent
            / (
                args.input.stem
                + "_summary.tsv"
            )
        )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary.to_csv(
        output,
        sep="\t",
        index=False,
    )

    print()
    print("Saved:", output)


if __name__ == "__main__":
    main()
