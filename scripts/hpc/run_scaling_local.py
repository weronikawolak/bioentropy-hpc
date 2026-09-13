#!/usr/bin/env python3

from pathlib import Path
import argparse
import csv
import datetime
import json
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[2]

SHARD_RUNNER = (
    ROOT
    / "scripts/hpc"
    / "run_manifest_shard.py"
)


def utc_now():
    return datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--manifest",
        required=True,
    )

    parser.add_argument(
        "--world-size",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--limit",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--profile",
        required=True,
    )

    parser.add_argument(
        "--mode",
        choices=[
            "ensemble-strong",
            "ensemble-weak",
        ],
        required=True,
    )

    parser.add_argument(
        "--repetition",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--result-dir",
        required=True,
    )

    args = parser.parse_args()

    if args.world_size < 1:
        raise ValueError(
            "world-size must be positive"
        )

    if args.limit < 1:
        raise ValueError(
            "limit must be positive"
        )

    manifest = Path(
        args.manifest
    )

    if not manifest.is_absolute():
        manifest = ROOT / manifest

    result_dir = Path(
        args.result_dir
    )

    if not result_dir.is_absolute():
        result_dir = (
            ROOT / result_dir
        )

    result_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    with manifest.open(
        encoding="utf-8",
    ) as handle:
        rows = list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )

    rows = rows[:args.limit]

    if len(rows) != args.limit:
        raise RuntimeError(
            "manifest shorter than requested limit"
        )

    total_output_bits = sum(
        int(row["output_bits"])
        for row in rows
    )

    processes = []

    started_utc = utc_now()

    started_ns = (
        time.perf_counter_ns()
    )

    for rank in range(
        args.world_size
    ):
        log_path = (
            result_dir
            / f"rank_{rank:04d}.log"
        )

        handle = log_path.open(
            "w",
            encoding="utf-8",
        )

        command = [
            sys.executable,
            str(SHARD_RUNNER),
            "--manifest",
            str(manifest),
            "--rank",
            str(rank),
            "--world-size",
            str(args.world_size),
            "--limit",
            str(args.limit),
            "--result-dir",
            str(result_dir),
        ]

        process = subprocess.Popen(
            command,
            cwd=ROOT,
            stdout=handle,
            stderr=subprocess.STDOUT,
            text=True,
        )

        processes.append(
            (
                process,
                handle,
                rank,
            )
        )

    failures = []

    for (
        process,
        handle,
        rank,
    ) in processes:

        returncode = (
            process.wait()
        )

        handle.close()

        if returncode != 0:
            failures.append(
                (
                    rank,
                    returncode,
                )
            )

    finished_ns = (
        time.perf_counter_ns()
    )

    finished_utc = utc_now()

    if failures:
        raise RuntimeError(
            f"worker failures: "
            f"{failures}"
        )

    job = {
        "schema_version":
            2,

        "environment":
            "local",

        "scaling_scope":
            "independent-workload-ensemble",

        "profile":
            args.profile,

        "mode":
            args.mode,

        "world_size":
            args.world_size,

        "limit":
            args.limit,

        "repetition":
            args.repetition,

        "manifest":
            str(
                manifest.relative_to(
                    ROOT
                )
            ),

        "total_output_bits":
            total_output_bits,

        "started_utc":
            started_utc,

        "finished_utc":
            finished_utc,

        "wall_seconds":
            (
                finished_ns
                - started_ns
            )
            / 1e9,
    }

    output = (
        result_dir
        / "job.json"
    )

    output.write_text(
        json.dumps(
            job,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        f"{args.mode} "
        f"p={args.world_size} "
        f"rep={args.repetition} "
        f"items={args.limit} "
        f"seconds="
        f"{job['wall_seconds']:.6f}"
    )


if __name__ == "__main__":
    main()
