#!/usr/bin/env python3

from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

LOGISTIC = (
    ROOT
    / "results/aggregated"
    / "logistic_by_r.tsv"
)

CA_CHACHA = (
    ROOT
    / "results/aggregated"
    / "ca_chacha_screening.tsv"
)

SERIAL = (
    ROOT
    / "results/aggregated"
    / "serial_metrics.tsv"
)

MANIFEST = (
    ROOT
    / "configs/generated/screening"
    / "manifest.tsv"
)

OUTPUT = (
    ROOT
    / "results/aggregated"
    / "source_comparison.tsv"
)


def read_tsv(path: Path):
    if not path.exists():
        raise RuntimeError(
            f"Required file not found: {path}"
        )

    with path.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        return list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )


def as_float(value):
    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    return float(value)


def as_int(value):
    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    return int(float(value))


def quartiles(values):
    values = sorted(values)

    if not values:
        return None, None

    if len(values) == 1:
        return values[0], values[0]

    q = statistics.quantiles(
        values,
        n=4,
        method="inclusive",
    )

    return q[0], q[2]


def median_iqr(values):
    values = [
        value
        for value in values
        if value is not None
    ]

    if not values:
        return None, None, None

    q1, q3 = quartiles(values)

    return (
        statistics.median(values),
        q1,
        q3,
    )


def manifest_metadata():
    rows = read_tsv(MANIFEST)

    metadata = {}

    for row in rows:
        experiment_id = row["experiment_id"]

        output_bits = as_int(
            row["output_bits"]
        )

        if experiment_id not in metadata:
            metadata[experiment_id] = {
                "source":
                    row["source"].strip(),

                "output_bits":
                    output_bits,
            }

        else:
            previous = metadata[
                experiment_id
            ]

            if (
                previous["output_bits"]
                != output_bits
            ):
                raise RuntimeError(
                    "Inconsistent output_bits for "
                    f"{experiment_id}"
                )

    return metadata


def logistic_rows(metadata):
    rows = read_tsv(LOGISTIC)

    output = []

    for row in rows:
        experiment_id = row[
            "experiment_id"
        ]

        r = as_float(row["r"])

        completed = as_int(
            row["completed_replicates"]
        )

        expected = as_int(
            row["expected_replicates"]
        )

        if experiment_id not in metadata:
            raise RuntimeError(
                "Missing manifest metadata for "
                f"{experiment_id}"
            )

        output.append(
            {
                "source_family":
                    "logistic_map",

                "role":
                    "deterministic_candidate",

                "group":
                    "Logistic Map",

                "configuration":
                    f"r={r:.15g}",

                "parameter":
                    "r",

                "parameter_value":
                    r,

                "experiment_id":
                    experiment_id,

                "total_bits_per_run":
                    metadata[
                        experiment_id
                    ]["output_bits"],

                "completed_replicates":
                    completed,

                "expected_replicates":
                    expected,

                "complete":
                    completed == expected,

                "median_bias":
                    as_float(
                        row.get(
                            "median_bias"
                        )
                    ),

                "q1_bias":
                    as_float(
                        row.get("q1_bias")
                    ),

                "q3_bias":
                    as_float(
                        row.get("q3_bias")
                    ),

                "median_shannon_entropy":
                    as_float(
                        row.get(
                            "median_shannon_entropy"
                        )
                    ),

                "q1_shannon_entropy":
                    as_float(
                        row.get(
                            "q1_shannon_entropy"
                        )
                    ),

                "q3_shannon_entropy":
                    as_float(
                        row.get(
                            "q3_shannon_entropy"
                        )
                    ),

                "median_abs_ac1":
                    as_float(
                        row.get(
                            "median_abs_ac1"
                        )
                    ),

                "q1_abs_ac1":
                    as_float(
                        row.get(
                            "q1_abs_ac1"
                        )
                    ),

                "q3_abs_ac1":
                    as_float(
                        row.get(
                            "q3_abs_ac1"
                        )
                    ),

                "median_abs_runs_z":
                    as_float(
                        row.get(
                            "median_abs_runs_z"
                        )
                    ),

                "q1_abs_runs_z":
                    as_float(
                        row.get(
                            "q1_abs_runs_z"
                        )
                    ),

                "q3_abs_runs_z":
                    as_float(
                        row.get(
                            "q3_abs_runs_z"
                        )
                    ),

                "median_longest_run":
                    as_float(
                        row.get(
                            "median_longest_run"
                        )
                    ),

                "q1_longest_run":
                    as_float(
                        row.get(
                            "q1_longest_run"
                        )
                    ),

                "q3_longest_run":
                    as_float(
                        row.get(
                            "q3_longest_run"
                        )
                    ),
            }
        )

    if len(output) != 100:
        raise RuntimeError(
            "Expected 100 Logistic rows, "
            f"found {len(output)}"
        )

    return output


