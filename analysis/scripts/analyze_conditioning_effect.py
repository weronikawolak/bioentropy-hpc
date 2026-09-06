#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

MANIFEST = (
    ROOT
    / "configs/generated/conditioning"
    / "manifest.tsv"
)

RESULTS = ROOT / "results/metrics"

PAIR_OUTPUT = (
    ROOT
    / "results/aggregated"
    / "conditioning_effect_pairs.tsv"
)

GROUP_OUTPUT = (
    ROOT
    / "results/aggregated"
    / "conditioning_effect_by_group.tsv"
)


def result_path(
    experiment_id,
    replicate_id,
    mode,
):
    suffix = (
        "_ascon-xof128"
        if mode == "ascon_xof128"
        else ""
    )

    return (
        RESULTS
        / (
            f"{experiment_id}_"
            f"rep{replicate_id:04d}"
            f"{suffix}.json"
        )
    )


def group_name(
    source_family,
    experiment_id,
):
    if source_family == "dna_sequence":
        return re.sub(
            r"-w\d+$",
            "",
            experiment_id,
        )

    return experiment_id


def median(values):
    return statistics.median(values)


def main():
    with MANIFEST.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        manifest = list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )

    identities = {}

    for row in manifest:
        key = (
            row["experiment_id"].strip(),
            int(row["replicate_id"]),
        )

        identities[key] = (
            row["source_family"].strip()
        )

    pair_rows = []

    for (
        experiment_id,
        replicate_id,
    ), source_family in sorted(
        identities.items()
    ):
        raw_path = result_path(
            experiment_id,
            replicate_id,
            "raw",
        )

        ascon_path = result_path(
            experiment_id,
            replicate_id,
            "ascon_xof128",
        )

        if (
            not raw_path.exists()
            or not ascon_path.exists()
        ):
            continue

        raw = json.loads(
            raw_path.read_text()
        )

        ascon = json.loads(
            ascon_path.read_text()
        )

        raw_sha = (
            raw["reproducibility"]
            ["bitstream_sha256"]
        )

        input_sha = (
            ascon["conditioning"]
            ["input_sha256"]
        )

        if raw_sha != input_sha:
            raise RuntimeError(
                "RAW/Ascon input mismatch: "
                f"{experiment_id} "
                f"rep={replicate_id}"
            )

        rs = raw["statistics"]
        cs = ascon["statistics"]

        raw_bias = float(
            rs["bias"]
        )

        ascon_bias = float(
            cs["bias"]
        )

        raw_h = float(
            rs["shannon_entropy"]
        )

        ascon_h = float(
            cs["shannon_entropy"]
        )

        raw_ac1 = abs(
            float(
                rs[
                    "autocorrelation_lag1"
                ]
            )
        )

        ascon_ac1 = abs(
            float(
                cs[
                    "autocorrelation_lag1"
                ]
            )
        )

        raw_runs = abs(
            float(
                rs["runs_z_score"]
            )
        )

        ascon_runs = abs(
            float(
                cs["runs_z_score"]
            )
        )

        raw_longest = int(
            rs["longest_run"]
        )

        ascon_longest = int(
            cs["longest_run"]
        )

        pair_rows.append(
            {
                "source_family":
                    source_family,

                "group":
                    group_name(
                        source_family,
                        experiment_id,
                    ),

                "experiment_id":
                    experiment_id,

                "replicate_id":
                    replicate_id,

                "raw_bias":
                    raw_bias,

                "ascon_bias":
                    ascon_bias,

                "delta_bias":
                    ascon_bias
                    - raw_bias,

                "raw_shannon_entropy":
                    raw_h,

                "ascon_shannon_entropy":
                    ascon_h,

                "delta_shannon_entropy":
                    ascon_h
                    - raw_h,

                "raw_abs_ac1":
                    raw_ac1,

                "ascon_abs_ac1":
                    ascon_ac1,

                "delta_abs_ac1":
                    ascon_ac1
                    - raw_ac1,

                "raw_abs_runs_z":
                    raw_runs,

                "ascon_abs_runs_z":
                    ascon_runs,

                "delta_abs_runs_z":
                    ascon_runs
                    - raw_runs,

                "raw_longest_run":
                    raw_longest,

                "ascon_longest_run":
                    ascon_longest,

                "delta_longest_run":
                    ascon_longest
                    - raw_longest,
            }
        )

    PAIR_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    pair_fields = [
        "source_family",
        "group",
        "experiment_id",
        "replicate_id",
        "raw_bias",
        "ascon_bias",
        "delta_bias",
        "raw_shannon_entropy",
        "ascon_shannon_entropy",
        "delta_shannon_entropy",
        "raw_abs_ac1",
        "ascon_abs_ac1",
        "delta_abs_ac1",
        "raw_abs_runs_z",
        "ascon_abs_runs_z",
        "delta_abs_runs_z",
        "raw_longest_run",
        "ascon_longest_run",
        "delta_longest_run",
    ]

    with PAIR_OUTPUT.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=pair_fields,
            delimiter="\t",
            lineterminator="\n",
        )

        writer.writeheader()
        writer.writerows(pair_rows)

    grouped = defaultdict(list)

    for row in pair_rows:
        grouped[
            (
                row["source_family"],
                row["group"],
            )
        ].append(row)

    group_rows = []

    for (
        source_family,
        group,
    ), rows in sorted(grouped.items()):

        group_rows.append(
            {
                "source_family":
                    source_family,

                "group":
                    group,

                "n_pairs":
                    len(rows),

                "median_raw_bias":
                    median([
                        r["raw_bias"]
                        for r in rows
                    ]),

                "median_ascon_bias":
                    median([
                        r["ascon_bias"]
                        for r in rows
                    ]),

                "median_delta_bias":
                    median([
                        r["delta_bias"]
                        for r in rows
                    ]),

                "median_raw_shannon":
                    median([
                        r[
                            "raw_shannon_entropy"
                        ]
                        for r in rows
                    ]),

                "median_ascon_shannon":
                    median([
                        r[
                            "ascon_shannon_entropy"
                        ]
                        for r in rows
                    ]),

                "median_delta_shannon":
                    median([
                        r[
                            "delta_shannon_entropy"
                        ]
                        for r in rows
                    ]),

                "median_raw_abs_ac1":
                    median([
                        r["raw_abs_ac1"]
                        for r in rows
                    ]),

                "median_ascon_abs_ac1":
                    median([
                        r["ascon_abs_ac1"]
                        for r in rows
                    ]),

                "median_delta_abs_ac1":
                    median([
                        r["delta_abs_ac1"]
                        for r in rows
                    ]),

                "median_raw_abs_runs_z":
                    median([
                        r["raw_abs_runs_z"]
                        for r in rows
                    ]),

                "median_ascon_abs_runs_z":
                    median([
                        r["ascon_abs_runs_z"]
                        for r in rows
                    ]),

                "median_delta_abs_runs_z":
                    median([
                        r[
                            "delta_abs_runs_z"
                        ]
                        for r in rows
                    ]),
            }
        )

    group_fields = [
        "source_family",
        "group",
        "n_pairs",
        "median_raw_bias",
        "median_ascon_bias",
        "median_delta_bias",
        "median_raw_shannon",
        "median_ascon_shannon",
        "median_delta_shannon",
        "median_raw_abs_ac1",
        "median_ascon_abs_ac1",
        "median_delta_abs_ac1",
        "median_raw_abs_runs_z",
        "median_ascon_abs_runs_z",
        "median_delta_abs_runs_z",
    ]

    with GROUP_OUTPUT.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=group_fields,
            delimiter="\t",
            lineterminator="\n",
        )

        writer.writeheader()
        writer.writerows(group_rows)

    print(
        "Conditioning effect analysis"
    )
    print(
        "----------------------------"
    )

    print(
        f"Completed pairs : "
        f"{len(pair_rows)}"
    )

    print(
        f"Groups          : "
        f"{len(group_rows)}"
    )

    print()
    print(
        "Delta interpretation:"
    )
    print(
        "  bias, |AC1|, |runs z|: "
        "negative = improvement"
    )
    print(
        "  Shannon entropy: "
        "positive = improvement"
    )

    print()
    print(
        f"Pairs : "
        f"{PAIR_OUTPUT.relative_to(ROOT)}"
    )

    print(
        f"Groups: "
        f"{GROUP_OUTPUT.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
