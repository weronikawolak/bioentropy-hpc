#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

RESULT_ROOT = ROOT / "results/metrics"

DNA_MANIFEST = (
    ROOT / "datasets/manifests/dna_windows.tsv"
)

OUTPUT = (
    ROOT /
    "results/aggregated/"
    "serial_metrics.tsv"
)


def load_dna_organisms():
    mapping = {}

    with DNA_MANIFEST.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        rows = csv.DictReader(
            handle,
            delimiter="\t",
        )

        for row in rows:
            mapping[
                row["experiment_id"]
            ] = row["organism"]

    return mapping


def median(values):
    return statistics.median(values)


def main():
    dna_organisms = load_dna_organisms()

    rows = []

    for path in sorted(
        RESULT_ROOT.glob("*.json")
    ):
        with path.open(
            encoding="utf-8",
        ) as handle:
            data = json.load(handle)

        statistics_data = (
            data["statistics"]
        )

        if (
            "autocorrelation_lag1"
            not in statistics_data
        ):
            continue

        experiment_id = (
            data["experiment"]["id"]
        )

        source = data["source"]["name"]

        if source == "dna_sequence":
            group = dna_organisms.get(
                experiment_id,
                "DNA"
            )

        elif source == "cellular_automaton":
            rule = (
                data["source"]
                ["parameters"]
                ["rule"]
            )

            group = f"CA Rule {rule}"

        elif source == "logistic":
            group = "Logistic"

        elif source == "chacha20_reference":
            group = "ChaCha20"

        else:
            group = source

        rows.append(
            {
                "experiment_id":
                    experiment_id,

                "source":
                    source,

                "group":
                    group,

                "total_bits":
                    statistics_data[
                        "total_bits"
                    ],

                "bias":
                    statistics_data[
                        "bias"
                    ],

                "shannon_entropy":
                    statistics_data[
                        "shannon_entropy"
                    ],

                "autocorrelation_lag1":
                    statistics_data[
                        "autocorrelation_lag1"
                    ],

                "runs":
                    statistics_data[
                        "runs"
                    ],

                "expected_runs":
                    statistics_data[
                        "expected_runs"
                    ],

                "runs_z_score":
                    statistics_data[
                        "runs_z_score"
                    ],

                "longest_run":
                    statistics_data[
                        "longest_run"
                    ],
            }
        )

    if not rows:
        raise RuntimeError(
            "No results containing serial metrics"
        )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fields = list(
        rows[0].keys()
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
        writer.writerows(rows)

    groups = defaultdict(list)

    for row in rows:
        groups[row["group"]].append(row)

    print(
        f"{'Group':45s}"
        f"{'N':>5s}"
        f"{'med bias':>12s}"
        f"{'med AC1':>12s}"
        f"{'med |runs z|':>15s}"
        f"{'med longest':>14s}"
    )

    print("-" * 103)

    for group, values in sorted(
        groups.items()
    ):
        biases = [
            float(v["bias"])
            for v in values
        ]

        autocorrelations = [
            float(
                v["autocorrelation_lag1"]
            )
            for v in values
            if v["autocorrelation_lag1"]
            is not None
        ]

        run_z = [
            abs(
                float(v["runs_z_score"])
            )
            for v in values
            if v["runs_z_score"]
            is not None
        ]

        longest = [
            int(v["longest_run"])
            for v in values
        ]

        ac_value = (
            median(autocorrelations)
            if autocorrelations
            else float("nan")
        )

        run_value = (
            median(run_z)
            if run_z
            else float("nan")
        )

        print(
            f"{group:45s}"
            f"{len(values):5d}"
            f"{median(biases):12.6f}"
            f"{ac_value:12.6f}"
            f"{run_value:15.3f}"
            f"{median(longest):14.1f}"
        )

    print()
    print(
        "Rows:",
        len(rows)
    )

    print(
        "Output:",
        OUTPUT.relative_to(ROOT)
    )


if __name__ == "__main__":
    main()
