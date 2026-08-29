#!/usr/bin/env python3

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path


RESULT_RE = re.compile(
    r"^\s*([^#|][^|]*)\|"
    r"\s*([^|]+)\|"
    r"\s*([^|]+)\|"
    r"\s*([^|]+)\|"
    r"\s*([^|]+)\|"
    r"\s*([^|]+)\s*$"
)

REWIND_RE = re.compile(
    r"rewound\s+(\d+)\s+times",
    re.IGNORECASE,
)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
    )

    return parser.parse_args()


def parse_float(value):
    try:
        return float(value)
    except ValueError:
        return float("nan")


def parse_file(path):
    text = path.read_text(
        errors="replace"
    )

    rewind_match = REWIND_RE.search(text)

    rewinds = (
        int(rewind_match.group(1))
        if rewind_match
        else 0
    )

    stem = path.stem

    source = stem
    test_number = ""

    match = re.match(
        r"(.+)-d(\d+)$",
        stem,
    )

    if match:
        source = match.group(1)
        test_number = match.group(2)

    rows = []

    for line in text.splitlines():
        match = RESULT_RE.match(line)

        if not match:
            continue

        fields = [
            value.strip()
            for value in match.groups()
        ]

        test_name = fields[0]

        if test_name in {
            "test_name",
            "rng_name",
        }:
            continue

        p_value = parse_float(
            fields[4]
        )

        assessment = (
            fields[5]
            .strip()
            .upper()
        )

        finite_p = math.isfinite(
            p_value
        )

        valid = (
            rewinds == 0
            and finite_p
        )

        effective = (
            assessment
            if valid
            else "INVALID"
        )

        invalid_reason = ""

        if rewinds > 0:
            invalid_reason = (
                f"input_rewound_{rewinds}_times"
            )

        if not finite_p:
            if invalid_reason:
                invalid_reason += ";"

            invalid_reason += (
                "non_finite_p_value"
            )

        rows.append(
            {
                "source": source,
                "test_number": test_number,
                "test_name": test_name,
                "ntup": fields[1],
                "tsamples": fields[2],
                "psamples": fields[3],
                "p_value": fields[4],
                "dieharder_assessment":
                    assessment,
                "rewinds": rewinds,
                "valid": valid,
                "assessment": effective,
                "invalid_reason":
                    invalid_reason,
                "file": str(path),
            }
        )

    return rows


def main():
    args = parse_args()

    rows = []

    for path in sorted(
        args.input_dir.glob("*.txt")
    ):
        rows.extend(
            parse_file(path)
        )

    if not rows:
        raise SystemExit(
            "No Dieharder result rows found."
        )

    columns = [
        "source",
        "test_number",
        "test_name",
        "ntup",
        "tsamples",
        "psamples",
        "p_value",
        "dieharder_assessment",
        "rewinds",
        "valid",
        "assessment",
        "invalid_reason",
        "file",
    ]

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with args.output.open("w") as handle:
        handle.write(
            "\t".join(columns)
            + "\n"
        )

        for row in rows:
            handle.write(
                "\t".join(
                    str(row[column])
                    for column in columns
                )
                + "\n"
            )

    print(
        f"{'source':<20}"
        f"{'test':<18}"
        f"{'p-value':>12}"
        f"{'raw':>10}"
        f"{'rew':>6}"
        f"{'final':>10}"
    )

    print("-" * 76)

    for row in rows:
        print(
            f"{row['source']:<20}"
            f"{row['test_name']:<18}"
            f"{row['p_value']:>12}"
            f"{row['dieharder_assessment']:>10}"
            f"{row['rewinds']:>6}"
            f"{row['assessment']:>10}"
        )

    print()
    print(
        "Saved:",
        args.output,
    )


if __name__ == "__main__":
    main()
