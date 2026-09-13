#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

COLLAPSE = {
    1: 5_919_555,
    5: 16_181_612,
    7: 21_156_926,
    8: 10_996_001,
    12: 9_423_224,
}


def read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )


def write_rows(
    path: Path,
    rows: list[dict],
    fields: list[str],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Aggregate windowed NIST SP 800-90B results "
            "for the five frozen collapsed float64 "
            "logistic-map realizations."
        )
    )

    parser.add_argument(
        "--input-dir",
        type=Path,
        default=(
            ROOT
            / "results"
            / "aggregated"
        ),
    )

    parser.add_argument(
        "--combined",
        type=Path,
        default=(
            ROOT
            / "results"
            / "aggregated"
            / "nist90b_logistic-float64_"
            "collapsed_windows.tsv"
        ),
    )

    parser.add_argument(
        "--summary",
        type=Path,
        default=(
            ROOT
            / "results"
            / "aggregated"
            / "nist90b_logistic-float64_"
            "collapse_summary.tsv"
        ),
    )

    args = parser.parse_args()

    combined = []
    summary = []

    for replicate, collapse_index in COLLAPSE.items():
        path = args.input_dir / (
            "nist90b_logistic-float64_"
            f"rep{replicate:03d}_windows.tsv"
        )

        if not path.is_file():
            raise FileNotFoundError(
                f"Missing window results: {path}"
            )

        rows = read_rows(path)

        if not rows:
            raise RuntimeError(
                f"No rows in {path}"
            )

        processed = []

        for row in rows:
            start = int(
                row["window_start"]
            )
            end = int(
                row["window_end_exclusive"]
            )

            midpoint = (
                start + end
            ) / 2.0

            if (
                start
                <= collapse_index
                < end
            ):
                phase = "collapse"
            elif end <= collapse_index:
                phase = "pre"
            else:
                phase = "post"

            row["collapse_index"] = (
                collapse_index
            )

            row["phase"] = phase

            row[
                "relative_midpoint_bits"
            ] = (
                midpoint
                - collapse_index
            )

            row[
                "relative_midpoint_mbit"
            ] = (
                midpoint
                - collapse_index
            ) / 1_000_000.0

            processed.append(row)
            combined.append(row)

        collapse_rows = [
            row
            for row in processed
            if row["phase"] == "collapse"
        ]

        if len(collapse_rows) != 1:
            raise RuntimeError(
                f"Expected exactly one collapse "
                f"window for rep{replicate:03d}; "
                f"got {len(collapse_rows)}."
            )

        pre_rows = [
            row
            for row in processed
            if row["phase"] == "pre"
        ]

        post_rows = [
            row
            for row in processed
            if row["phase"] == "post"
        ]

        if not pre_rows:
            raise RuntimeError(
                f"No pre-collapse window for "
                f"rep{replicate:03d}."
            )

        last_pre = max(
            pre_rows,
            key=lambda row: int(
                row[
                    "window_end_exclusive"
                ]
            ),
        )

        first_post = (
            min(
                post_rows,
                key=lambda row: int(
                    row["window_start"]
                ),
            )
            if post_rows
            else None
        )

        collapse_row = (
            collapse_rows[0]
        )

        pre_h = float(
            last_pre["h_original"]
        )

        collapse_h = float(
            collapse_row["h_original"]
        )

        summary.append(
            {
                "replicate_id": (
                    f"{replicate:03d}"
                ),
                "collapse_index": (
                    collapse_index
                ),
                "last_pre_start": int(
                    last_pre[
                        "window_start"
                    ]
                ),
                "last_pre_end": int(
                    last_pre[
                        "window_end_exclusive"
                    ]
                ),
                "last_pre_h_original": (
                    pre_h
                ),
                "collapse_start": int(
                    collapse_row[
                        "window_start"
                    ]
                ),
                "collapse_end": int(
                    collapse_row[
                        "window_end_exclusive"
                    ]
                ),
                "collapse_p1": float(
                    collapse_row["p1"]
                ),
                "collapse_h_original": (
                    collapse_h
                ),
                "absolute_h_drop": (
                    pre_h - collapse_h
                ),
                "first_post_h_original": (
                    float(
                        first_post[
                            "h_original"
                        ]
                    )
                    if first_post
                    else ""
                ),
                "first_post_status": (
                    first_post[
                        "assessment_status"
                    ]
                    if first_post
                    else ""
                ),
                "provenance_ok": all(
                    row[
                        "provenance_ok"
                    ].lower()
                    == "true"
                    for row in processed
                ),
            }
        )

    combined.sort(
        key=lambda row: (
            int(row["replicate_id"]),
            int(row["window_start"]),
        )
    )

    combined_fields = [
        "source",
        "replicate_id",
        "collapse_index",
        "phase",
        "window_start",
        "window_end_exclusive",
        "relative_midpoint_bits",
        "relative_midpoint_mbit",
        "window_samples",
        "p1",
        "h_original",
        "assessment_status",
        "h_original_origin",
        "nist_exit_code",
        "provenance_ok",
        "raw_input_sha256",
        "nist_input_sha256",
    ]

    summary_fields = [
        "replicate_id",
        "collapse_index",
        "last_pre_start",
        "last_pre_end",
        "last_pre_h_original",
        "collapse_start",
        "collapse_end",
        "collapse_p1",
        "collapse_h_original",
        "absolute_h_drop",
        "first_post_h_original",
        "first_post_status",
        "provenance_ok",
    ]

    write_rows(
        args.combined,
        combined,
        combined_fields,
    )

    write_rows(
        args.summary,
        summary,
        summary_fields,
    )

    mean_pre = sum(
        float(row["last_pre_h_original"])
        for row in summary
    ) / len(summary)

    mean_collapse = sum(
        float(row["collapse_h_original"])
        for row in summary
    ) / len(summary)

    mean_drop = sum(
        float(row["absolute_h_drop"])
        for row in summary
    ) / len(summary)

    print(
        "Collapsed realizations :",
        len(summary),
    )
    print(
        "Combined windows       :",
        len(combined),
    )
    print(
        "Mean last-pre H        :",
        f"{mean_pre:.8f}",
    )
    print(
        "Mean collapse-window H :",
        f"{mean_collapse:.8f}",
    )
    print(
        "Mean absolute H drop   :",
        f"{mean_drop:.8f}",
    )
    print(
        "Combined TSV           :",
        args.combined,
    )
    print(
        "Summary TSV            :",
        args.summary,
    )


if __name__ == "__main__":
    main()
