#!/usr/bin/env bash

#SBATCH --job-name=bioentropy-scale
#SBATCH --cpus-per-task=1
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err

set -euo pipefail

: "${BIOENTROPY_MANIFEST:?missing BIOENTROPY_MANIFEST}"
: "${BIOENTROPY_LIMIT:?missing BIOENTROPY_LIMIT}"
: "${BIOENTROPY_PROFILE:?missing BIOENTROPY_PROFILE}"
: "${BIOENTROPY_MODE:?missing BIOENTROPY_MODE}"
: "${BIOENTROPY_REPETITION:?missing BIOENTROPY_REPETITION}"
: "${BIOENTROPY_RESULT_DIR:?missing BIOENTROPY_RESULT_DIR}"

ROOT="${SLURM_SUBMIT_DIR}"

cd "$ROOT"

PYTHON_BIN="${BIOENTROPY_PYTHON:-python3}"

mkdir -p \
  "${BIOENTROPY_RESULT_DIR}"

START_UTC="$(
  date -u +"%Y-%m-%dT%H:%M:%SZ"
)"

START_NS="$(
  python3 - <<'PY'
import time
print(time.perf_counter_ns())
PY
)"

srun \
  "${PYTHON_BIN}" \
  scripts/hpc/run_manifest_shard.py \
  --manifest \
  "${BIOENTROPY_MANIFEST}" \
  --world-size \
  "${SLURM_NTASKS}" \
  --limit \
  "${BIOENTROPY_LIMIT}" \
  --result-dir \
  "${BIOENTROPY_RESULT_DIR}"

END_NS="$(
  python3 - <<'PY'
import time
print(time.perf_counter_ns())
PY
)"

END_UTC="$(
  date -u +"%Y-%m-%dT%H:%M:%SZ"
)"


export BIOENTROPY_RESULT_DIR
export BIOENTROPY_LIMIT

"${PYTHON_BIN}" - <<'PYVERIFY'
from pathlib import Path
import json
import os

result_dir = Path(
    os.environ[
        "BIOENTROPY_RESULT_DIR"
    ]
)

expected_ranks = int(
    os.environ[
        "SLURM_NTASKS"
    ]
)

expected_items = int(
    os.environ[
        "BIOENTROPY_LIMIT"
    ]
)

rank_files = sorted(
    result_dir.glob(
        "rank_*.json"
    )
)

if len(rank_files) != expected_ranks:
    raise RuntimeError(
        f"Expected {expected_ranks} "
        f"rank files, got "
        f"{len(rank_files)}"
    )

indices = []

for path in rank_files:
    data = json.loads(
        path.read_text()
    )

    if (
        data["world_size"]
        != expected_ranks
    ):
        raise RuntimeError(
            f"{path}: incorrect world size"
        )

    indices.extend(
        item["workload_index"]
        for item
        in data["workloads"]
    )

if len(indices) != expected_items:
    raise RuntimeError(
        "Completed workload count "
        "does not match expected limit"
    )

if len(indices) != len(
    set(indices)
):
    raise RuntimeError(
        "Duplicate workload execution "
        "detected"
    )

if sorted(indices) != list(
    range(expected_items)
):
    raise RuntimeError(
        "Incomplete workload coverage"
    )

print(
    "PASSED: Slurm rank outputs "
    "complete and non-overlapping"
)
PYVERIFY

export START_NS
export END_NS
export START_UTC
export END_UTC

python3 - <<'PY'
from pathlib import Path
import csv
import json
import os
import platform
import subprocess

root = Path.cwd()

manifest = Path(
    os.environ["BIOENTROPY_MANIFEST"]
)

if not manifest.is_absolute():
    manifest = root / manifest

limit = int(
    os.environ["BIOENTROPY_LIMIT"]
)

with manifest.open(
    encoding="utf-8",
) as handle:
    rows = list(
        csv.DictReader(
            handle,
            delimiter="\t",
        )
    )[:limit]

if len(rows) != limit:
    raise RuntimeError(
        "manifest shorter than limit"
    )

total_bits = sum(
    int(row["output_bits"])
    for row in rows
)

start_ns = int(
    os.environ["START_NS"]
)

end_ns = int(
    os.environ["END_NS"]
)

result_dir = Path(
    os.environ["BIOENTROPY_RESULT_DIR"]
)

if not result_dir.is_absolute():
    result_dir = root / result_dir

git_commit = subprocess.check_output(
    [
        "git",
        "rev-parse",
        "HEAD",
    ],
    cwd=root,
    text=True,
).strip()

job = {
    "schema_version":
        2,

    "environment":
        "slurm",

    "scaling_scope":
        "independent-workload-ensemble",

    "profile":
        os.environ["BIOENTROPY_PROFILE"],

    "mode":
        os.environ["BIOENTROPY_MODE"],

    "world_size":
        int(
            os.environ["SLURM_NTASKS"]
        ),

    "limit":
        limit,

    "repetition":
        int(
            os.environ[
                "BIOENTROPY_REPETITION"
            ]
        ),

    "manifest":
        str(
            manifest.relative_to(root)
        ),

    "total_output_bits":
        total_bits,

    "started_utc":
        os.environ["START_UTC"],

    "finished_utc":
        os.environ["END_UTC"],

    "wall_seconds":
        (
            end_ns
            - start_ns
        )
        / 1e9,

    "git_commit":
        git_commit,

    "hostname":
        platform.node(),

    "slurm_job_id":
        os.environ.get(
            "SLURM_JOB_ID"
        ),

    "slurm_job_nodelist":
        os.environ.get(
            "SLURM_JOB_NODELIST"
        ),
}

(result_dir / "job.json").write_text(
    json.dumps(
        job,
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)

print(
    "job wall seconds:",
    job["wall_seconds"],
)
PY
