#!/usr/bin/env python3

from pathlib import Path

import pandas as pd


INPUT = Path(
    "results/aggregated/"
    "dieharder_screening.tsv"
)

OUTPUT = Path(
    "results/aggregated/"
    "dieharder_screening_summary.tsv"
)


def main():
    frame = pd.read_csv(
        INPUT,
        sep="\t",
    )

    assessments = (
        "PASSED",
        "WEAK",
        "FAILED",
        "INVALID",
    )

    rows = []

    for source, group in frame.groupby(
        "source",
        sort=True,
    ):
        row = {
            "source": source,
            "rows_total": len(group),
            "valid_rows": int(
                group["valid"].sum()
            ),
        }

        for assessment in assessments:
            row[
                assessment.lower()
            ] = int(
                (
                    group["assessment"]
                    == assessment
                ).sum()
            )

        valid = group[
            group["assessment"]
            != "INVALID"
        ]

        row["valid_failure_rate"] = (
            (
                valid["assessment"]
                == "FAILED"
            ).mean()
            if len(valid)
            else float("nan")
        )

        rows.append(row)

    summary = pd.DataFrame(rows)

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary.to_csv(
        OUTPUT,
        sep="\t",
        index=False,
    )

    print(
        summary.to_string(
            index=False
        )
    )

    print()
    print("Valid WEAK/FAILED rows")
    print("=" * 90)

    interesting = frame[
        frame["assessment"].isin(
            ["WEAK", "FAILED"]
        )
    ][
        [
            "source",
            "test_number",
            "test_name",
            "ntup",
            "p_value",
            "assessment",
        ]
    ]

    if interesting.empty:
        print("None")
    else:
        print(
            interesting.to_string(
                index=False
            )
        )

    print()
    print(
        "Saved:",
        OUTPUT,
    )


if __name__ == "__main__":
    main()
