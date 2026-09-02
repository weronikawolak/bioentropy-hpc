#!/usr/bin/env python3

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


KEYS = [
    "source",
    "replicate_id",
]


FAMILY_KEYS = [
    "source",
    "replicate_id",
    "test_number",
    "test_name",
]


OUTCOMES = [
    "FAILED",
    "WEAK",
    "PASSED",
    "INVALID",
]


def load(path, keys):
    with Path(path).open() as f:
        rows = list(csv.DictReader(f, delimiter="\t"))

    return {
        tuple(row[k] for k in keys): row
        for row in rows
    }


def write_tsv(path, header, rows):
    with Path(path).open("w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(header)
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--raw-replicates", required=True)
    parser.add_argument("--ascon-replicates", required=True)

    parser.add_argument("--raw-family", required=True)
    parser.add_argument("--ascon-family", required=True)

    parser.add_argument("--output-prefix", required=True)

    args = parser.parse_args()

    raw_rep = load(args.raw_replicates, KEYS)
    asc_rep = load(args.ascon_replicates, KEYS)

    raw_family = load(args.raw_family, FAMILY_KEYS)
    asc_family = load(args.ascon_family, FAMILY_KEYS)

    if set(raw_rep) != set(asc_rep):
        raise SystemExit(
            "RAW and Ascon replicate keys do not match"
        )

    if set(raw_family) != set(asc_family):
        raise SystemExit(
            "RAW and Ascon family keys do not match"
        )

    prefix = Path(args.output_prefix)

    rep_transitions = Counter()
    family_transitions = Counter()
    source_counts = defaultdict(
        lambda: {
            "raw": Counter(),
            "ascon": Counter(),
        }
    )

    rep_pairs = []

    for key in sorted(raw_rep):
        source, replicate = key

        raw = raw_rep[key]["outcome"]
        asc = asc_rep[key]["outcome"]

        rep_transitions[(raw, asc)] += 1

        source_counts[source]["raw"][raw] += 1
        source_counts[source]["ascon"][asc] += 1

        rep_pairs.append(
            [source, replicate, raw, asc]
        )

    family_pairs = []

    for key in sorted(raw_family):
        raw = raw_family[key]["outcome"]
        asc = asc_family[key]["outcome"]

        family_transitions[(raw, asc)] += 1

        family_pairs.append(
            list(key) + [raw, asc]
        )

    write_tsv(
        f"{prefix}_replicate_pairs.tsv",
        [
            "source",
            "replicate_id",
            "raw_outcome",
            "ascon_outcome",
        ],
        rep_pairs,
    )

    write_tsv(
        f"{prefix}_family_pairs.tsv",
        FAMILY_KEYS
        + ["raw_outcome", "ascon_outcome"],
        family_pairs,
    )

    write_tsv(
        f"{prefix}_replicate_transitions.tsv",
        [
            "raw_outcome",
            "ascon_outcome",
            "count",
        ],
        [
            [raw, asc, count]
            for (raw, asc), count
            in sorted(rep_transitions.items())
        ],
    )

    write_tsv(
        f"{prefix}_family_transitions.tsv",
        [
            "raw_outcome",
            "ascon_outcome",
            "count",
        ],
        [
            [raw, asc, count]
            for (raw, asc), count
            in sorted(family_transitions.items())
        ],
    )

    source_rows = []

    for source in sorted(source_counts):
        row = [source]

        for mode in ["raw", "ascon"]:
            for outcome in OUTCOMES:
                row.append(
                    source_counts[source][mode][outcome]
                )

        source_rows.append(row)

    write_tsv(
        f"{prefix}_source_summary.tsv",
        [
            "source",
            "raw_failed",
            "raw_weak",
            "raw_passed",
            "raw_invalid",
            "ascon_failed",
            "ascon_weak",
            "ascon_passed",
            "ascon_invalid",
        ],
        source_rows,
    )

    print("Replicate pairs:", len(rep_pairs))
    print("Family pairs   :", len(family_pairs))

    print("\nREPLICATE TRANSITIONS")

    for pair, count in sorted(
        rep_transitions.items()
    ):
        print(
            f"{pair[0]:>7} -> "
            f"{pair[1]:<7}: {count}"
        )

    print("\nFAMILY TRANSITIONS")

    for pair, count in sorted(
        family_transitions.items()
    ):
        print(
            f"{pair[0]:>7} -> "
            f"{pair[1]:<7}: {count}"
        )


if __name__ == "__main__":
    main()
