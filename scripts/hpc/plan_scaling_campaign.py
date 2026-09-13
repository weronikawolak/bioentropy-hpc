#!/usr/bin/env python3

from pathlib import Path
import argparse
import json
import shlex
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]

PREPARE = (
    ROOT
    / "scripts/hpc"
    / "prepare_scaling_workloads.py"
)

PLAN_ROOT = (
    ROOT
    / "results/hpc"
    / "submission_plans"
)


def parse_tasks(value):
    tasks = sorted({
        int(x.strip())
        for x in value.split(",")
        if x.strip()
    })

    if not tasks:
        raise ValueError(
            "empty task list"
        )

    if tasks[0] != 1:
        raise ValueError(
            "p=1 baseline is required"
        )

    if any(p < 1 for p in tasks):
        raise ValueError(
            "task counts must be positive"
        )

    return tasks


def prepare_manifest(
    profile,
    mode,
    items,
    output_bits,
):
    command = [
        sys.executable,
        str(PREPARE),
        "--profile",
        profile,
        "--mode",
        mode,
        "--items",
        str(items),
        "--output-bits",
        str(output_bits),
    ]

    subprocess.run(
        command,
        cwd=ROOT,
        check=True,
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--campaign-id",
        required=True,
    )

    parser.add_argument(
        "--profile",
        choices=[
            "ctr-drbg",
            "logistic-mpfr",
        ],
        required=True,
    )

    parser.add_argument(
        "--tasks",
        required=True,
    )

    parser.add_argument(
        "--repetitions",
        type=int,
        default=3,
    )

    parser.add_argument(
        "--strong-items",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--weak-items-per-task",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--output-bits",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--partition",
    )

    parser.add_argument(
        "--account",
    )

    args = parser.parse_args()

    tasks = parse_tasks(
        args.tasks
    )

    if args.repetitions < 1:
        raise ValueError(
            "repetitions must be positive"
        )

    if args.strong_items < 1:
        raise ValueError(
            "strong-items must be positive"
        )

    if args.weak_items_per_task < 1:
        raise ValueError(
            "weak-items-per-task must be positive"
        )

    if (
        args.output_bits < 8
        or args.output_bits % 8 != 0
    ):
        raise ValueError(
            "output-bits must be positive "
            "and divisible by 8"
        )

    for p in tasks:
        if (
            args.strong_items
            % p
            != 0
        ):
            raise ValueError(
                "strong-items must divide "
                f"evenly at p={p}"
            )

    max_tasks = max(tasks)

    weak_max_items = (
        max_tasks
        * args.weak_items_per_task
    )

    #
    # Generate the exact frozen manifests
    # referenced by the Slurm commands.
    #
    prepare_manifest(
        args.profile,
        "strong",
        args.strong_items,
        args.output_bits,
    )

    prepare_manifest(
        args.profile,
        "weak",
        weak_max_items,
        args.output_bits,
    )

    jobs = []

    for mode in (
        "ensemble-strong",
        "ensemble-weak",
    ):
        for p in tasks:

            if (
                mode
                == "ensemble-strong"
            ):
                limit = (
                    args.strong_items
                )

                manifest = (
                    "results/hpc/manifests/"
                    f"{args.profile}_strong.tsv"
                )

            else:
                limit = (
                    p
                    * args.weak_items_per_task
                )

                manifest = (
                    "results/hpc/manifests/"
                    f"{args.profile}_weak.tsv"
                )

            for rep in range(
                1,
                args.repetitions + 1,
            ):
                result_dir = (
                    "results/hpc/runs/"
                    f"{args.campaign_id}/"
                    f"{args.profile}/"
                    f"{mode}/"
                    f"p{p:04d}/"
                    f"rep{rep:02d}"
                )

                exports = (
                    "ALL,"
                    f"BIOENTROPY_MANIFEST={manifest},"
                    f"BIOENTROPY_LIMIT={limit},"
                    f"BIOENTROPY_PROFILE={args.profile},"
                    f"BIOENTROPY_MODE={mode},"
                    f"BIOENTROPY_REPETITION={rep},"
                    f"BIOENTROPY_RESULT_DIR={result_dir}"
                )

                command = [
                    "sbatch",
                    "--ntasks",
                    str(p),
                    "--cpus-per-task",
                    "1",
                    "--export",
                    exports,
                ]

                if args.partition:
                    command += [
                        "--partition",
                        args.partition,
                    ]

                if args.account:
                    command += [
                        "--account",
                        args.account,
                    ]

                command.append(
                    "scripts/hpc/"
                    "slurm_scaling_job.sh"
                )

                jobs.append(
                    {
                        "mode":
                            mode,
                        "world_size":
                            p,
                        "repetition":
                            rep,
                        "limit":
                            limit,
                        "manifest":
                            manifest,
                        "result_dir":
                            result_dir,
                        "command":
                            shlex.join(
                                command
                            ),
                    }
                )

    PLAN_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = (
        PLAN_ROOT
        / (
            f"{args.campaign_id}_"
            f"{args.profile}.json"
        )
    )

    output.write_text(
        json.dumps(
            {
                "campaign_id":
                    args.campaign_id,
                "profile":
                    args.profile,
                "tasks":
                    tasks,
                "repetitions":
                    args.repetitions,
                "strong_items":
                    args.strong_items,
                "weak_items_per_task":
                    args.weak_items_per_task,
                "output_bits":
                    args.output_bits,
                "jobs":
                    jobs,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print(
        "Frozen execution plan"
    )
    print(
        "====================="
    )
    print(
        "Campaign:",
        args.campaign_id,
    )
    print(
        "Profile :",
        args.profile,
    )
    print(
        "Tasks   :",
        tasks,
    )
    print()

    for job in jobs:
        print(
            job["command"]
        )

    print()
    print(
        f"Planned jobs: "
        f"{len(jobs)}"
    )
    print(
        "DRY RUN ONLY — nothing submitted."
    )
    print(
        "Saved plan:",
        output.relative_to(ROOT),
    )


if __name__ == "__main__":
    main()