def ca_chacha_rows(metadata):
    rows = read_tsv(CA_CHACHA)

    output = []

    for row in rows:
        experiment_id = row[
            "experiment_id"
        ]

        source = row["source"].strip()

        completed = as_int(
            row["completed_replicates"]
        )

        expected = as_int(
            row["expected_replicates"]
        )

        if experiment_id not in metadata:
            raise RuntimeError(
                "Missing manifest metadata for "
                f"{experiment_id}"
            )

        if source == "cellular_automaton":
            rule = as_int(row["rule"])
            cells = as_int(row["cells"])

            if rule == 90:
                role = "negative_control"
            else:
                role = (
                    "deterministic_candidate"
                )

            source_family = (
                "cellular_automaton"
            )

            group = f"CA Rule {rule}"

            parameter = "cells"

            parameter_value = cells

        elif source == "chacha20_reference":
            role = (
                "cryptographic_reference"
            )

            source_family = (
                "chacha20_reference"
            )

            group = "ChaCha20"

            parameter = ""

            parameter_value = ""

        else:
            raise RuntimeError(
                "Unexpected source in "
                f"{CA_CHACHA}: {source}"
            )

        output.append(
            {
                "source_family":
                    source_family,

                "role":
                    role,

                "group":
                    group,

                "configuration":
                    row[
                        "configuration"
                    ].strip(),

                "parameter":
                    parameter,

                "parameter_value":
                    parameter_value,

                "experiment_id":
                    experiment_id,

                "total_bits_per_run":
                    metadata[
                        experiment_id
                    ]["output_bits"],

                "completed_replicates":
                    completed,

                "expected_replicates":
                    expected,

                "complete":
                    completed == expected,

                "median_bias":
                    as_float(
                        row.get(
                            "median_bias"
                        )
                    ),

                "q1_bias":
                    as_float(
                        row.get("q1_bias")
                    ),

                "q3_bias":
                    as_float(
                        row.get("q3_bias")
                    ),

                "median_shannon_entropy":
                    as_float(
                        row.get(
                            "median_shannon_entropy"
                        )
                    ),

                "q1_shannon_entropy":
                    as_float(
                        row.get(
                            "q1_shannon_entropy"
                        )
                    ),

                "q3_shannon_entropy":
                    as_float(
                        row.get(
                            "q3_shannon_entropy"
                        )
                    ),

                "median_abs_ac1":
                    as_float(
                        row.get(
                            "median_abs_ac1"
                        )
                    ),

                "q1_abs_ac1":
                    as_float(
                        row.get(
                            "q1_abs_ac1"
                        )
                    ),

                "q3_abs_ac1":
                    as_float(
                        row.get(
                            "q3_abs_ac1"
                        )
                    ),

                "median_abs_runs_z":
                    as_float(
                        row.get(
                            "median_abs_runs_z"
                        )
                    ),

                "q1_abs_runs_z":
                    as_float(
                        row.get(
                            "q1_abs_runs_z"
                        )
                    ),

                "q3_abs_runs_z":
                    as_float(
                        row.get(
                            "q3_abs_runs_z"
                        )
                    ),

                "median_longest_run":
                    as_float(
                        row.get(
                            "median_longest_run"
                        )
                    ),

                "q1_longest_run":
                    as_float(
                        row.get(
                            "q1_longest_run"
                        )
                    ),

                "q3_longest_run":
                    as_float(
                        row.get(
                            "q3_longest_run"
                        )
                    ),
            }
        )

    if len(output) != 5:
        raise RuntimeError(
            "Expected 5 CA/ChaCha groups, "
            f"found {len(output)}"
        )

    return output


