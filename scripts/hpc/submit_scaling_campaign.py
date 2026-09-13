#!/usr/bin/env python3

from pathlib import Path
import argparse
import csv
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

SLURM_SCRIPT = (
    ROOT
    / "scripts/hpc"
    / "slurm_scaling_job.sh"
)

PLAN_ROOT = (
    ROOT
    / "results/hpc"
    / "submission_plans"
)


def parse_tasks(value):
    result = []

    for item in value.split(","):
        item = item.strip()

        if not item:
            continue

        p = int(item)

        if p < 1:
            raise ValueError(
                "task counts must be positive"
            )

        result.append(p)

    result = sorted(set(result))

    if not result:
        raise ValueError(
            "empty task list"
        )

    if 1 not in result:
        raise ValueError(
            "task list must include p=1 baseline"
        )

    return result


def run_prepare(
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
        help="comma-separated, e.g. 1,2,4,8,16",
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

    parser.add_argument(
        "--time",
        dest="time_limit",
    )

    parser.add_argument(
        "--mem-per-cpu",
    )

    parser.add_argument(
        "--submit",
        action="store_true",
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
            % p != 0
        ):
            raise ValueError(
                "strong-items must be divisible "
                f"by every task count; failed at p={p}"
            )

    max_p = max(tasks)

    weak_max_items = (
        max_p
        * args.weak_items_per_task
    )

    #
    # Freeze manifests/configs.
    #
    run_prepare(
        args.profile,
        "strong",
        args.strong_items,
        args.output_bits,
    )

    run_prepare(
        args.profile,
        "weak",
        weak_max_items,
        args.output_bits,
    )

    strong_manifest = (
        f"results/hpc/manifests/"
        f"{args.profile}_strong.tsv"
    )

    weak_manifest = (
        f"results/hpc/manifests/"
        f"{args.profile}_weak.tsv"
    )

    jobs = []

    for mode in (
        "strong",
        "weak",
    ):
        for p in tasks:
            if mode == "strong":
                limit = (
                    args.strong_items
                )
                manifest = (
                    strong_manifest
                )
            else:
                limit = (
                    p
                    * args.weak_items_per_task
                )
                manifest = (
                    weak_manifest
                )

            for repetition in range(
                1,
                args.repetitions + 1,
            ):
                result_dir = (
                    "results/hpc/runs/"
                    f"{args.campaign_id}/"
                    f"{args.profile}/"
                    f"{mode}/"
                    f"p{p:04d}/"
                    f"rep{repetition:02d}"
                )

                export_values = [
                    "ALL",
                    (
                        "BIOENTROPY_MANIFEST="
                        + manifest
                    ),
                    (
                        "BIOENTROPY_LIMIT="
                        + str(limit)
                    ),
                    (
                        "BIOENTROPY_PROFILE="
                        + args.profile
                    ),
                    (
                        "BIOENTROPY_MODE="
                        + mode
                    ),
                    (
                        "BIOENTROPY_REPETITION="
                        + str(repetition)
                    ),
                    (
                        "BIOENTROPY_RESULT_DIR="
                        + result_dir
                    ),
                ]

                command = [
                    "sbatch",
                    "--parsable",
                    "--ntasks",
                    str(p),
                    "--cpus-per-task",
                    "1",
                    "--export",
                    ",".join(
                        export_values
                    ),
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

                if args.time_limit:
                    command += [
                        "--time",
                        args.time_limit,
                    ]

                if args.mem_per_cpu:
                    command += [
                        "--mem-per-cpu",
                        args.mem_per_cpu,
                    ]

                command.append(
                    str(
                        SLURM_SCRIPT.relative_to(
                            ROOT
                        )
                    )
                )

                jobs.append(
                    {
                        "campaign_id":
                            args.campaign_id,
                        "profile":
                            args.profile,
                        "mode":
                            mode,
                        "world_size":
                            p,
                        "repetition":
                            repetition,
                        "limit":
                            limit,
                        "manifest":
                            manifest,
                        "result_dir":
                            result_dir,
                        "command":
                            shlex.join(command),
                        "job_id":
                            "",
                    }
                )

    PLAN_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    plan_tsv = (
        PLAN_ROOT
        / (
            args.campaign_id
            + "_"
            + args.profile
            + ".tsv"
        )
    )

    plan_json = plan_tsv.with_suffix(
        ".json"
    )

    print()
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
    print(
        "Jobs    :",
        len(jobs),
    )
    print()

    if args.submit:
        if not shutil_which(
            "sbatch"
        ):
            raise RuntimeError(
                "--submit requested but "
                "sbatch is unavailable"
            )

        for index, job in enumerate(
            jobs,
            start=1,
        ):
            command = shlex.split(
                job["command"]
            )

            print(
                f"[{index:02d}/"
                f"{len(jobs):02d}] "
                f"SUBMIT "
                f"{job['mode']} "
                f"p={job['world_size']} "
                f"rep={job['repetition']}"
            )

            result = subprocess.run(
                command,
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            job["job_id"] = (
                result.stdout.strip()
            )
    else:
        print(
            "DRY RUN ONLY — no jobs submitted."
        )
        print()

        for job in jobs:
            print(
                job["command"]
            )

    columns = list(
        jobs[0].keys()
    )

    with plan_tsv.open(
        "w",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=columns,
            delimiter="\t",
            lineterminator="\n",
        )

        writer.writeheader()
        writer.writerows(jobs)

    plan_json.write_text(
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
                "submitted":
                    args.submit,
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
    print("Plan TSV :", plan_tsv)
    print("Plan JSON:", plan_json)


def shutil_which(command):
    from shutil import which
    return which(command)


if __name__ == "__main__":
    main()
