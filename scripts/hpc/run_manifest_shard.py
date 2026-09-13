#!/usr/bin/env python3

from pathlib import Path
import argparse
import csv
import hashlib
import json
import os
import subprocess
import time


ROOT = Path(__file__).resolve().parents[2]

RUNNER = (
    ROOT
    / "build"
    / "bioentropy-runner"
)


def sha256(path):
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--manifest",
        required=True,
    )

    parser.add_argument(
        "--rank",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--world-size",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--result-dir",
        required=True,
    )

    args = parser.parse_args()

    rank = args.rank

    if rank is None:
        value = os.environ.get(
            "SLURM_PROCID"
        )

        if value is None:
            raise RuntimeError(
                "No --rank and "
                "SLURM_PROCID is absent"
            )

        rank = int(value)

    if not (
        0 <= rank < args.world_size
    ):
        raise ValueError(
            "rank outside world"
        )

    if not RUNNER.is_file():
        raise FileNotFoundError(
            RUNNER
        )

    manifest = Path(
        args.manifest
    )

    if not manifest.is_absolute():
        manifest = ROOT / manifest

    with manifest.open(
        encoding="utf-8",
    ) as handle:
        rows = list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )

    if args.limit is not None:
        rows = rows[
            :args.limit
        ]

    assigned = [
        row
        for index, row
        in enumerate(rows)
        if index % args.world_size
        == rank
    ]

    result_dir = Path(
        args.result_dir
    )

    if not result_dir.is_absolute():
        result_dir = (
            ROOT
            / result_dir
        )

    result_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    started_monotonic_ns = time.perf_counter_ns()

    completed = []

    for row in assigned:
        config = (
            ROOT
            / row["config"]
        )

        expected_sha = row[
            "config_sha256"
        ]

        actual_sha = sha256(
            config
        )

        if (
            actual_sha
            != expected_sha
        ):
            raise RuntimeError(
                f"SHA mismatch: {config}"
            )

        t0 = time.perf_counter()

        process = subprocess.run(
            [
                str(RUNNER),
                "--config",
                str(config),
            ],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

        elapsed = (
            time.perf_counter()
            - t0
        )

        if process.returncode != 0:
            raise RuntimeError(
                f"runner failed for "
                f"{config}:\n"
                f"{process.stderr}"
            )

        completed.append(
            {
                "workload_index":
                    int(
                        row[
                            "workload_index"
                        ]
                    ),
                "config":
                    row["config"],
                "seconds":
                    elapsed,
                "output_bits":
                    int(
                        row[
                            "output_bits"
                        ]
                    ),
            }
        )

    finished_monotonic_ns = time.perf_counter_ns()

    summary = {
        "rank":
            rank,
        "world_size":
            args.world_size,
        "manifest":
            str(
                manifest.relative_to(
                    ROOT
                )
            ),
        "assigned_count":
            len(assigned),
        "completed_count":
            len(completed),
        "started_monotonic_ns":
            started_monotonic_ns,
        "finished_monotonic_ns":
            finished_monotonic_ns,
        "rank_wall_seconds":
            (
                finished_monotonic_ns
                - started_monotonic_ns
            )
            / 1e9,
        "total_output_bits":
            sum(
                item["output_bits"]
                for item in completed
            ),
        "workloads":
            completed,
    }

    output = (
        result_dir
        / f"rank_{rank:04d}.json"
    )

    output.write_text(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        f"rank={rank} "
        f"completed={len(completed)} "
        f"seconds="
        f"{summary['rank_wall_seconds']:.6f}"
    )


if __name__ == "__main__":
    main()
