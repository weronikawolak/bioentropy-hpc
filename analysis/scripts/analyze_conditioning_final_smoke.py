#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

RESULTS = (
    ROOT
    / "results/metrics"
)

SOURCES = [
    "logistic",
    "rule30",
    "rule90",
    "dna",
    "chacha20",
]


def result_paths(
    source: str,
) -> tuple[Path, Path]:
    experiment_id = (
        f"conditioning-final-smoke-{source}"
    )

    raw = (
        RESULTS
        / f"{experiment_id}_rep0000.json"
    )

    xof = (
        RESULTS
        / (
            f"{experiment_id}_rep0000_"
            "ascon-xof128.json"
        )
    )

    return raw, xof


def metric(
    document: dict,
    name: str,
):
    return document["statistics"][name]


def main() -> None:
    rows = []

    failures = []

    for source in SOURCES:
        raw_path, xof_path = (
            result_paths(source)
        )

        if not raw_path.exists():
            failures.append(
                f"{source}: missing {raw_path}"
            )
            continue

        if not xof_path.exists():
            failures.append(
                f"{source}: missing {xof_path}"
            )
            continue

        raw = json.loads(
            raw_path.read_text()
        )

        xof = json.loads(
            xof_path.read_text()
        )

        raw_sha = (
            raw["reproducibility"]
            ["bitstream_sha256"]
        )

        xof_input_sha = (
            xof["conditioning"]
            ["input_sha256"]
        )

        xof_output_sha = (
            xof["reproducibility"]
            ["bitstream_sha256"]
        )

        same_input = (
            raw_sha
            == xof_input_sha
        )

        output_changed = (
            raw_sha
            != xof_output_sha
        )

        same_bits = (
            metric(
                raw,
                "total_bits",
            )
            ==
            metric(
                xof,
                "total_bits",
            )
        )

        if not same_input:
            failures.append(
                f"{source}: RAW/XOF input SHA mismatch"
            )

        if not output_changed:
            failures.append(
                f"{source}: XOF output equals raw input"
            )

        if not same_bits:
            failures.append(
                f"{source}: output length mismatch"
            )

        rows.append(
            {
                "source": source,

                "total_bits":
                    metric(
                        raw,
                        "total_bits",
                    ),

                "same_raw_input":
                    same_input,

                "xof_changed_stream":
                    output_changed,

                "raw_bias":
                    metric(
                        raw,
                        "bias",
                    ),

                "xof_bias":
                    metric(
                        xof,
                        "bias",
                    ),

                "raw_shannon":
                    metric(
                        raw,
                        "shannon_entropy",
                    ),

                "xof_shannon":
                    metric(
                        xof,
                        "shannon_entropy",
                    ),

                "raw_ac1":
                    metric(
                        raw,
                        "autocorrelation_lag1",
                    ),

                "xof_ac1":
                    metric(
                        xof,
                        "autocorrelation_lag1",
                    ),

                "raw_runs_z":
                    metric(
                        raw,
                        "runs_z_score",
                    ),

                "xof_runs_z":
                    metric(
                        xof,
                        "runs_z_score",
                    ),

                "raw_longest_run":
                    metric(
                        raw,
                        "longest_run",
                    ),

                "xof_longest_run":
                    metric(
                        xof,
                        "longest_run",
                    ),
            }
        )

    if failures:
        print()
        print("FAILED")
        print("======")

        for failure in failures:
            print(failure)

        raise SystemExit(1)

    frame = pd.DataFrame(rows)

    frame[
        "abs_bias_improvement"
    ] = (
        frame["raw_bias"].abs()
        - frame["xof_bias"].abs()
    )

    frame[
        "abs_ac1_improvement"
    ] = (
        frame["raw_ac1"].abs()
        - frame["xof_ac1"].abs()
    )

    frame[
        "abs_runs_z_improvement"
    ] = (
        frame["raw_runs_z"].abs()
        - frame["xof_runs_z"].abs()
    )

    output = (
        ROOT
        / "results/aggregated/"
          "conditioning_final_smoke_summary.tsv"
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame.to_csv(
        output,
        sep="\t",
        index=False,
    )

    print()
    print(
        "Paired RAW vs Ascon-XOF128 smoke"
    )
    print("=" * 130)

    print(
        frame[
            [
                "source",
                "total_bits",
                "same_raw_input",
                "raw_bias",
                "xof_bias",
                "raw_shannon",
                "xof_shannon",
                "raw_ac1",
                "xof_ac1",
                "raw_runs_z",
                "xof_runs_z",
                "raw_longest_run",
                "xof_longest_run",
            ]
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:.8f}",
        )
    )

    print()
    print(
        "PASSED: all five RAW/XOF pairs "
        "used identical raw source streams."
    )

    print()
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
