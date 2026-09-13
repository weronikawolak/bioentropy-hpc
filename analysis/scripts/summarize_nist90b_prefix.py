#!/usr/bin/env python3

import csv
import json
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

INPUT_ROOT = (
    ROOT
    / "results"
    / "external"
    / "nist90b-prefix1m"
)

OUT_ALL = (
    ROOT
    / "results"
    / "aggregated"
    / "nist90b_prefix1m_all_sources.tsv"
)

OUT_SUMMARY = (
    ROOT
    / "results"
    / "aggregated"
    / "nist90b_prefix1m_source_summary.tsv"
)


EXPECTED_SOURCES = [
    "logistic-float32",
    "logistic-float64",
    "logistic-fixed_q3_29",
    "logistic-mpfr_256",
    "chen-4d-dcs",
    "rule30-cells256",
    "rule30-cells1024",
    "rule90-cells256",
    "rule90-cells1024",
    "chacha20",
]


def load_results():
    rows = []

    for path in sorted(
        INPUT_ROOT.glob(
            "*/rep*/result.json"
        )
    ):
        with path.open(
            encoding="utf-8",
        ) as handle:
            row = json.load(handle)

        row.setdefault(
            "assessment_status",
            "nist_estimated",
        )

        row["result_file"] = str(
            path.relative_to(ROOT)
        )

        rows.append(row)

    return rows


def write_tsv(
    path,
    rows,
    fields,
):
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


def main():
    rows = load_results()

    if not rows:
        raise RuntimeError(
            "No NIST 90B prefix results found."
        )

    rows.sort(
        key=lambda r: (
            r["source"],
            int(r["replicate_id"]),
        )
    )

    all_fields = [
        "source",
        "replicate_id",
        "samples",
        "p1",
        "h_original",
        "assessment_status",
        "provenance_ok",
        "raw_input_sha256",
        "nist_input_sha256",
        "result_file",
    ]

    write_tsv(
        OUT_ALL,
        rows,
        all_fields,
    )

    summary = []

    for source in EXPECTED_SOURCES:
        source_rows = [
            r
            for r in rows
            if r["source"] == source
        ]

        if not source_rows:
            continue

        h = [
            float(r["h_original"])
            for r in source_rows
        ]

        p1 = [
            float(r["p1"])
            for r in source_rows
        ]

        provenance_pass = sum(
            bool(r.get("provenance_ok"))
            for r in source_rows
        )

        summary.append(
            {
                "source": source,
                "replicates": len(
                    source_rows
                ),
                "h_min": min(h),
                "h_mean": statistics.mean(h),
                "h_median": statistics.median(h),
                "h_max": max(h),
                "h_stdev": (
                    statistics.stdev(h)
                    if len(h) > 1
                    else 0.0
                ),
                "p1_mean": statistics.mean(p1),
                "provenance_pass": provenance_pass,
            }
        )

    fields = [
        "source",
        "replicates",
        "h_min",
        "h_mean",
        "h_median",
        "h_max",
        "h_stdev",
        "p1_mean",
        "provenance_pass",
    ]

    write_tsv(
        OUT_SUMMARY,
        summary,
        fields,
    )

    print(
        "Total realizations :",
        len(rows),
    )

    print(
        "Sources            :",
        len(summary),
    )

    for row in summary:
        print(
            f"{row['source']:<24} "
            f"n={row['replicates']:>2} "
            f"mean={row['h_mean']:.6f} "
            f"min={row['h_min']:.6f} "
            f"max={row['h_max']:.6f}"
        )

    print()
    print(
        "All results :",
        OUT_ALL,
    )
    print(
        "Summary     :",
        OUT_SUMMARY,
    )


if __name__ == "__main__":
    main()
