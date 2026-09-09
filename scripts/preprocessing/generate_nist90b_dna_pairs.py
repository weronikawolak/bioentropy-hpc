#!/usr/bin/env python3

import csv
import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "datasets"
    / "manifests"
    / "dna_windows.jsonl"
)

OUTPUT_JSONL = (
    ROOT
    / "datasets"
    / "manifests"
    / "dna_nist90b_pairs.jsonl"
)

OUTPUT_TSV = (
    ROOT
    / "datasets"
    / "manifests"
    / "dna_nist90b_pairs.tsv"
)

PAIRING_SCHEME = (
    "BIOENTROPY-HPC-DNA-NIST90B-PAIRING-v1"
)

EXPERIMENT_RE = re.compile(
    r"^dna-(.+)-w(\d{2})$"
)


def main():
    if not INPUT.is_file():
        raise FileNotFoundError(INPUT)

    windows = []

    with INPUT.open(
        encoding="utf-8",
    ) as handle:
        for line in handle:
            line = line.strip()

            if not line:
                continue

            row = json.loads(line)

            match = EXPERIMENT_RE.fullmatch(
                row["experiment_id"]
            )

            if not match:
                raise RuntimeError(
                    "Unexpected DNA experiment ID: "
                    f"{row['experiment_id']}"
                )

            row["_corpus"] = match.group(1)
            row["_window_index"] = int(
                match.group(2)
            )

            if int(row["output_bits"]) != 800_000:
                raise RuntimeError(
                    f"Expected 800000 bits for "
                    f"{row['experiment_id']}"
                )

            if row["mapping"] != "acgt_2bit":
                raise RuntimeError(
                    f"Unexpected mapping for "
                    f"{row['experiment_id']}: "
                    f"{row['mapping']}"
                )

            windows.append(row)

    grouped = defaultdict(list)

    for row in windows:
        grouped[row["_corpus"]].append(row)

    if len(grouped) != 5:
        raise RuntimeError(
            f"Expected 5 DNA corpora, got "
            f"{len(grouped)}"
        )

    pairs = []

    for corpus in sorted(grouped):
        rows = sorted(
            grouped[corpus],
            key=lambda x: x["_window_index"],
        )

        indices = [
            row["_window_index"]
            for row in rows
        ]

        if indices != list(range(10)):
            raise RuntimeError(
                f"{corpus}: expected windows 0..9, "
                f"got {indices}"
            )

        for pair_index in range(5):
            left = rows[2 * pair_index]
            right = rows[
                2 * pair_index + 1
            ]

            pair = {
                "schema_version": 1,
                "pairing_scheme": PAIRING_SCHEME,
                "pair_id": (
                    f"dna-{corpus}-p"
                    f"{pair_index:02d}"
                ),
                "corpus": corpus,
                "organism": left["organism"],
                "pair_index": pair_index,
                "mapping": "acgt_2bit",
                "member_experiment_ids": [
                    left["experiment_id"],
                    right["experiment_id"],
                ],
                "member_window_indices": [
                    left["_window_index"],
                    right["_window_index"],
                ],
                "member_config_files": [
                    left["config_file"],
                    right["config_file"],
                ],
                "member_sequence_files": [
                    left["sequence_file"],
                    right["sequence_file"],
                ],
                "member_window_sha256": [
                    left["window_sha256"],
                    right["window_sha256"],
                ],
                "member_output_bits": [
                    int(left["output_bits"]),
                    int(right["output_bits"]),
                ],
                "output_bits": 1_600_000,
                "nist_samples": 1_600_000,
            }

            pairs.append(pair)

    if len(pairs) != 25:
        raise RuntimeError(
            f"Expected 25 DNA pairs, got "
            f"{len(pairs)}"
        )

    OUTPUT_JSONL.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_JSONL.open(
        "w",
        encoding="utf-8",
    ) as handle:
        for pair in pairs:
            handle.write(
                json.dumps(
                    pair,
                    sort_keys=True,
                )
                + "\n"
            )

    fields = [
        "pair_id",
        "corpus",
        "organism",
        "pair_index",
        "mapping",
        "member_experiment_ids",
        "member_window_indices",
        "member_config_files",
        "member_window_sha256",
        "output_bits",
        "nist_samples",
        "pairing_scheme",
    ]

    with OUTPUT_TSV.open(
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

        for pair in pairs:
            row = dict(pair)

            for field in (
                "member_experiment_ids",
                "member_window_indices",
                "member_config_files",
                "member_window_sha256",
            ):
                row[field] = ";".join(
                    str(x)
                    for x in row[field]
                )

            writer.writerow(
                {
                    field: row[field]
                    for field in fields
                }
            )

    print(
        "Frozen DNA windows :",
        len(windows),
    )
    print(
        "DNA corpora        :",
        len(grouped),
    )
    print(
        "NIST DNA pairs     :",
        len(pairs),
    )

    for corpus in sorted(grouped):
        count = sum(
            p["corpus"] == corpus
            for p in pairs
        )

        print(
            f"{corpus:<20} pairs={count}"
        )

    print("JSONL:", OUTPUT_JSONL)
    print("TSV  :", OUTPUT_TSV)


if __name__ == "__main__":
    main()
