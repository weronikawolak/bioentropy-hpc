# HPC Execution Checklist

## Before submission

1. Clone or update the frozen repository revision.
2. Confirm a clean Git working tree.
3. Run:

   `bash scripts/hpc/hpc_preflight.sh --require-slurm --strict-clean`

4. Record the preflight report.
5. Identify the correct:
   - Slurm partition;
   - account/project;
   - wall-time limit;
   - memory limit;
   - maximum practical task count.

## Tiny cluster smoke

Before the full campaign, submit only:

- `p = 1`;
- `p = 2`;
- small workload;
- one repetition.

Verify:

- all ranks produce `rank_XXXX.json`;
- no duplicated workload indices;
- `job.json` is created;
- all return codes are zero;
- Git commit matches the frozen revision.

## Final scaling campaign

Run two profiles:

- `ctr-drbg`;
- `logistic-mpfr`.

For each profile:

### Strong scaling

- fixed total workload;
- task counts include `p = 1`;
- three repetitions per point.

### Weak scaling

- fixed workload items per task;
- total workload grows linearly with task count;
- three repetitions per point.

## Before scientific interpretation

Verify every expected result directory exists.

Verify every job has:

- `job.json`;
- complete rank JSON files;
- successful Slurm exit status;
- expected task count;
- expected workload count.

Do not combine incomplete points with completed repetitions.

## Analysis

Run:

`analysis/scripts/analyze_hpc_scaling.py`

Primary reported statistics:

- median wall time;
- min/max wall time;
- aggregate throughput;
- strong speedup;
- strong parallel efficiency;
- weak scaling efficiency.

## Interpretation boundary

HPC scalability results measure computational performance only.

They are not randomness, entropy, or cryptographic-security metrics.
