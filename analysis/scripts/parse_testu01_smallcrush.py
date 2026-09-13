#!/usr/bin/env python3

from pathlib import Path
import csv
import json
import re


ROOT = Path(__file__).resolve().parents[2]

MANIFEST = (
    ROOT
    / "results/aggregated"
    / "testu01_smallcrush_subset_manifest.tsv"
)

LOG_DIR = (
    ROOT
    / "results/raw/testu01"
)

OUTPUT = (
    ROOT
    / "results/aggregated"
    / "testu01_smallcrush_summary.tsv"
)


def extract_int(
    pattern,
    text,
):
    match = re.search(
        pattern,
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return int(
        match.group(1)
    )


def main():
    with MANIFEST.open(
        encoding="utf-8",
    ) as handle:
        manifest = list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )

    output_rows = []

    for row in manifest:
        label = row["label"]

        log_path = (
            LOG_DIR
            / f"smallcrush_{label}_rep000.log"
        )

        meta_path = (
            LOG_DIR
            / f"smallcrush_{label}_rep000.json"
        )

        if (
            not log_path.is_file()
            or not meta_path.is_file()
        ):
            raise RuntimeError(
                f"{label}: missing result"
            )

        text = log_path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        meta = json.loads(
            meta_path.read_text()
        )

        all_passed = bool(
            re.search(
                r"All tests were passed",
                text,
                flags=re.IGNORECASE,
            )
        )

        outside = bool(
            re.search(
                r"p-values?\s+outside",
                text,
                flags=re.IGNORECASE,
            )
        )

        words = extract_int(
            r"32-bit words consumed\s*:\s*(\d+)",
            text,
        )

        bytes_used = extract_int(
            r"bytes consumed\s*:\s*(\d+)",
            text,
        )

        #
        # Do not reinterpret TestU01's individual tests
        # as statistically independent observations.
        #
        status = (
            "PASSED"
            if all_passed
            else (
                "SUSPECT"
                if outside
                else "REVIEW"
            )
        )

        output_rows.append(
            {
                "source":
                    label,
                "replicate_id":
                    0,
                "battery":
                    "SmallCrush",
                "execution_returncode":
                    meta["returncode"],
                "testu01_status":
                    status,
                "all_tests_passed":
                    int(all_passed),
                "pvalue_outside_notice":
                    int(outside),
                "words_consumed":
                    words
                    if words is not None
                    else "",
                "bytes_consumed":
                    bytes_used
                    if bytes_used is not None
                    else "",
                "config_sha256":
                    row["config_sha256"],
                "log":
                    str(
                        log_path.relative_to(
                            ROOT
                        )
                    ),
            }
        )

    columns = list(
        output_rows[0].keys()
    )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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
        writer.writerows(
            output_rows
        )

    print(
        "source".ljust(28),
        "status".ljust(10),
        "words",
    )

    print(
        "-" * 55
    )

    for row in output_rows:
        print(
            row["source"].ljust(28),
            row[
                "testu01_status"
            ].ljust(10),
            row["words_consumed"],
        )

    print()
    print("Saved:", OUTPUT)


if __name__ == "__main__":
    main()