def dna_rows():
    rows = read_tsv(SERIAL)

    dna = [
        row
        for row in rows
        if (
            row["source"].strip()
            == "dna_sequence"
        )
    ]

    if len(dna) != 50:
        raise RuntimeError(
            "Expected 50 DNA streams, "
            f"found {len(dna)}"
        )

    groups = defaultdict(list)

    for row in dna:
        groups[
            row["group"].strip()
        ].append(row)

    if len(groups) != 5:
        raise RuntimeError(
            "Expected 5 DNA groups, "
            f"found {len(groups)}"
        )

    output = []

    for group in sorted(groups):
        values = groups[group]

        if len(values) != 10:
            raise RuntimeError(
                f"Expected 10 DNA windows for "
                f"{group}, found {len(values)}"
            )

        total_bits = {
            as_int(row["total_bits"])
            for row in values
        }

        if len(total_bits) != 1:
            raise RuntimeError(
                "Inconsistent DNA bit lengths "
                f"for {group}"
            )

        bias = [
            as_float(row["bias"])
            for row in values
        ]

        shannon = [
            as_float(
                row["shannon_entropy"]
            )
            for row in values
        ]

        abs_ac1 = [
            abs(
                as_float(
                    row[
                        "autocorrelation_lag1"
                    ]
                )
            )
            for row in values
        ]

        abs_runs_z = [
            abs(
                as_float(
                    row["runs_z_score"]
                )
            )
            for row in values
        ]

        longest = [
            as_float(
                row["longest_run"]
            )
            for row in values
        ]

        bias_med, bias_q1, bias_q3 = (
            median_iqr(bias)
        )

        sh_med, sh_q1, sh_q3 = (
            median_iqr(shannon)
        )

        ac_med, ac_q1, ac_q3 = (
            median_iqr(abs_ac1)
        )

        runs_med, runs_q1, runs_q3 = (
            median_iqr(abs_runs_z)
        )

        long_med, long_q1, long_q3 = (
            median_iqr(longest)
        )

        output.append(
            {
                "source_family":
                    "dna_sequence",

                "role":
                    "biological_sequence_candidate",

                "group":
                    group,

                "configuration":
                    "10 deterministic windows",

                "parameter":
                    "reference_genome",

                "parameter_value":
                    group,

                "experiment_id":
                    "",

                "total_bits_per_run":
                    next(iter(total_bits)),

                "completed_replicates":
                    len(values),

                "expected_replicates":
                    10,

                "complete":
                    True,

                "median_bias":
                    bias_med,

                "q1_bias":
                    bias_q1,

                "q3_bias":
                    bias_q3,

                "median_shannon_entropy":
                    sh_med,

                "q1_shannon_entropy":
                    sh_q1,

                "q3_shannon_entropy":
                    sh_q3,

                "median_abs_ac1":
                    ac_med,

                "q1_abs_ac1":
                    ac_q1,

                "q3_abs_ac1":
                    ac_q3,

                "median_abs_runs_z":
                    runs_med,

                "q1_abs_runs_z":
                    runs_q1,

                "q3_abs_runs_z":
                    runs_q3,

                "median_longest_run":
                    long_med,

                "q1_longest_run":
                    long_q1,

                "q3_longest_run":
                    long_q3,
            }
        )

    return output


def main():
    metadata = manifest_metadata()

    rows = []

    rows.extend(
        logistic_rows(metadata)
    )

    rows.extend(
        ca_chacha_rows(metadata)
    )

    rows.extend(
        dna_rows()
    )

    if len(rows) != 110:
        raise RuntimeError(
            "Expected 110 comparison rows, "
            f"found {len(rows)}"
        )

    fields = [
        "source_family",
        "role",
        "group",
        "configuration",
        "parameter",
        "parameter_value",
        "experiment_id",
        "total_bits_per_run",
        "completed_replicates",
        "expected_replicates",
        "complete",
        "median_bias",
        "q1_bias",
        "q3_bias",
        "median_shannon_entropy",
        "q1_shannon_entropy",
        "q3_shannon_entropy",
        "median_abs_ac1",
        "q1_abs_ac1",
        "q3_abs_ac1",
        "median_abs_runs_z",
        "q1_abs_runs_z",
        "q3_abs_runs_z",
        "median_longest_run",
        "q1_longest_run",
        "q3_longest_run",
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
            lineterminator="\n",
        )

        writer.writeheader()
        writer.writerows(rows)

    available = [
        row
        for row in rows
        if row["completed_replicates"] > 0
    ]

    complete = [
        row
        for row in rows
        if row["complete"] is True
    ]

    print(
        "Unified source comparison"
    )
    print(
        "-------------------------"
    )

    print(
        f"Total rows       : {len(rows)}"
    )

    print(
        f"With data        : {len(available)}"
    )

    print(
        f"Complete groups  : {len(complete)}"
    )

    print()
    print("Breakdown:")

    counts = defaultdict(int)

    for row in rows:
        counts[
            row["source_family"]
        ] += 1

    for source in sorted(counts):
        print(
            f"  {source:<24} "
            f"{counts[source]}"
        )

    print()
    print(
        "Output:"
    )

    print(
        f"  {OUTPUT.relative_to(ROOT)}"
    )

    print()
    print(
        "DNA medians:"
    )

    for row in rows:
        if (
            row["source_family"]
            != "dna_sequence"
        ):
            continue

        print(
            f"  {row['group']:<42} "
            f"bias={row['median_bias']:.6f}  "
            f"H={row['median_shannon_entropy']:.6f}  "
            f"|AC1|={row['median_abs_ac1']:.6f}  "
            f"|runs z|={row['median_abs_runs_z']:.3f}  "
            f"longest={row['median_longest_run']:.1f}"
        )


if __name__ == "__main__":
    main()
