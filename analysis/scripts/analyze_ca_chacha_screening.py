#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

MANIFEST = ROOT / "configs/generated/screening/manifest.tsv"
RESULTS = ROOT / "results/metrics"

OUTPUT = (
    ROOT
    / "results/aggregated"
    / "ca_chacha_screening.tsv"
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


def result_path(experiment_id, replicate_id):
    return (
        RESULTS
        / f"{experiment_id}_rep{replicate_id:04d}.json"
    )


def summarize(values):
    bias = [v["bias"] for v in values]
    shannon = [v["shannon"] for v in values]
    abs_ac1 = [abs(v["ac1"]) for v in values]
    abs_runs_z = [abs(v["runs_z"]) for v in values]
    longest = [v["longest_run"] for v in values]

    bias_q1, bias_q3 = quartiles(bias)
    shannon_q1, shannon_q3 = quartiles(shannon)
    ac1_q1, ac1_q3 = quartiles(abs_ac1)
    runs_q1, runs_q3 = quartiles(abs_runs_z)
    longest_q1, longest_q3 = quartiles(longest)

    return {
        "median_bias": statistics.median(bias),
        "q1_bias": bias_q1,
        "q3_bias": bias_q3,

        "median_shannon_entropy":
            statistics.median(shannon),
        "q1_shannon_entropy": shannon_q1,
        "q3_shannon_entropy": shannon_q3,

        "median_abs_ac1":
            statistics.median(abs_ac1),
        "q1_abs_ac1": ac1_q1,
        "q3_abs_ac1": ac1_q3,

        "median_abs_runs_z":
            statistics.median(abs_runs_z),
        "q1_abs_runs_z": runs_q1,
        "q3_abs_runs_z": runs_q3,

        "median_longest_run":
            statistics.median(longest),
        "q1_longest_run": longest_q1,
        "q3_longest_run": longest_q3,
    }


def main():
    if not MANIFEST.exists():
        raise RuntimeError(
            f"Manifest not found: {MANIFEST}"
        )

    with MANIFEST.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        all_rows = list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )

    manifest_rows = [
        row
        for row in all_rows
        if row["source"] in {
            "cellular_automaton",
            "chacha20_reference",
        }
    ]

    expected = 100

    if len(manifest_rows) != expected:
        raise RuntimeError(
            "Expected 100 CA + ChaCha20 runs "
            f"in manifest, found {len(manifest_rows)}"
        )

    groups = defaultdict(list)
    group_metadata = {}

    missing = []
    invalid = []

    for row in manifest_rows:
        experiment_id = row["experiment_id"]
        replicate_id = int(row["replicate_id"])

        path = result_path(
            experiment_id,
            replicate_id,
        )

        if not path.exists():
            missing.append(
                (experiment_id, replicate_id)
            )
            continue

        try:
            with path.open(
                encoding="utf-8",
            ) as handle:
                data = json.load(handle)

            if (
                data["experiment"]["id"]
                != experiment_id
            ):
                raise ValueError(
                    "experiment_id mismatch"
                )

            if (
                int(
                    data["experiment"][
                        "replicate_id"
                    ]
                )
                != replicate_id
            ):
                raise ValueError(
                    "replicate_id mismatch"
                )

            stats = data["statistics"]

            ac1 = stats[
                "autocorrelation_lag1"
            ]

            runs_z = stats["runs_z_score"]

            if ac1 is None:
                raise ValueError(
                    "undefined autocorrelation"
                )

            if runs_z is None:
                raise ValueError(
                    "undefined runs z-score"
                )

            groups[experiment_id].append(
                {
                    "bias":
                        float(stats["bias"]),

                    "shannon":
                        float(
                            stats[
                                "shannon_entropy"
                            ]
                        ),

                    "ac1":
                        float(ac1),

                    "runs_z":
                        float(runs_z),

                    "longest_run":
                        int(
                            stats["longest_run"]
                        ),
                }
            )

            if row["source"] == "cellular_automaton":
                group_metadata[
                    experiment_id
                ] = {
                    "source":
                        "cellular_automaton",

                    "configuration":
                        (
                            f"Rule {row['rule']}, "
                            f"{row['cells']} cells"
                        ),

                    "rule":
                        row["rule"],

                    "cells":
                        row["cells"],
                }

            else:
                group_metadata[
                    experiment_id
                ] = {
                    "source":
                        "chacha20_reference",

                    "configuration":
                        "ChaCha20 reference PRG",

                    "rule":
                        "",

                    "cells":
                        "",
                }

        except Exception as exc:
            invalid.append(
                (
                    experiment_id,
                    replicate_id,
                    str(exc),
                )
            )

    expected_experiments = []

    for row in manifest_rows:
        experiment_id = row["experiment_id"]

        if experiment_id not in expected_experiments:
            expected_experiments.append(
                experiment_id
            )

        if (
            experiment_id
            not in group_metadata
        ):
            if row["source"] == "cellular_automaton":
                group_metadata[
                    experiment_id
                ] = {
                    "source":
                        "cellular_automaton",

                    "configuration":
                        (
                            f"Rule {row['rule']}, "
                            f"{row['cells']} cells"
                        ),

                    "rule":
                        row["rule"],

                    "cells":
                        row["cells"],
                }
            else:
                group_metadata[
                    experiment_id
                ] = {
                    "source":
                        "chacha20_reference",

                    "configuration":
                        "ChaCha20 reference PRG",

                    "rule":
                        "",

                    "cells":
                        "",
                }

    output_rows = []

    for experiment_id in expected_experiments:
        values = groups.get(
            experiment_id,
            [],
        )

        metadata = group_metadata[
            experiment_id
        ]

        row = {
            "experiment_id":
                experiment_id,

            "source":
                metadata["source"],

            "configuration":
                metadata["configuration"],

            "rule":
                metadata["rule"],

            "cells":
                metadata["cells"],

            "completed_replicates":
                len(values),

            "expected_replicates":
                EXPECTED_REPLICATES,

            "complete":
                (
                    len(values)
                    == EXPECTED_REPLICATES
                ),
        }

        if values:
            row.update(
                summarize(values)
            )

        output_rows.append(row)

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fields = [
        "experiment_id",
        "source",
        "configuration",
        "rule",
        "cells",
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

    with OUTPUT.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
            extrasaction="ignore",
            lineterminator="\n",
        )

        writer.writeheader()
        writer.writerows(output_rows)

    complete_runs = (
        len(manifest_rows)
        - len(missing)
        - len(invalid)
    )

    print(
        "CA + ChaCha20 screening analysis"
    )

    print(
        "--------------------------------"
    )

    print(
        f"Expected runs       : "
        f"{len(manifest_rows)}"
    )

    print(
        f"Available valid     : "
        f"{complete_runs}"
    )

    print(
        f"Missing             : "
        f"{len(missing)}"
    )

    print(
        f"Invalid             : "
        f"{len(invalid)}"
    )

    print(
        f"Groups              : "
        f"{len(output_rows)}"
    )

    print(
        "Complete groups     : "
        f"{sum(r['complete'] for r in output_rows)}"
        f" / {len(output_rows)}"
    )

    print(
        f"Output              : "
        f"{OUTPUT.relative_to(ROOT)}"
    )

    print()
    print("Current group status:")

    for row in output_rows:
        print(
            f"  {row['configuration']:<28} "
            f"{row['completed_replicates']:>2}/"
            f"{row['expected_replicates']}"
        )

        if row["completed_replicates"]:
            print(
                "    "
                f"bias={row['median_bias']:.6f}  "
                f"H={row['median_shannon_entropy']:.6f}  "
                f"|AC1|={row['median_abs_ac1']:.6f}  "
                f"|runs z|={row['median_abs_runs_z']:.3f}  "
                f"longest={row['median_longest_run']:.1f}"
            )

    if invalid:
        print()
        print("First invalid results:")

        for item in invalid[:5]:
            print(
                f"  {item[0]} "
                f"rep={item[1]}: "
                f"{item[2]}"
            )


if __name__ == "__main__":
    main()
