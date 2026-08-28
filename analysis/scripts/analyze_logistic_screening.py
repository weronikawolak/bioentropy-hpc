#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

MANIFEST = (
    ROOT /
    "configs/generated/screening/"
    "manifest.tsv"
)

RESULT_ROOT = (
    ROOT /
    "results/metrics"
)

SUMMARY_PATH = (
    ROOT /
    "results/aggregated/"
    "logistic_by_r.tsv"
)

CANDIDATES_PATH = (
    ROOT /
    "results/aggregated/"
    "logistic_candidates.tsv"
)

EXPECTED_REPLICATES = 20


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


def result_path(
    experiment_id: str,
    replicate_id: int,
) -> Path:
    return (
        RESULT_ROOT /
        f"{experiment_id}_"
        f"rep{replicate_id:04d}.json"
    )


def main():
    if not MANIFEST.exists():
        raise RuntimeError(
            f"Manifest not found: {MANIFEST}"
        )

    with MANIFEST.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        manifest_rows = [
            row
            for row in csv.DictReader(
                handle,
                delimiter="\t",
            )
            if row["source"] == "logistic"
        ]

    if len(manifest_rows) != 2000:
        raise RuntimeError(
            "Expected 2000 Logistic manifest rows, "
            f"found {len(manifest_rows)}"
        )

    groups = defaultdict(list)
    missing = []

    for row in manifest_rows:
        experiment_id = row["experiment_id"]
        replicate_id = int(
            row["replicate_id"]
        )

        path = result_path(
            experiment_id,
            replicate_id,
        )

        if not path.exists():
            missing.append(
                (
                    experiment_id,
                    replicate_id,
                )
            )
            continue

        with path.open(
            encoding="utf-8",
        ) as handle:
            data = json.load(handle)

        if (
            data["experiment"]["id"]
            != experiment_id
        ):
            raise RuntimeError(
                f"Experiment ID mismatch in {path}"
            )

        if (
            data["experiment"]["replicate_id"]
            != replicate_id
        ):
            raise RuntimeError(
                f"Replicate mismatch in {path}"
            )

        if data["source"]["name"] != "logistic":
            raise RuntimeError(
                f"Unexpected source in {path}"
            )

        stats = data["statistics"]

        required = [
            "bias",
            "shannon_entropy",
            "autocorrelation_lag1",
            "runs_z_score",
            "longest_run",
        ]

        for field in required:
            if field not in stats:
                raise RuntimeError(
                    f"Missing {field} in {path}"
                )

        if (
            stats["autocorrelation_lag1"]
            is None
        ):
            raise RuntimeError(
                f"Undefined autocorrelation in {path}"
            )

        if stats["runs_z_score"] is None:
            raise RuntimeError(
                f"Undefined runs z-score in {path}"
            )

        manifest_r = float(row["r"])

        result_r = float(
            data["source"]
            ["parameters"]["r"]
        )

        if abs(
            manifest_r - result_r
        ) > 1e-12:
            raise RuntimeError(
                f"r mismatch in {path}"
            )

        groups[experiment_id].append(
            {
                "experiment_id":
                    experiment_id,

                "replicate_id":
                    replicate_id,

                "r":
                    manifest_r,

                "bias":
                    float(
                        stats["bias"]
                    ),

                "shannon_entropy":
                    float(
                        stats["shannon_entropy"]
                    ),

                "autocorrelation_lag1":
                    float(
                        stats[
                            "autocorrelation_lag1"
                        ]
                    ),

                "runs_z_score":
                    float(
                        stats["runs_z_score"]
                    ),

                "longest_run":
                    int(
                        stats["longest_run"]
                    ),
            }
        )

    summary = []

    expected_groups = sorted({
        row["experiment_id"]
        for row in manifest_rows
    })

    for experiment_id in expected_groups:
        values = groups.get(
            experiment_id,
            []
        )

        manifest_group = [
            row
            for row in manifest_rows
            if (
                row["experiment_id"]
                == experiment_id
            )
        ]

        r = float(
            manifest_group[0]["r"]
        )

        if not values:
            summary.append(
                {
                    "experiment_id":
                        experiment_id,

                    "r":
                        r,

                    "completed_replicates":
                        0,

                    "expected_replicates":
                        EXPECTED_REPLICATES,

                    "complete":
                        False,
                }
            )
            continue

        biases = [
            item["bias"]
            for item in values
        ]

        shannon = [
            item["shannon_entropy"]
            for item in values
        ]

        ac1 = [
            item["autocorrelation_lag1"]
            for item in values
        ]

        abs_ac1 = [
            abs(value)
            for value in ac1
        ]

        runs_z = [
            item["runs_z_score"]
            for item in values
        ]

        abs_runs_z = [
            abs(value)
            for value in runs_z
        ]

        longest = [
            item["longest_run"]
            for item in values
        ]

        bias_q1, bias_q3 = quartiles(
            biases
        )

        shannon_q1, shannon_q3 = quartiles(
            shannon
        )

        abs_ac1_q1, abs_ac1_q3 = quartiles(
            abs_ac1
        )

        abs_runs_q1, abs_runs_q3 = quartiles(
            abs_runs_z
        )

        longest_q1, longest_q3 = quartiles(
            longest
        )

        summary.append(
            {
                "experiment_id":
                    experiment_id,

                "r":
                    r,

                "completed_replicates":
                    len(values),

                "expected_replicates":
                    EXPECTED_REPLICATES,

                "complete":
                    (
                        len(values)
                        == EXPECTED_REPLICATES
                    ),

                "median_bias":
                    statistics.median(
                        biases
                    ),

                "q1_bias":
                    bias_q1,

                "q3_bias":
                    bias_q3,

                "median_shannon_entropy":
                    statistics.median(
                        shannon
                    ),

                "q1_shannon_entropy":
                    shannon_q1,

                "q3_shannon_entropy":
                    shannon_q3,

                "median_ac1":
                    statistics.median(
                        ac1
                    ),

                "median_abs_ac1":
                    statistics.median(
                        abs_ac1
                    ),

                "q1_abs_ac1":
                    abs_ac1_q1,

                "q3_abs_ac1":
                    abs_ac1_q3,

                "median_runs_z":
                    statistics.median(
                        runs_z
                    ),

                "median_abs_runs_z":
                    statistics.median(
                        abs_runs_z
                    ),

                "q1_abs_runs_z":
                    abs_runs_q1,

                "q3_abs_runs_z":
                    abs_runs_q3,

                "median_longest_run":
                    statistics.median(
                        longest
                    ),

                "q1_longest_run":
                    longest_q1,

                "q3_longest_run":
                    longest_q3,
            }
        )

    SUMMARY_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "experiment_id",
        "r",
        "completed_replicates",
        "expected_replicates",
        "complete",
        "median_bias",
        "q1_bias",
        "q3_bias",
        "median_shannon_entropy",
        "q1_shannon_entropy",
        "q3_shannon_entropy",
        "median_ac1",
        "median_abs_ac1",
        "q1_abs_ac1",
        "q3_abs_ac1",
        "median_runs_z",
        "median_abs_runs_z",
        "q1_abs_runs_z",
        "q3_abs_runs_z",
        "median_longest_run",
        "q1_longest_run",
        "q3_longest_run",
    ]

    with SUMMARY_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            extrasaction="ignore",
            lineterminator="\n",
        )

        writer.writeheader()
        writer.writerows(summary)

    complete_groups = [
        row
        for row in summary
        if row["complete"] is True
    ]

    candidates = []

    if complete_groups:
        criteria = [
            (
                "lowest_median_bias",
                "median_bias",
                min,
            ),
            (
                "highest_median_shannon",
                "median_shannon_entropy",
                max,
            ),
            (
                "lowest_median_abs_ac1",
                "median_abs_ac1",
                min,
            ),
            (
                "lowest_median_abs_runs_z",
                "median_abs_runs_z",
                min,
            ),
            (
                "highest_median_bias",
                "median_bias",
                max,
            ),
            (
                "highest_median_abs_ac1",
                "median_abs_ac1",
                max,
            ),
            (
                "highest_median_abs_runs_z",
                "median_abs_runs_z",
                max,
            ),
        ]

        for criterion, field, chooser in criteria:
            selected_value = chooser(
                row[field]
                for row in complete_groups
            )

            tied = [
                row
                for row in complete_groups
                if (
                    row[field]
                    == selected_value
                )
            ]

            selected = min(
                tied,
                key=lambda row: row["r"],
            )

            candidates.append(
                {
                    "criterion":
                        criterion,

                    "experiment_id":
                        selected[
                            "experiment_id"
                        ],

                    "r":
                        selected["r"],

                    "metric":
                        field,

                    "value":
                        selected[field],
                }
            )

    with CANDIDATES_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        fields = [
            "criterion",
            "experiment_id",
            "r",
            "metric",
            "value",
        ]

        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
            lineterminator="\n",
        )

        writer.writeheader()
        writer.writerows(candidates)

    print(
        "Logistic screening analysis"
    )

    print(
        "---------------------------"
    )

    print(
        f"Expected runs       : "
        f"{len(manifest_rows)}"
    )

    print(
        f"Available runs      : "
        f"{len(manifest_rows) - len(missing)}"
    )

    print(
        f"Missing runs        : "
        f"{len(missing)}"
    )

    print(
        f"Parameter values    : "
        f"{len(summary)}"
    )

    print(
        f"Complete r groups   : "
        f"{len(complete_groups)} / 100"
    )

    print(
        f"Summary             : "
        f"{SUMMARY_PATH.relative_to(ROOT)}"
    )

    print(
        f"Candidate shortlist : "
        f"{CANDIDATES_PATH.relative_to(ROOT)}"
    )

    if not complete_groups:
        print()
        print(
            "No r value has all 20 replicates yet."
        )

        print(
            "Candidate selection will activate "
            "after complete groups are available."
        )

    else:
        print()
        print("Candidate criteria:")

        for row in candidates:
            print(
                f"  {row['criterion']:28s} "
                f"r={row['r']:.8f} "
                f"value={row['value']:.8f}"
            )


if __name__ == "__main__":
    main()
