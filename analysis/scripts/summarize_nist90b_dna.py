#!/usr/bin/env python3

import csv
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "results"
    / "aggregated"
    / "nist90b_dna_pairs.tsv"
)

OUTPUT = (
    ROOT
    / "results"
    / "aggregated"
    / "nist90b_dna_corpus_summary.tsv"
)


def main():
    if not INPUT.is_file():
        raise FileNotFoundError(INPUT)

    with INPUT.open(
        encoding="utf-8",
    ) as handle:
        rows = list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )

    if len(rows) != 25:
        raise RuntimeError(
            f"Expected 25 DNA pairs, got "
            f"{len(rows)}"
        )

    corpora = sorted(
        {
            row["corpus"]
            for row in rows
        }
    )

    if len(corpora) != 5:
        raise RuntimeError(
            f"Expected 5 corpora, got "
            f"{len(corpora)}"
        )

    summary = []

    for corpus in corpora:
        subset = [
            row
            for row in rows
            if row["corpus"]
            == corpus
        ]

        if len(subset) != 5:
            raise RuntimeError(
                f"{corpus}: expected "
                f"5 pairs, got {len(subset)}"
            )

        h = [
            float(row["h_original"])
            for row in subset
        ]

        p1 = [
            float(row["p1"])
            for row in subset
        ]

        provenance_pass = sum(
            row["provenance_ok"].lower()
            == "true"
            for row in subset
        )

        summary.append(
            {
                "corpus": corpus,
                "organism": subset[0][
                    "organism"
                ],
                "pairs": len(subset),
                "samples_per_pair": int(
                    subset[0]["samples"]
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
                "provenance_pass": (
                    provenance_pass
                ),
            }
        )

    fields = [
        "corpus",
        "organism",
        "pairs",
        "samples_per_pair",
        "h_min",
        "h_mean",
        "h_median",
        "h_max",
        "h_stdev",
        "p1_mean",
        "provenance_pass",
    ]

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
        )

        writer.writeheader()
        writer.writerows(summary)

    print(
        "DNA pairs:",
        len(rows),
    )
    print(
        "Corpora   :",
        len(summary),
    )

    for row in summary:
        print(
            f"{row['corpus']:<20} "
            f"n={row['pairs']} "
            f"mean={row['h_mean']:.6f} "
            f"min={row['h_min']:.6f} "
            f"max={row['h_max']:.6f} "
            f"P1={row['p1_mean']:.6f}"
        )

    print()
    print(
        "Summary:",
        OUTPUT,
    )


if __name__ == "__main__":
    main()
