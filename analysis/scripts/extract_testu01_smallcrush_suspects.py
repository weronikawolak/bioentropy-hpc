#!/usr/bin/env python3

from pathlib import Path
import csv
import re

ROOT = Path(__file__).resolve().parents[2]

SUMMARY = (
    ROOT
    / "results/aggregated"
    / "testu01_smallcrush_summary.tsv"
)

OUTPUT = (
    ROOT
    / "results/aggregated"
    / "testu01_smallcrush_suspect_tests.tsv"
)


def extract_suspect_lines(text):
    marker = re.search(
        r"The following tests gave p-values "
        r"outside\s*\[[^\]]+\]:",
        text,
        flags=re.IGNORECASE,
    )

    if marker is None:
        return []

    tail = text[marker.end():]

    stop = re.search(
        r"(All other tests were passed|"
        r"All tests were passed|"
        r"BioEntropy adapter summary)",
        tail,
        flags=re.IGNORECASE,
    )

    if stop is not None:
        tail = tail[:stop.start()]

    rows = []

    for line in tail.splitlines():
        stripped = line.strip()

        if not re.match(
            r"^\d+\s+",
            stripped,
        ):
            continue

        parts = re.split(
            r"\s{2,}",
            stripped,
        )

        if len(parts) < 2:
            continue

        test_number = int(
            re.match(
                r"^\d+",
                parts[0],
            ).group()
        )

        if len(parts) >= 3:
            test_name = " | ".join(
                parts[1:-1]
            )
            pvalue = parts[-1]
        else:
            test_name = parts[1]
            pvalue = ""

        rows.append(
            {
                "test_number":
                    test_number,
                "test_name":
                    test_name,
                "pvalue_text":
                    pvalue,
                "raw_line":
                    stripped,
            }
        )

    return rows


def main():
    with SUMMARY.open(
        encoding="utf-8",
    ) as handle:
        summary = list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )

    output = []

    for row in summary:
        source = row["source"]

        log_path = (
            ROOT
            / row["log"]
        )

        text = log_path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        suspects = extract_suspect_lines(
            text
        )

        if (
            row["testu01_status"]
            == "PASSED"
            and suspects
        ):
            raise RuntimeError(
                f"{source}: PASSED but "
                f"suspect rows found"
            )

        if (
            row["testu01_status"]
            == "SUSPECT"
            and not suspects
        ):
            raise RuntimeError(
                f"{source}: SUSPECT but no "
                f"suspect test rows parsed"
            )

        for item in suspects:
            output.append(
                {
                    "source":
                        source,
                    "replicate_id":
                        row["replicate_id"],
                    "battery":
                        "SmallCrush",
                    **item,
                }
            )

        print(
            f"{source:28s} "
            f"suspects={len(suspects)}"
        )

    columns = [
        "source",
        "replicate_id",
        "battery",
        "test_number",
        "test_name",
        "pvalue_text",
        "raw_line",
    ]

    with OUTPUT.open(
        "w",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=columns,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(output)

    print()
    print(
        "Total suspect statistics:",
        len(output),
    )
    print("Saved:", OUTPUT)


if __name__ == "__main__":
    main()
