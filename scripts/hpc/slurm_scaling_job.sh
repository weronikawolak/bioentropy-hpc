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

cd "${ROOT}"

source .venv/bin/activate

mkdir -p \
  "${BIOENTROPY_RESULT_DIR}"

START_NS="$(
  date +%s%N
)"

srun \
  python \
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
  date +%s%N
)"

export START_NS
export END_NS

python - <<'PY'
from pathlib import Path
import csv
import json
import os
import platform
import subprocess

root = Path.cwd()

manifest = Path(
    os.environ[
        "BIOENTROPY_MANIFEST"
    ]
)

if not manifest.is_absolute():
    manifest = root / manifest

limit = int(
    os.environ[
        "BIOENTROPY_LIMIT"
    ]
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
    os.environ[
        "BIOENTROPY_RESULT_DIR"
    ]
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
        1,
    "environment":
        "slurm",
    "profile":
        os.environ[
            "BIOENTROPY_PROFILE"
        ],
    "mode":
        os.environ[
            "BIOENTROPY_MODE"
        ],
    "world_size":
        int(
            os.environ[
                "SLURM_NTASKS"
            ]
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
    "started_ns":
        start_ns,
    "finished_ns":
        end_ns,
    "wall_seconds":
        (
            end_ns
            - start_ns
        )
        / 1e9,
    "slurm_job_id":
        os.environ.get(
            "SLURM_JOB_ID"
        ),
    "slurm_job_nodelist":
        os.environ.get(
            "SLURM_JOB_NODELIST"
        ),
    "slurm_cpus_per_task":
        os.environ.get(
            "SLURM_CPUS_PER_TASK"
        ),
    "hostname":
        platform.node(),
    "git_commit":
        git_commit,
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
